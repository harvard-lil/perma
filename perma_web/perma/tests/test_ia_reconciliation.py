from datetime import datetime, timedelta, timezone as tz
import json
from unittest.mock import patch

import fakeredis
import pytest
from psycopg2.extras import DateTimeTZRange

from perma.celery_tasks import IA_RECONCILE_LOCK, reconcile_internet_archive_files
from perma.models import InternetArchiveFile, InternetArchiveItem, Link
from perma.models.internet_archive import uneditable_daily_item_identifiers
from perma.tests.test_internet_archive_tasks import _daily_item, _file_with_status


def _link_on(factory, day, **fields):
    link = factory()
    Link.objects.all_with_deleted().filter(pk=link.pk).update(
        creation_timestamp=datetime.combine(day, datetime.min.time(), tzinfo=tz.utc) + timedelta(hours=12), **fields
    )
    return Link.objects.all_with_deleted().get(pk=link.pk)


def _item_for(day, complete=False):
    start = InternetArchiveItem.datetime(f"{day:%Y-%m-%d} 00:00:00")
    return InternetArchiveItem.objects.create(
        identifier=f"daily_perma_cc_{day:%Y-%m-%d}", span=DateTimeTZRange(start, start + timedelta(days=1)), complete=complete,
    )


def _reconcile(broker=None):
    emitted = []
    with (
        patch("perma.celery_tasks.redis.from_url", return_value=broker or fakeredis.FakeStrictRedis()),
        patch("perma.ia_metrics.logger") as metrics_logger,
    ):
        metrics_logger.info.side_effect = lambda message: emitted.append(json.loads(message))
        counts = reconcile_internet_archive_files.run()
    return counts, emitted


def _status(link):
    return InternetArchiveFile.objects.get(link_id=link.guid).status


@pytest.mark.django_db
@pytest.mark.parametrize("fields, status", [
    ({"is_private": True}, "deletion_needed"),
    ({"is_unlisted": True}, "deletion_needed"),
    ({"user_deleted": True}, "deletion_needed"),
    # not playable is not a reason to delete
    ({"cached_can_play_back": False}, "confirmed_present"),
    ({}, "confirmed_present"),
])
def test_withdrawn_links_files_at_ia_need_deletion(complete_link_factory, fields, status):
    link = complete_link_factory()
    _file_with_status(_daily_item(link), link, "confirmed_present")
    Link.objects.all_with_deleted().filter(pk=link.pk).update(**fields)

    _reconcile()

    assert _status(link) == status


@pytest.mark.django_db
def test_uneditable_items_are_left_alone(complete_link_factory):
    link = _link_on(complete_link_factory, datetime(2022, 7, 19).date(), is_private=True)
    item = _item_for(link.creation_timestamp.date())
    assert item.identifier in uneditable_daily_item_identifiers()
    _file_with_status(item, link, "confirmed_present")

    _reconcile()

    assert _status(link) == "confirmed_present"


@pytest.mark.django_db
@pytest.mark.parametrize("fields, status", [({}, "upload_needed"), ({"is_private": True}, "confirmed_absent")])
def test_public_links_deleted_from_ia_need_uploading_again(complete_link_factory, fields, status):
    link = complete_link_factory()
    _file_with_status(_daily_item(link), link, "confirmed_absent")
    Link.objects.filter(pk=link.pk).update(**fields)

    _reconcile()

    assert _status(link) == status


@pytest.mark.django_db
def test_links_that_flip_back_are_restored(complete_link_factory):
    to_keep, to_skip = complete_link_factory(), complete_link_factory()
    item = _daily_item(to_keep)
    _file_with_status(item, to_keep, "deletion_needed")
    _file_with_status(item, to_skip, "upload_needed")
    Link.objects.filter(pk=to_skip.pk).update(is_private=True)

    counts, _ = _reconcile()

    assert (_status(to_keep), _status(to_skip)) == ("confirmed_present", "confirmed_absent")
    assert (counts["deletion_cancelled"], counts["upload_cancelled"]) == (1, 1)


@pytest.mark.django_db
def test_links_without_ia_files_on_finished_days_need_uploading(complete_link_factory):
    # other links the test database may hold
    baseline, _ = _reconcile()
    today = datetime.now(tz.utc).date()
    current = complete_link_factory()
    _item_for(today)  # incomplete: the producer's backlog starts today
    on_complete_day = _link_on(complete_link_factory, datetime(2024, 3, 1).date())
    _item_for(on_complete_day.creation_timestamp.date(), complete=True)
    on_day_without_item = _link_on(complete_link_factory, datetime(2024, 3, 2).date())
    before_backlog = _link_on(complete_link_factory, datetime(2021, 6, 1).date())
    legacy = _link_on(complete_link_factory, datetime(2022, 3, 1).date())
    legacy_item = InternetArchiveItem.objects.create(identifier=f"perma_cc_{legacy.guid}")
    _file_with_status(legacy_item, legacy, "confirmed_present")
    uneditable = _link_on(complete_link_factory, datetime(2022, 7, 20).date())
    private = _link_on(complete_link_factory, datetime(2024, 3, 1).date(), is_private=True)

    counts, emitted = _reconcile()

    assert _status(on_complete_day) == "upload_needed"
    assert _status(on_day_without_item) == "upload_needed"
    assert InternetArchiveItem.objects.filter(identifier="daily_perma_cc_2024-03-02").exists()
    for link in (current, before_backlog, uneditable, private):
        assert not InternetArchiveFile.objects.filter(link_id=link.guid).exists()
    assert not InternetArchiveFile.objects.filter(link_id=legacy.guid, item__span__isempty=False).exists()
    keys = ("upload_needed_new", "left_to_producer", "pre_backlog", "legacy_only", "uneditable")
    assert {k: counts[k] - (baseline[k] if k != "upload_needed_new" else 0) for k in keys} == {
        "upload_needed_new": 2, "left_to_producer": 1, "pre_backlog": 1, "legacy_only": 1, "uneditable": 1,
    }
    [event] = emitted
    assert event["event"] == "reconcile" and event["upload_needed_new"] == 2 and "reconcile_ms" in event

    # a second run changes nothing
    counts, _ = _reconcile()
    assert counts["upload_needed_new"] == 0


@pytest.mark.django_db
def test_reconciliation_runs_one_at_a_time():
    broker = fakeredis.FakeStrictRedis()
    broker.set(IA_RECONCILE_LOCK, 1)

    assert _reconcile(broker)[0] is None
