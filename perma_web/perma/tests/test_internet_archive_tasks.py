from contextlib import nullcontext
from datetime import timedelta
import logging
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
import requests
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.core.files.storage import storages
from django.utils import timezone
from psycopg2.extras import DateTimeTZRange

from perma.celery_tasks import (
    conditionally_queue_internet_archive_uploads_for_date_range,
    confirm_file_deleted_from_daily_item,
    confirm_file_uploaded_to_internet_archive,
    confirm_files_uploaded_to_internet_archive_item,
    delete_link_from_daily_item,
    ia_confirmation_interval,
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

    delay.assert_called_once_with(complete_link.guid, 1, 0)


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
        delay.assert_called_once_with(complete_link.guid, 0, timeouts + 1)
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
