"""
The ia_flow events the IA tasks emit (see perma/ia_metrics.py), checked through
the metrics logger's messages.
"""
from contextlib import nullcontext
from datetime import timedelta
from io import BytesIO
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import fakeredis
import pytest
import requests
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone

from perma.celery_tasks import (
    IA_STATE_CACHE_KEY,
    IA_UPLOAD_QUEUING_LOCK,
    conditionally_queue_internet_archive_uploads_for_date_range,
    confirm_file_deleted_from_daily_item,
    confirm_files_uploaded_to_internet_archive_item,
    delete_link_from_daily_item,
    queue_internet_archive_deletions,
    upload_link_to_internet_archive,
)
from perma.models import InternetArchiveFile, InternetArchiveItem, Link
from perma.tests.test_internet_archive_tasks import (
    _daily_item,
    _fake_session,
    _file_with_status,
    _http_error,
    _ia_file_entry,
    _ia_item,
    _overloaded_session,
    _s3_details,
    _stale,
    _submitted_file,
    _upload_raising,
    _upload_session,
)


@pytest.fixture
def events():
    emitted = []
    with patch("perma.ia_metrics.logger") as logger:
        logger.info.side_effect = lambda message: emitted.append(json.loads(message))
        yield emitted


def _flows(events):
    return [{k: v for k, v in e.items() if k not in ("ia_metrics", "event", "item")} for e in events if e["event"] == "ia_flow"]


@pytest.mark.django_db
def test_a_successful_upload_is_started_then_submitted(complete_link, events):
    with (
        patch("perma.celery_tasks.get_ia_session", return_value=_upload_session()),
        patch.object(Link, "get_warc", return_value=nullcontext(BytesIO(b"warc"))),
    ):
        upload_link_to_internet_archive.run(complete_link.guid)

    assert _flows(events) == [{"kind": "upload_started", "n": 1}, {"kind": "upload_submitted", "n": 1}]
    assert all(e["item"].startswith("daily_perma_cc_") for e in events)


@pytest.mark.django_db
@pytest.mark.parametrize("error, expected", [
    (_http_error(503), [{"kind": "upload_retry", "n": 1, "reason": "rate_limit"}]),
    (_http_error(500), [{"kind": "http_error", "n": 1, "status": 500}, {"kind": "upload_retry", "n": 1, "reason": "http"}]),
    (_http_error(503, "Failed to get necessary short term bucket lock"), [{"kind": "upload_retry", "n": 1, "reason": "bucket_lock"}]),
    (requests.exceptions.ConnectionError(), [{"kind": "upload_retry", "n": 1, "reason": "connection"}]),
    (SoftTimeLimitExceeded(), [{"kind": "upload_retry", "n": 1, "reason": "timeout"}]),
])
def test_upload_retries_record_their_reason(complete_link, events, error, expected):
    _upload_raising(complete_link, error)

    assert _flows(events)[1:] == expected


@pytest.mark.django_db
@pytest.mark.parametrize("over_limit, detail, limit", [
    (True, {}, "ia_over_limit"),
    (False, {"total_tasks_queued": 990}, "global"),
    (False, {"accesskey_tasks_queued": 99}, "accesskey"),
    (False, {"bucket_tasks_queued": 99}, "bucket"),
])
def test_rate_limited_uploads_record_the_limit(complete_link, events, over_limit, detail, limit):
    s3_details = _s3_details()
    s3_details["detail"].update(detail)
    session = _overloaded_session()
    session.get_s3_load_info.return_value = (over_limit, s3_details)
    with (
        patch("perma.celery_tasks.get_ia_session", return_value=session),
        patch.object(upload_link_to_internet_archive, "apply_async"),
    ):
        upload_link_to_internet_archive.run(complete_link.guid)

    assert _flows(events)[1:] == [
        {"kind": "rate_limited", "n": 1, "limit": limit},
        {"kind": "upload_retry", "n": 1, "reason": "rate_limit"},
    ]


@pytest.mark.django_db
def test_a_lost_claim_and_a_stale_reattempt_are_recorded(complete_link, events):
    perma_file = _file_with_status(_daily_item(complete_link), complete_link, "upload_attempted")
    with patch("perma.celery_tasks.get_ia_session", return_value=_overloaded_session()):
        upload_link_to_internet_archive.run(complete_link.guid)
        _stale(perma_file, 1)
        with patch.object(upload_link_to_internet_archive, "apply_async"):
            upload_link_to_internet_archive.run(complete_link.guid)

    assert _flows(events)[0] == {"kind": "upload_claim_lost", "n": 1}
    assert _flows(events)[1] == {"kind": "upload_stale_reattempt", "n": 1, "attempt": 2}


@pytest.mark.django_db
def test_confirmation_records_confirmed_and_unconfirmed_counts(complete_link_factory, events):
    present, lost = complete_link_factory(), complete_link_factory()
    perma_item = _daily_item(present)
    _submitted_file(perma_item, present, age=timedelta(minutes=20))
    _submitted_file(perma_item, lost, age=settings.INTERNET_ARCHIVE_UPLOAD_CONFIRMATION_MAX_AGE)
    session = _fake_session(_ia_item([_ia_file_entry(present)]))

    with patch("perma.celery_tasks.get_ia_session", return_value=session):
        confirm_files_uploaded_to_internet_archive_item.run(perma_item.identifier)

    assert _flows(events) == [{"kind": "upload_confirmed", "n": 1}, {"kind": "upload_unconfirmed", "n": 1}]


@pytest.mark.django_db
def test_deletions_record_start_retry_submission_and_confirmation(complete_link, events):
    perma_file = _file_with_status(_daily_item(complete_link), complete_link, "confirmed_present")
    ia_file = Mock()
    ia_file.delete.side_effect = [_http_error(500), SimpleNamespace(status_code=204, text="")]
    ia_item = Mock(files_count=3, item_metadata={"files": []})
    ia_item.get_file.return_value = ia_file
    with (
        patch("perma.celery_tasks.get_ia_session", return_value=_fake_session(ia_item)),
        patch.object(delete_link_from_daily_item, "apply_async") as apply_async,
    ):
        delete_link_from_daily_item.run(complete_link.guid)
        delete_link_from_daily_item.run(complete_link.guid)  # a duplicate while the retry waits
        delete_link_from_daily_item.push_request(**apply_async.call_args.kwargs["headers"])
        try:
            delete_link_from_daily_item.run(*apply_async.call_args.args[0])
        finally:
            delete_link_from_daily_item.pop_request()
        confirm_file_deleted_from_daily_item.run(perma_file.id)

    assert [f["kind"] for f in _flows(events)] == [
        "deletion_started", "http_error", "deletion_retry", "deletion_claim_lost", "deletion_submitted", "deletion_confirmed",
    ]


@pytest.mark.django_db
def test_giving_up_records_a_failed_deletion(complete_link, events):
    Link.objects.filter(pk=complete_link.pk).update(is_private=True)
    perma_file = _file_with_status(_daily_item(complete_link), complete_link, "deletion_attempted")
    _stale(perma_file, settings.INTERNET_ARCHIVE_MAX_ATTEMPTS_PER_FILE)

    with patch.object(delete_link_from_daily_item, "delay"):
        queue_internet_archive_deletions.run()

    assert _flows(events) == [{"kind": "deletion_failed", "n": 1}]
    assert InternetArchiveFile.objects.get(pk=perma_file.pk).status == "deletion_failed"


def _states(events):
    return [e for e in events if e["event"] == "ia_state"]


def _run_producer(session=None, broker=None, date_string=None):
    broker = broker or fakeredis.FakeStrictRedis()
    with (
        patch("perma.celery_tasks.redis.from_url", return_value=broker),
        patch("perma.celery_tasks.get_ia_session", return_value=session or _fake_session(Mock())),
        patch.object(upload_link_to_internet_archive, "delay"),
    ):
        conditionally_queue_internet_archive_uploads_for_date_range.run(date_string, date_string)


@pytest.fixture
def broker():
    return fakeredis.FakeStrictRedis()


@pytest.mark.django_db
def test_state_after_queuing(complete_link, events):
    _run_producer(date_string=complete_link.creation_timestamp.strftime("%Y-%m-%d"))

    [state] = _states(events)
    assert state["decision"] == "queued"
    assert state["queued"] == 1
    assert state["ia_total_tasks_queued"] == 0 and state["ia_total_global_limit"] == 1_000 and state["ia_over_limit"] == 0
    assert isinstance(state["state_query_ms"], int)


@pytest.mark.django_db
def test_state_when_nothing_is_pending(events):
    _run_producer(date_string="1999-01-01")

    [state] = _states(events)
    assert state["decision"] == "nothing_pending"
    assert state["queued"] == 0


@pytest.mark.django_db
def test_state_when_ia_is_overloaded(complete_link, events):
    _run_producer(session=_overloaded_session(), date_string=complete_link.creation_timestamp.strftime("%Y-%m-%d"))

    [state] = _states(events)
    assert (state["decision"], state["ia_over_limit"]) == ("skip_ia_load", 1)


@pytest.mark.django_db
def test_state_when_the_ia_queue_has_work(events, broker):
    broker.rpush("ia", "message")

    _run_producer(broker=broker, date_string="1999-01-01")

    [state] = _states(events)
    assert (state["decision"], state["queue_ia"]) == ("skip_queue_nonempty", 1)
    assert "ia_over_limit" not in state


@pytest.mark.django_db
def test_state_at_capacity(events, settings):
    settings.INTERNET_ARCHIVE_MAX_SIMULTANEOUS_UPLOADS = 0

    _run_producer(date_string="1999-01-01")

    assert _states(events)[0]["decision"] == "skip_at_capacity"


@pytest.mark.django_db
def test_state_when_another_run_holds_the_lock(events, broker):
    broker.set(IA_UPLOAD_QUEUING_LOCK, 1)

    _run_producer(broker=broker, date_string="1999-01-01")

    [state] = _states(events)
    assert state["decision"] == "skip_lock"
    assert "in_flight_derived" in state


@pytest.mark.django_db
def test_state_counts_files_and_pending_links(complete_link_factory, events):
    links = [complete_link_factory() for _ in range(6)]
    perma_item = _daily_item(links[0])
    stale_age = settings.INTERNET_ARCHIVE_ATTEMPT_STALE_AFTER + timedelta(minutes=1)
    _file_with_status(perma_item, links[0], "upload_attempted")
    _file_with_status(perma_item, links[1], "upload_attempted", None)
    _file_with_status(perma_item, links[4], "upload_attempted", stale_age)
    _file_with_status(perma_item, links[2], "upload_submitted", timedelta(hours=30))
    _file_with_status(perma_item, links[3], "upload_failed")
    # links[5] has no file: pending; links[1] and links[4] are stale attempts: pending too
    date_string = links[0].creation_timestamp.strftime("%Y-%m-%d")

    _run_producer(session=_overloaded_session(), date_string=date_string)

    [state] = _states(events)
    assert {k: state[k] for k in (
        "in_flight_derived", "attempted_fresh", "attempted_stale", "attempted_legacy", "submitted", "submitted_over_24h",
        "failed_upload", "in_flight_stored", "pending_recent_total", "pending_oldest_day_age_days",
    )} == {
        "in_flight_derived": 2, "attempted_fresh": 1, "attempted_stale": 1, "attempted_legacy": 1, "submitted": 1,
        "submitted_over_24h": 1, "failed_upload": 1, "in_flight_stored": 2, "pending_recent_total": 3,
        "pending_oldest_day_age_days": 0,
    }
    assert state["pending_by_day"] == {date_string: 3}
    assert 29.9 < state["oldest_submitted_hours"] < 30.1


@pytest.mark.django_db
def test_state_leaves_out_fields_whose_query_times_out(events, settings):
    settings.INTERNET_ARCHIVE_STATE_STATEMENT_TIMEOUT_MS = 10

    def slow():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_sleep(1)")
        return {"pending_recent_total": 1}

    with patch("perma.celery_tasks.ia_pending_state", slow):
        _run_producer(date_string="1999-01-01")

    [state] = _states(events)
    assert "pending_recent_total" not in state
    assert state["in_flight_derived"] == 0


@pytest.mark.django_db
def test_state_is_cached_for_the_stats_page(events):
    cache.delete(IA_STATE_CACHE_KEY)

    _run_producer(date_string="1999-01-01")

    emitted = {k: v for k, v in _states(events)[0].items() if k not in ("ia_metrics", "event")}
    assert cache.get(IA_STATE_CACHE_KEY)["state"] == emitted
    cache.delete(IA_STATE_CACHE_KEY)


@pytest.mark.django_db
def test_state_counts_unconfirmed_deletions(complete_link, events):
    _file_with_status(_daily_item(complete_link), complete_link, "deletion_unconfirmed")

    _run_producer(date_string="1999-01-01")

    [state] = _states(events)
    assert (state["unconfirmed_deletion"], state["in_flight_derived"]) == (1, 0)


@pytest.mark.django_db
def test_giving_up_on_a_deletion_confirmation_is_recorded(complete_link, events):
    perma_file = _file_with_status(
        _daily_item(complete_link), complete_link, "deletion_submitted", settings.INTERNET_ARCHIVE_DELETION_CONFIRMATION_MAX_AGE
    )
    ia_item = Mock(files_count=3, item_metadata={"files": [{"name": f"{complete_link.guid}.warc.gz"}]})

    with patch("perma.celery_tasks.get_ia_session", return_value=_fake_session(ia_item)):
        confirm_file_deleted_from_daily_item.run(perma_file.id)

    assert _flows(events) == [{"kind": "deletion_unconfirmed", "n": 1}]


@pytest.mark.django_db
def test_state_counts_items_held_back_for_ia_tasks(complete_link, events):
    perma_item = _daily_item(complete_link)
    InternetArchiveItem.objects.filter(pk=perma_item.pk).update(ia_tasks_blocked_since=timezone.now())

    _run_producer(date_string="1999-01-01")

    assert _states(events)[0]["items_blocked_by_ia_tasks"] == 1
