from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command

from perma.tests.test_internet_archive_tasks import _daily_item, _file_with_status, _s3_details


def _session(files):
    ia_item = Mock(item_metadata={"files": files})
    ia_item.get_file.return_value.delete.return_value = SimpleNamespace(status_code=204, text="")
    session = Mock()
    session.get_item.return_value = ia_item
    session.get_s3_load_info.return_value = (False, _s3_details())
    return session, ia_item


def _run(session, *args):
    out = StringIO()
    with patch("perma.management.commands.remove_ia_derivative_leftovers.get_ia_session", return_value=session), \
            patch("perma.management.commands.remove_ia_derivative_leftovers.time.sleep"):
        call_command("remove_ia_derivative_leftovers", *args, stdout=out)
    return out.getvalue()


@pytest.fixture
def deleted_link(complete_link_factory):
    deleted, present = complete_link_factory(), complete_link_factory()
    item = _daily_item(deleted)
    _file_with_status(item, deleted, "confirmed_absent")
    _file_with_status(item, present, "confirmed_present")
    files = [
        {"name": f"{deleted.guid}.warc.os.cdx.gz"},
        {"name": f"{present.guid}.warc.gz"},
        {"name": f"{present.guid}.warc.os.cdx.gz"},
    ]
    return deleted, item, files


@pytest.mark.django_db
def test_a_dry_run_only_reports(deleted_link):
    deleted, item, files = deleted_link
    session, ia_item = _session(files)

    out = _run(session)

    assert f"Would delete {deleted.guid}.warc.os.cdx.gz from {item.identifier}." in out
    assert "1 leftover file(s) found" in out
    ia_item.get_file.assert_not_called()


@pytest.mark.django_db
def test_apply_deletes_only_leftovers_of_deleted_links(deleted_link):
    deleted, item, files = deleted_link
    session, ia_item = _session(files)

    out = _run(session, "--apply")

    ia_item.get_file.assert_called_once_with(f"{deleted.guid}.warc.os.cdx.gz")
    assert ia_item.get_file.return_value.delete.call_args.kwargs["cascade_delete"] is False
    assert f"Deleted {deleted.guid}.warc.os.cdx.gz from {item.identifier}." in out
    assert f"Resume with --after-item {item.identifier}." in out


@pytest.mark.django_db
def test_resuming_skips_items_already_done(deleted_link):
    deleted, item, files = deleted_link
    session, ia_item = _session(files)

    _run(session, "--apply", "--after-item", item.identifier)

    session.get_item.assert_not_called()
