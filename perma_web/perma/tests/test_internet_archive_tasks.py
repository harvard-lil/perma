from contextlib import nullcontext
from datetime import timedelta
import logging
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import ANY, Mock, patch

import fakeredis
import pytest
import requests
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.core.files.storage import storages
from django.utils import timezone
from psycopg2.extras import DateTimeTZRange

from perma.celery_tasks import (
    IA_UPLOAD_QUEUING_LOCK,
    conditionally_queue_internet_archive_uploads_for_date_range,
    confirm_file_deleted_from_daily_item,
    confirm_file_uploaded_to_internet_archive,
    confirm_files_uploaded_to_internet_archive_item,
    delete_link_from_daily_item,
    ia_confirmation_interval,
    ia_rate_limit_countdown,
    queue_file_uploaded_confirmation_tasks,
    upload_link_to_internet_archive,
)
from perma.models import InternetArchiveFile, InternetArchiveItem, Link


def _s3_details():
    return {
        "detail": {
            "accesskey_ration": 100,
            "accesskey_tasks_queued": 0,
            "bucket_ration": 100,
            "bucket_tasks_queued": 0,
            "total_global_limit": 1_000,
            "total_tasks_queued": 0,
        }
    }


def _daily_item(link):
    date_string = link.creation_timestamp.strftime("%Y-%m-%d")
    start = InternetArchiveItem.datetime(f"{date_string} 00:00:00")
    return InternetArchiveItem.objects.create(
        identifier=InternetArchiveItem.DAILY_IDENTIFIER.format(
            prefix=settings.INTERNET_ARCHIVE_DAILY_IDENTIFIER_PREFIX,
            date_string=date_string,
        ),
        span=DateTimeTZRange(start, start + timedelta(days=1)),
    )


def _fake_session(ia_item):
    session = Mock()
    session.get_s3_load_info.return_value = (False, _s3_details())
    session.get_item.return_value = ia_item
    return session


@pytest.mark.django_db
def test_upload_to_internet_archive_sends_expected_file_and_metadata(complete_link):
    ia_item = Mock()
    uploaded_bodies = []

    def upload_file(**kwargs):
        uploaded_bodies.append(kwargs["body"].read())
        return SimpleNamespace(status_code=200, text="")

    ia_item.upload_file.side_effect = upload_file
    session = _fake_session(ia_item)

    with (
        patch("perma.celery_tasks.get_ia_session", return_value=session),
        patch.object(Link, "get_warc", return_value=nullcontext(BytesIO(b"warc"))),
    ):
        upload_link_to_internet_archive.run(complete_link.guid)

    date_string = complete_link.creation_timestamp.strftime("%Y-%m-%d")
    identifier = InternetArchiveItem.DAILY_IDENTIFIER.format(
        prefix=settings.INTERNET_ARCHIVE_DAILY_IDENTIFIER_PREFIX,
        date_string=date_string,
    )
    session.get_s3_load_info.assert_called_once_with(
        identifier=identifier,
        access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY,
    )
    session.get_item.assert_called_once_with(identifier)
    upload_kwargs = ia_item.upload_file.call_args.kwargs
    upload_kwargs.pop("body")
    assert uploaded_bodies == [b"warc"]
    assert upload_kwargs == {
        "key": InternetArchiveFile.WARC_FILENAME.format(guid=complete_link.guid),
        "metadata": InternetArchiveItem.standard_metadata_for_date(date_string),
        "file_metadata": InternetArchiveFile.standard_metadata_for_link(complete_link),
        "access_key": settings.INTERNET_ARCHIVE_ACCESS_KEY,
        "secret_key": settings.INTERNET_ARCHIVE_SECRET_KEY,
        "queue_derive": False,
        "retries": 0,
        "retries_sleep": 0,
        "verbose": False,
        "debug": False,
    }
    assert InternetArchiveFile.objects.get(link=complete_link, item_id=identifier).status == "upload_submitted"


@pytest.mark.django_db
def test_upload_to_internet_archive_requeues_failed_upload(complete_link):
    ia_item = Mock()
    ia_item.upload_file.return_value = SimpleNamespace(status_code=500, text="temporary error")
    session = _fake_session(ia_item)

    with (
        patch("perma.celery_tasks.get_ia_session", return_value=session),
        patch.object(Link, "get_warc", return_value=nullcontext(BytesIO(b"warc"))),
        patch.object(upload_link_to_internet_archive, "delay") as delay,
    ):
        upload_link_to_internet_archive.run(complete_link.guid)

    delay.assert_called_once_with(complete_link.guid, 1, 0, ANY)


def _ia_file_entry(link, **overrides):
    return {
        "name": InternetArchiveFile.WARC_FILENAME.format(guid=link.guid),
        "size": "123",
        **InternetArchiveFile.standard_metadata_for_link(link),
        **overrides,
    }


def _ia_item(files, tasks=None):
    item_metadata = {
        "metadata": {
            "addeddate": "2024-01-02 03:04:05",
            "title": "Daily captures",
            "description": "Remote item description",
        },
        "files": files,
        "files_count": len(files) + 2,
    }
    if tasks is not None:
        item_metadata["tasks"] = tasks
    return Mock(item_metadata=item_metadata)


def _submitted_file(item, link, age=timedelta(0)):
    perma_file = InternetArchiveFile.objects.create(item=item, link=link, status="upload_submitted")
    InternetArchiveFile.objects.filter(pk=perma_file.pk).update(status_updated=timezone.now() - age)
    perma_file.refresh_from_db()
    return perma_file


@pytest.mark.django_db
def test_upload_confirmation_checks_all_of_an_items_files_with_one_fetch(complete_link_factory):
    present, missing = complete_link_factory(), complete_link_factory()
    perma_item = _daily_item(present)
    present_file = _submitted_file(perma_item, present, age=timedelta(minutes=20))
    missing_file = _submitted_file(perma_item, missing, age=timedelta(minutes=20))
    perma_item.tasks_in_progress = 50
    perma_item.save()
    session = _fake_session(_ia_item([_ia_file_entry(present)]))

    with patch("perma.celery_tasks.get_ia_session", return_value=session):
        confirm_files_uploaded_to_internet_archive_item.run(perma_item.identifier)

    session.get_item.assert_called_once_with(perma_item.identifier)
    present_file.refresh_from_db()
    missing_file.refresh_from_db()
    perma_item.refresh_from_db()
    assert present_file.status == "confirmed_present"
    assert present_file.cached_size == 123
    assert present_file.cached_title == InternetArchiveFile.standard_metadata_for_link(present)["title"]
    assert missing_file.status == "upload_submitted"
    assert perma_item.confirmed_exists is True
    assert perma_item.cached_title == "Daily captures"
    assert perma_item.cached_file_count == 3
    assert perma_item.derive_required is True
    # the missing file is still in flight; the stale count of 50 is replaced
    assert perma_item.tasks_in_progress == 1
    # backoff: a quarter of the newest pending file's 20-minute age
    expected_next = timezone.now() + timedelta(minutes=5)
    assert abs(perma_item.next_confirmation_check - expected_next) < timedelta(seconds=30)


@pytest.mark.django_db
def test_upload_confirmation_rejects_mismatched_metadata(complete_link):
    perma_item = _daily_item(complete_link)
    perma_file = _submitted_file(perma_item, complete_link)
    session = _fake_session(_ia_item([_ia_file_entry(complete_link, title="an older title")]))

    with patch("perma.celery_tasks.get_ia_session", return_value=session):
        confirm_files_uploaded_to_internet_archive_item.run(perma_item.identifier)

    perma_file.refresh_from_db()
    assert perma_file.status == "upload_submitted"


@pytest.mark.django_db
def test_upload_confirmation_gives_up_after_max_age(complete_link, caplog):
    perma_item = _daily_item(complete_link)
    perma_file = _submitted_file(
        perma_item, complete_link, age=settings.INTERNET_ARCHIVE_UPLOAD_CONFIRMATION_MAX_AGE
    )
    perma_item.tasks_in_progress = 1
    perma_item.save()
    session = _fake_session(_ia_item([_ia_file_entry(complete_link, title="an older title")]))

    with (
        patch("perma.celery_tasks.get_ia_session", return_value=session),
        caplog.at_level(logging.ERROR, logger="celery.django"),
    ):
        confirm_files_uploaded_to_internet_archive_item.run(perma_item.identifier)

    perma_file.refresh_from_db()
    perma_item.refresh_from_db()
    assert perma_file.status == "upload_unconfirmed"
    assert perma_item.next_confirmation_check is None
    assert perma_item.tasks_in_progress == 0
    [record] = [r for r in caplog.records if r.levelname == "ERROR"]
    assert complete_link.guid in record.getMessage()
    assert "an older title" in record.getMessage()


@pytest.mark.django_db
def test_upload_confirmation_starts_the_clock_for_files_without_a_status_time(complete_link):
    perma_item = _daily_item(complete_link)
    perma_file = InternetArchiveFile.objects.create(item=perma_item, link=complete_link, status="upload_submitted")
    InternetArchiveFile.objects.filter(pk=perma_file.pk).update(status_updated=None)
    session = _fake_session(_ia_item([]))

    with patch("perma.celery_tasks.get_ia_session", return_value=session):
        confirm_files_uploaded_to_internet_archive_item.run(perma_item.identifier)

    perma_file.refresh_from_db()
    assert perma_file.status == "upload_submitted"
    assert timezone.now() - perma_file.status_updated < timedelta(minutes=1)


@pytest.mark.django_db
def test_upload_confirmation_waits_longer_when_ia_tasks_are_stuck(complete_link):
    perma_item = _daily_item(complete_link)
    _submitted_file(perma_item, complete_link)
    session = _fake_session(_ia_item([], tasks=[{"cmd": "archive.php", "wait_admin": 2}]))

    with patch("perma.celery_tasks.get_ia_session", return_value=session):
        confirm_files_uploaded_to_internet_archive_item.run(perma_item.identifier)

    perma_item.refresh_from_db()
    assert perma_item.next_confirmation_check - timezone.now() > (
        settings.INTERNET_ARCHIVE_CONFIRMATION_BLOCKED_TASKS_INTERVAL - timedelta(minutes=1)
    )


@pytest.mark.django_db
def test_upload_confirmation_connection_error_leaves_item_due(complete_link):
    perma_item = _daily_item(complete_link)
    perma_file = _submitted_file(perma_item, complete_link)
    session = Mock()
    session.get_item.side_effect = requests.exceptions.ConnectionError

    with patch("perma.celery_tasks.get_ia_session", return_value=session):
        confirm_files_uploaded_to_internet_archive_item.run(perma_item.identifier)

    perma_file.refresh_from_db()
    perma_item.refresh_from_db()
    assert perma_file.status == "upload_submitted"
    assert perma_item.next_confirmation_check is None


def test_confirmation_interval_backs_off_with_age():
    assert ia_confirmation_interval(timedelta(minutes=4), []) == timedelta(minutes=1)
    assert ia_confirmation_interval(timedelta(hours=4), []) == timedelta(hours=1)
    assert ia_confirmation_interval(timedelta(days=3), []) == settings.INTERNET_ARCHIVE_CONFIRMATION_MAX_INTERVAL
    queued = [{"cmd": "archive.php", "wait_admin": 0}]
    assert ia_confirmation_interval(timedelta(minutes=4), queued) == settings.INTERNET_ARCHIVE_CONFIRMATION_PENDING_TASKS_INTERVAL
    paused = [{"cmd": "archive.php", "wait_admin": "9"}]
    assert ia_confirmation_interval(timedelta(minutes=4), paused) == settings.INTERNET_ARCHIVE_CONFIRMATION_BLOCKED_TASKS_INTERVAL


@pytest.mark.django_db
def test_confirmation_queue_task_queues_each_due_item_once(complete_link_factory):
    due_links = [complete_link_factory(), complete_link_factory()]
    due_item = _daily_item(due_links[0])
    for link in due_links:
        _submitted_file(due_item, link)

    later_link = complete_link_factory()
    later_item = InternetArchiveItem.objects.create(
        identifier="daily_perma_cc_1999-01-01",
        span=DateTimeTZRange(InternetArchiveItem.datetime("1999-01-01 00:00:00"), InternetArchiveItem.datetime("1999-01-02 00:00:00")),
        next_confirmation_check=timezone.now() + timedelta(hours=1),
    )
    _submitted_file(later_item, later_link)

    redis_client = Mock()
    redis_client.llen.return_value = 0
    with (
        patch("perma.celery_tasks.redis.from_url", return_value=redis_client),
        patch.object(confirm_files_uploaded_to_internet_archive_item, "delay") as delay,
    ):
        queue_file_uploaded_confirmation_tasks.run()

    delay.assert_called_once_with(due_item.identifier)


@pytest.mark.django_db
def test_superseded_per_file_confirmation_task_does_not_fetch(complete_link):
    perma_file = _submitted_file(_daily_item(complete_link), complete_link)

    with patch("perma.celery_tasks.get_ia_session") as get_ia_session:
        confirm_file_uploaded_to_internet_archive.run(perma_file.id)

    get_ia_session.assert_not_called()


@pytest.mark.django_db
def test_tasks_in_progress_is_derived_from_file_statuses(complete_link_factory):
    links = [complete_link_factory() for _ in range(6)]
    perma_item = _daily_item(links[0])
    perma_item.tasks_in_progress = 100
    perma_item.save()
    statuses = [
        ("upload_attempted", timedelta(0)),
        ("upload_submitted", timedelta(days=2)),
        ("deletion_submitted", timedelta(0)),
        # an attempt whose task ended without recording a result
        ("upload_attempted", settings.INTERNET_ARCHIVE_ATTEMPT_STALE_AFTER + timedelta(minutes=1)),
        ("upload_unconfirmed", timedelta(0)),
        ("confirmed_present", timedelta(0)),
    ]
    for link, (status, age) in zip(links, statuses):
        perma_file = InternetArchiveFile.objects.create(item=perma_item, link=link, status=status)
        InternetArchiveFile.objects.filter(pk=perma_file.pk).update(status_updated=timezone.now() - age)
    idle_item = InternetArchiveItem.objects.create(identifier="idle", tasks_in_progress=5)

    InternetArchiveItem.refresh_tasks_in_progress()

    perma_item.refresh_from_db()
    idle_item.refresh_from_db()
    assert perma_item.tasks_in_progress == 3
    assert idle_item.tasks_in_progress == 0


@pytest.mark.django_db
def test_saving_a_file_status_records_when(complete_link):
    perma_file = InternetArchiveFile.objects.create(
        item=_daily_item(complete_link), link=complete_link, status="upload_attempted"
    )
    InternetArchiveFile.objects.filter(pk=perma_file.pk).update(status_updated=None)
    perma_file.cached_title = "unrelated"
    perma_file.save(update_fields=["cached_title"])
    perma_file.refresh_from_db()
    assert perma_file.status_updated is None

    perma_file.save(update_fields=["status"])
    perma_file.refresh_from_db()
    assert timezone.now() - perma_file.status_updated < timedelta(minutes=1)


@pytest.mark.django_db
def test_upload_queueing_ignores_an_inflated_counter(complete_link):
    perma_item = _daily_item(complete_link)
    perma_item.tasks_in_progress = 100
    perma_item.save()
    date_string = complete_link.creation_timestamp.strftime("%Y-%m-%d")

    redis_client = Mock()
    redis_client.llen.return_value = 0
    with (
        patch("perma.celery_tasks.redis.from_url", return_value=redis_client),
        patch("perma.celery_tasks.queue_internet_archive_uploads_for_date", return_value=1) as queue_for_date,
    ):
        conditionally_queue_internet_archive_uploads_for_date_range.run(date_string, date_string, daily_limit=100)

    queue_for_date.assert_called_once_with(date_string, 100)
    perma_item.refresh_from_db()
    assert perma_item.tasks_in_progress == 0


@pytest.mark.django_db
def test_delete_from_internet_archive_sends_expected_request(complete_link):
    perma_item = _daily_item(complete_link)
    InternetArchiveFile.objects.create(
        item=perma_item,
        link=complete_link,
        status="confirmed_present",
    )
    ia_file = Mock()
    ia_file.delete.return_value = SimpleNamespace(status_code=204, text="")
    ia_item = Mock()
    ia_item.get_file.return_value = ia_file
    session = _fake_session(ia_item)

    with patch("perma.celery_tasks.get_ia_session", return_value=session):
        delete_link_from_daily_item.run(complete_link.guid)

    ia_file.delete.assert_called_once_with(
        cascade_delete=False,
        access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY,
        secret_key=settings.INTERNET_ARCHIVE_SECRET_KEY,
        verbose=False,
        debug=False,
        retries=0,
    )
    assert InternetArchiveFile.objects.get(link=complete_link, item=perma_item).status == "deletion_submitted"


@pytest.mark.django_db
def test_deletion_confirmation_requeues_connection_errors(complete_link):
    perma_item = _daily_item(complete_link)
    perma_file = InternetArchiveFile.objects.create(
        item=perma_item,
        link=complete_link,
        status="deletion_submitted",
    )
    session = Mock()
    session.get_item.side_effect = requests.exceptions.ConnectionError

    with (
        patch("perma.celery_tasks.get_ia_session", return_value=session),
        patch.object(confirm_file_deleted_from_daily_item, "delay") as delay,
    ):
        confirm_file_deleted_from_daily_item.run(perma_file.id)

    delay.assert_called_once_with(perma_file.id, 0, 1)


def test_upload_task_has_its_own_time_limits():
    assert upload_link_to_internet_archive.soft_time_limit == settings.INTERNET_ARCHIVE_UPLOAD_SOFT_TIME_LIMIT
    assert upload_link_to_internet_archive.time_limit == settings.INTERNET_ARCHIVE_UPLOAD_TIME_LIMIT
    assert settings.CELERY_TASK_SOFT_TIME_LIMIT < upload_link_to_internet_archive.soft_time_limit < upload_link_to_internet_archive.time_limit


@pytest.mark.django_db
@pytest.mark.parametrize("timeouts, requeued", [(0, True), (settings.INTERNET_ARCHIVE_UPLOAD_MAX_TIMEOUTS - 1, False)])
def test_upload_timeouts_are_retried_a_limited_number_of_times(complete_link, timeouts, requeued):
    assert settings.INTERNET_ARCHIVE_UPLOAD_MAX_TIMEOUTS
    ia_item = Mock()
    ia_item.upload_file.side_effect = SoftTimeLimitExceeded
    session = _fake_session(ia_item)

    with (
        patch("perma.celery_tasks.get_ia_session", return_value=session),
        patch.object(Link, "get_warc", return_value=nullcontext(BytesIO(b"warc"))),
        patch.object(upload_link_to_internet_archive, "delay") as delay,
    ):
        upload_link_to_internet_archive.run(complete_link.guid, 0, timeouts)

    if requeued:
        delay.assert_called_once_with(complete_link.guid, 0, timeouts + 1, ANY)
    else:
        delay.assert_not_called()


@pytest.mark.django_db
def test_upload_does_not_touch_the_stored_counter(complete_link):
    perma_item = _daily_item(complete_link)
    ia_item = Mock()
    ia_item.upload_file.return_value = SimpleNamespace(status_code=200, text="")

    with (
        patch("perma.celery_tasks.get_ia_session", return_value=_fake_session(ia_item)),
        patch.object(Link, "get_warc", return_value=nullcontext(BytesIO(b"warc"))),
    ):
        upload_link_to_internet_archive.run(complete_link.guid)

    perma_item.refresh_from_db()
    assert perma_item.tasks_in_progress == 0
    perma_file = InternetArchiveFile.objects.get(item=perma_item, link=complete_link)
    assert perma_file.status == "upload_submitted"
    assert perma_file.status_updated is not None


def test_s3_reads_spill_to_disk_above_the_memory_limit():
    storage = storages[settings.WARC_STORAGE]
    assert storage.max_memory_size == settings.AWS_S3_MAX_MEMORY_SIZE > 0

    name = "ia-tests/spill.bin"
    storage.save(name, BytesIO(b"x" * (settings.AWS_S3_MAX_MEMORY_SIZE + 1)))
    try:
        with storage.open(name, "rb") as f:
            f.read(1)
            assert f.file._rolled
    finally:
        storage.delete(name)


def _overloaded_session():
    session = Mock()
    session.get_s3_load_info.return_value = (True, _s3_details())
    return session


@pytest.mark.django_db
def test_rate_limited_upload_retries_after_a_delay(complete_link):
    with (
        patch("perma.celery_tasks.get_ia_session", return_value=_overloaded_session()),
        patch("perma.celery_tasks.ia_rate_limit_countdown", return_value=42) as countdown,
        patch.object(upload_link_to_internet_archive, "apply_async") as apply_async,
        patch.object(upload_link_to_internet_archive, "delay") as delay,
    ):
        upload_link_to_internet_archive.run(complete_link.guid, 3, 1)

    countdown.assert_called_once_with(3)
    apply_async.assert_called_once_with((complete_link.guid, 4, 1, ANY), countdown=42)
    delay.assert_not_called()


@pytest.mark.django_db
def test_rate_limited_deletion_retries_after_a_delay(complete_link):
    perma_item = _daily_item(complete_link)
    InternetArchiveFile.objects.create(
        item=perma_item,
        link=complete_link,
        status="confirmed_present",
    )

    with (
        patch("perma.celery_tasks.get_ia_session", return_value=_overloaded_session()),
        patch("perma.celery_tasks.ia_rate_limit_countdown", return_value=42),
        patch.object(delete_link_from_daily_item, "apply_async") as apply_async,
        patch.object(delete_link_from_daily_item, "delay") as delay,
    ):
        delete_link_from_daily_item.run(complete_link.guid)

    apply_async.assert_called_once_with((complete_link.guid, 1), countdown=42)
    delay.assert_not_called()


@pytest.mark.parametrize("attempts, low, high", [(0, 15, 30), (2, 60, 120), (1_000, 300, 600)])
def test_rate_limit_countdown_doubles_up_to_the_maximum(settings, attempts, low, high):
    settings.INTERNET_ARCHIVE_RATE_LIMIT_RETRY_BASE_DELAY = 30
    settings.INTERNET_ARCHIVE_RATE_LIMIT_RETRY_MAX_DELAY = 600

    assert low <= ia_rate_limit_countdown(attempts) <= high


def _http_error(status_code, message=""):
    return requests.exceptions.HTTPError(
        f" error uploading to item, {message}",
        response=SimpleNamespace(status_code=status_code),
    )


def _upload_raising(link, error, attempts=0, timeouts=0):
    ia_item = Mock()
    ia_item.upload_file.side_effect = error
    with (
        patch("perma.celery_tasks.get_ia_session", return_value=_fake_session(ia_item)),
        patch.object(Link, "get_warc", return_value=nullcontext(BytesIO(b"warc"))),
        patch("perma.celery_tasks.ia_rate_limit_countdown", return_value=42),
        patch.object(upload_link_to_internet_archive, "apply_async") as apply_async,
        patch.object(upload_link_to_internet_archive, "delay") as delay,
    ):
        upload_link_to_internet_archive.run(link.guid, attempts, timeouts)
    return apply_async, delay


@pytest.mark.django_db
@pytest.mark.parametrize("error", [
    _http_error(503, "Please reduce your request rate."),
    _http_error(503),
])
def test_rate_limited_upload_http_error_retries_after_a_delay(complete_link, error):
    apply_async, delay = _upload_raising(complete_link, error, attempts=2, timeouts=1)

    apply_async.assert_called_once_with((complete_link.guid, 3, 1, ANY), countdown=42)
    delay.assert_not_called()


@pytest.mark.django_db
def test_upload_http_error_counts_as_an_attempt(complete_link):
    apply_async, delay = _upload_raising(complete_link, _http_error(500, "We encountered an internal error."))

    delay.assert_called_once_with(complete_link.guid, 1, 0, ANY)
    apply_async.assert_not_called()


@pytest.mark.django_db
def test_upload_http_error_is_not_retried_past_the_error_limit(complete_link):
    apply_async, delay = _upload_raising(
        complete_link,
        _http_error(500, "We encountered an internal error."),
        attempts=settings.INTERNET_ARCHIVE_RETRY_FOR_ERROR_LIMIT - 1,
    )

    delay.assert_not_called()
    apply_async.assert_not_called()


@pytest.mark.django_db
def test_upload_bucket_lock_error_is_retried_without_counting(complete_link):
    apply_async, delay = _upload_raising(
        complete_link,
        _http_error(503, "Failed to get necessary short term bucket lock"),
        attempts=1,
    )

    delay.assert_called_once_with(complete_link.guid, 1, 0, ANY)
    apply_async.assert_not_called()


@pytest.mark.django_db
def test_upload_connection_error_is_retried_without_counting(complete_link):
    apply_async, delay = _upload_raising(complete_link, requests.exceptions.ConnectionError(), attempts=1)

    delay.assert_called_once_with(complete_link.guid, 1, 0, ANY)
    apply_async.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("error", [_http_error(502), requests.exceptions.ChunkedEncodingError()])
def test_upload_metadata_read_error_counts_as_an_attempt(complete_link, error):
    session = _fake_session(Mock())
    session.get_item.side_effect = error
    with (
        patch("perma.celery_tasks.get_ia_session", return_value=session),
        patch.object(upload_link_to_internet_archive, "delay") as delay,
    ):
        upload_link_to_internet_archive.run(complete_link.guid)

    delay.assert_called_once_with(complete_link.guid, 1, 0, ANY)


def _deletion_raising(link, error):
    InternetArchiveFile.objects.create(item=_daily_item(link), link=link, status="confirmed_present")
    ia_file = Mock()
    ia_file.delete.side_effect = error
    ia_item = Mock()
    ia_item.get_file.return_value = ia_file
    with (
        patch("perma.celery_tasks.get_ia_session", return_value=_fake_session(ia_item)),
        patch("perma.celery_tasks.ia_rate_limit_countdown", return_value=42),
        patch.object(delete_link_from_daily_item, "apply_async") as apply_async,
        patch.object(delete_link_from_daily_item, "delay") as delay,
    ):
        delete_link_from_daily_item.run(link.guid)
    return apply_async, delay


@pytest.mark.django_db
def test_rate_limited_deletion_http_error_retries_after_a_delay(complete_link):
    apply_async, delay = _deletion_raising(complete_link, _http_error(503))

    apply_async.assert_called_once_with((complete_link.guid, 1), countdown=42)
    delay.assert_not_called()


@pytest.mark.django_db
def test_deletion_http_error_counts_as_an_attempt(complete_link):
    apply_async, delay = _deletion_raising(complete_link, _http_error(500))

    delay.assert_called_once_with(complete_link.guid, 1)
    apply_async.assert_not_called()


@pytest.mark.django_db
def test_upload_confirmation_http_error_leaves_item_due(complete_link):
    perma_item = _daily_item(complete_link)
    perma_file = _submitted_file(perma_item, complete_link)
    session = Mock()
    session.get_item.side_effect = _http_error(502)

    with patch("perma.celery_tasks.get_ia_session", return_value=session):
        confirm_files_uploaded_to_internet_archive_item.run(perma_item.identifier)

    perma_file.refresh_from_db()
    perma_item.refresh_from_db()
    assert perma_file.status == "upload_submitted"
    assert perma_item.next_confirmation_check is None


def _file_with_status(item, link, status, age=timedelta(0)):
    perma_file = InternetArchiveFile.objects.create(item=item, link=link, status=status)
    status_updated = None if age is None else timezone.now() - age
    InternetArchiveFile.objects.filter(pk=perma_file.pk).update(status_updated=status_updated)
    return perma_file


@pytest.mark.django_db
def test_upload_pending_includes_stale_attempts(complete_link_factory):
    stale_age = settings.INTERNET_ARCHIVE_ATTEMPT_STALE_AFTER + timedelta(minutes=1)
    new, stale, legacy, running, submitted, present = [complete_link_factory() for _ in range(6)]
    perma_item = _daily_item(new)
    _file_with_status(perma_item, stale, "upload_attempted", stale_age)
    _file_with_status(perma_item, legacy, "upload_attempted", None)
    _file_with_status(perma_item, running, "upload_attempted")
    _file_with_status(perma_item, submitted, "upload_submitted", stale_age)
    _file_with_status(perma_item, present, "confirmed_present", stale_age)
    date_string = new.creation_timestamp.strftime("%Y-%m-%d")

    pending = set(Link.objects.ia_upload_pending(date_string, limit=None).values_list("guid", flat=True))

    assert pending == {new.guid, stale.guid, legacy.guid}


@pytest.mark.django_db
def test_upload_queueing_requeues_stale_attempts_but_leaves_complete_items_alone(complete_link):
    perma_item = _daily_item(complete_link)
    _file_with_status(perma_item, complete_link, "upload_attempted", None)
    date_string = complete_link.creation_timestamp.strftime("%Y-%m-%d")
    redis_client = Mock()
    redis_client.llen.return_value = 0

    def run_producer():
        with (
            patch("perma.celery_tasks.redis.from_url", return_value=redis_client),
            patch.object(upload_link_to_internet_archive, "delay") as delay,
        ):
            conditionally_queue_internet_archive_uploads_for_date_range.run(date_string, date_string)
        return delay

    InternetArchiveItem.objects.filter(pk=perma_item.pk).update(complete=True)
    run_producer().assert_not_called()

    InternetArchiveItem.objects.filter(pk=perma_item.pk).update(complete=False)
    run_producer().assert_called_once_with(complete_link.guid)


@pytest.mark.django_db
def test_an_upload_attempt_can_be_claimed_by_one_task_at_a_time(complete_link):
    perma_item = _daily_item(complete_link)

    first = InternetArchiveFile.claim_upload(perma_item.identifier, complete_link.guid)
    assert first
    assert InternetArchiveFile.claim_upload(perma_item.identifier, complete_link.guid) is None

    retry = InternetArchiveFile.claim_upload(perma_item.identifier, complete_link.guid, first)
    assert retry and retry != first
    assert InternetArchiveFile.claim_upload(perma_item.identifier, complete_link.guid, first) is None

    perma_file = InternetArchiveFile.objects.get(item=perma_item, link=complete_link)
    assert perma_file.status == "upload_attempted"
    assert perma_file.status_updated.isoformat() == retry


@pytest.mark.django_db
@pytest.mark.parametrize("status, age", [
    ("upload_attempted", settings.INTERNET_ARCHIVE_ATTEMPT_STALE_AFTER + timedelta(minutes=1)),
    ("upload_attempted", None),
    ("confirmed_absent", timedelta(0)),
])
def test_any_task_can_claim_a_stale_or_deleted_upload(complete_link, status, age):
    perma_item = _daily_item(complete_link)
    _file_with_status(perma_item, complete_link, status, age)

    assert InternetArchiveFile.claim_upload(perma_item.identifier, complete_link.guid)


def _upload_session():
    ia_item = Mock()
    ia_item.upload_file.return_value = SimpleNamespace(status_code=200, text="")
    return _fake_session(ia_item)


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["upload_attempted", "upload_submitted"])
def test_upload_task_leaves_an_upload_held_by_another_task_alone(complete_link, status):
    perma_file = _file_with_status(_daily_item(complete_link), complete_link, status)
    perma_file.refresh_from_db()
    session = _upload_session()

    with patch("perma.celery_tasks.get_ia_session", return_value=session):
        upload_link_to_internet_archive.run(complete_link.guid)

    session.get_s3_load_info.assert_not_called()
    session.get_item.return_value.upload_file.assert_not_called()
    unchanged = InternetArchiveFile.objects.get(pk=perma_file.pk)
    assert (unchanged.status, unchanged.status_updated) == (status, perma_file.status_updated)


@pytest.mark.django_db
def test_upload_retry_reclaims_its_own_attempt(complete_link):
    with (
        patch("perma.celery_tasks.get_ia_session", return_value=_overloaded_session()),
        patch.object(upload_link_to_internet_archive, "apply_async") as apply_async,
    ):
        upload_link_to_internet_archive.run(complete_link.guid)
    retry_args = apply_async.call_args.args[0]

    # a duplicate message for the same link, arriving while the retry waits
    session = _upload_session()
    with patch("perma.celery_tasks.get_ia_session", return_value=session):
        upload_link_to_internet_archive.run(complete_link.guid)
    session.get_s3_load_info.assert_not_called()

    with (
        patch("perma.celery_tasks.get_ia_session", return_value=session),
        patch.object(Link, "get_warc", return_value=nullcontext(BytesIO(b"warc"))),
    ):
        upload_link_to_internet_archive.run(*retry_args)

    session.get_item.return_value.upload_file.assert_called_once()
    assert InternetArchiveFile.objects.get(link=complete_link).status == "upload_submitted"


@pytest.mark.django_db
def test_upload_retry_yields_to_a_task_that_reclaimed_its_stale_attempt(complete_link):
    perma_item = _daily_item(complete_link)
    old_claim = InternetArchiveFile.claim_upload(perma_item.identifier, complete_link.guid)
    InternetArchiveFile.objects.filter(link=complete_link).update(
        status_updated=timezone.now() - settings.INTERNET_ARCHIVE_ATTEMPT_STALE_AFTER - timedelta(minutes=1)
    )
    assert InternetArchiveFile.claim_upload(perma_item.identifier, complete_link.guid)
    session = _upload_session()

    with patch("perma.celery_tasks.get_ia_session", return_value=session):
        upload_link_to_internet_archive.run(complete_link.guid, 1, 0, old_claim)

    session.get_s3_load_info.assert_not_called()


@pytest.mark.django_db
def test_upload_queueing_runs_one_at_a_time():
    broker = fakeredis.FakeStrictRedis()

    with (
        patch("perma.celery_tasks.redis.from_url", return_value=broker),
        patch("perma.celery_tasks.queue_internet_archive_uploads_for_date_range") as queue_uploads,
    ):
        broker.set(IA_UPLOAD_QUEUING_LOCK, 1)
        conditionally_queue_internet_archive_uploads_for_date_range.run(None, None)
        queue_uploads.assert_not_called()

        broker.delete(IA_UPLOAD_QUEUING_LOCK)
        conditionally_queue_internet_archive_uploads_for_date_range.run(None, None)
        queue_uploads.assert_called_once()

        # the lock is released even when a run fails
        queue_uploads.side_effect = SoftTimeLimitExceeded
        with pytest.raises(SoftTimeLimitExceeded):
            conditionally_queue_internet_archive_uploads_for_date_range.run(None, None)
    assert not broker.exists(IA_UPLOAD_QUEUING_LOCK)


@pytest.mark.django_db
def test_upload_queueing_lock_outlasts_a_run():
    broker = fakeredis.FakeStrictRedis()

    def check_lock(*args):
        assert 0 < broker.ttl(IA_UPLOAD_QUEUING_LOCK) <= settings.CELERY_TASK_TIME_LIMIT

    with (
        patch("perma.celery_tasks.redis.from_url", return_value=broker),
        patch("perma.celery_tasks.queue_internet_archive_uploads_for_date_range", side_effect=check_lock) as queue_uploads,
    ):
        conditionally_queue_internet_archive_uploads_for_date_range.run(None, None)
    queue_uploads.assert_called_once()
