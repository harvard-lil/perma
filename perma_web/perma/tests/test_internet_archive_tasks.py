from contextlib import nullcontext
from datetime import timedelta
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
import requests
from django.conf import settings
from psycopg2.extras import DateTimeTZRange

from perma.celery_tasks import (
    confirm_file_deleted_from_daily_item,
    confirm_file_uploaded_to_internet_archive,
    delete_link_from_daily_item,
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


@pytest.mark.django_db
def test_upload_confirmation_caches_remote_metadata(complete_link):
    perma_item = _daily_item(complete_link)
    perma_file = InternetArchiveFile.objects.create(
        item=perma_item,
        link=complete_link,
        status="upload_submitted",
    )
    metadata = InternetArchiveFile.standard_metadata_for_link(complete_link)
    ia_file = SimpleNamespace(exists=True, metadata=metadata, size=123)
    ia_item = Mock(
        metadata={
            "addeddate": "2024-01-02 03:04:05",
            "title": "Daily captures",
            "description": "Remote item description",
        },
        files_count=7,
    )
    ia_item.get_file.return_value = ia_file
    session = _fake_session(ia_item)

    with patch("perma.celery_tasks.get_ia_session", return_value=session):
        confirm_file_uploaded_to_internet_archive.run(perma_file.id)

    perma_file.refresh_from_db()
    perma_item.refresh_from_db()
    assert perma_file.status == "confirmed_present"
    assert perma_file.cached_size == 123
    assert perma_file.cached_title == metadata["title"]
    assert perma_item.confirmed_exists is True
    assert perma_item.cached_file_count == 7
    assert perma_item.derive_required is True
    session.get_item.assert_called_once_with(perma_item.identifier)
    ia_item.get_file.assert_called_once_with(
        InternetArchiveFile.WARC_FILENAME.format(guid=complete_link.guid)
    )


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
