"""
Accessibility gate: axe-core violations of the control pages must match their stored baselines.

One case per page and width, in each engine. Baselines are recorded with
`--update-a11y-baselines`; see developer.md, "Accessibility baselines".
The page sweep is marked `sweep`, so it runs only with `--all` or an update flag.
"""

import os

import pytest
from django.conf import settings
from django.core.files.storage import storages
from django.utils import timezone
from playwright.sync_api import expect

from functional_tests.control_pages import PAGES, WIDTHS, open_control_page

# Fixed so the archive pages' selectors (a[href="/<GUID>?type=image"]) are the same on every run.
ARCHIVE_GUID = "7R2K-9M4X"


def _warc_link(complete_link_factory, **link_kwargs):
    link = complete_link_factory({
        "submitted_url": "http://example.com",
        "submitted_title": "Example Domain",
        **link_kwargs,
    })
    with open(os.path.join(settings.PROJECT_ROOT, "perma/tests/assets/new_style_archive/archive.warc.gz"), "rb") as warc_file:
        storages[settings.WARC_STORAGE].store_file(warc_file, link.warc_storage_file(), overwrite=True)
        link.warc_size = warc_file.tell()
        link.save()
    return link


def _with_guid(complete_link_factory, guid):
    # Presetting the guid sets the pk, which makes Link.save() skip its whole `if not self.pk` block,
    # including the archive_timestamp default, so set that here.
    created = timezone.now()
    return _warc_link(
        complete_link_factory,
        guid=guid,
        creation_timestamp=created,
        archive_timestamp=created + settings.ARCHIVE_DELAY,
    )


@pytest.fixture
def complete_link_with_warc(complete_link_factory):
    """Overrides conftest's fixture, which `urls` uses, so the archive pages have a fixed GUID."""
    return _with_guid(complete_link_factory, ARCHIVE_GUID)


def _wait_for_replay(page):
    # The replay frame is drawn after the page settles, and axe scans the top frame only.
    expect(page.frame_locator(".archive-iframe").frame_locator("iframe").frame_locator("iframe")
           .locator("h1")).to_contain_text("Example Domain", timeout=120_000)


@pytest.mark.sweep
@pytest.mark.uses_storage
@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("slug", PAGES)
def test_accessibility_violations_match_the_baseline(
    page, request, assert_a11y_baseline, slug, width, ui_urls, user, staff_user, log_in
):
    open_control_page(page, request, slug, width)
    if PAGES[slug][1] == "archive":
        _wait_for_replay(page)

    assert_a11y_baseline(page, f"{slug}@{width}")


@pytest.mark.uses_storage
def test_fixed_guid_link_matches_one_with_a_generated_guid(complete_link_factory):
    fixed = _with_guid(complete_link_factory, "8R3K-4M7X")
    normal = _warc_link(complete_link_factory)

    assert fixed.guid == "8R3K-4M7X" and normal.guid != fixed.guid
    assert fixed.archive_timestamp - fixed.creation_timestamp == settings.ARCHIVE_DELAY
    assert normal.archive_timestamp - normal.creation_timestamp == settings.ARCHIVE_DELAY
    # The creator is a fresh user per link, and guid and timestamps are the point of the test.
    skipped = {"guid", "creation_timestamp", "archive_timestamp", "created_by"}
    for field in (f for f in fixed._meta.concrete_fields if f.name not in skipped):
        assert getattr(fixed, field.attname) == getattr(normal, field.attname), field.name
    assert fixed.folders.count() == normal.folders.count() == 1
    assert fixed.capture_job.status == normal.capture_job.status
    assert sorted(fixed.captures.values_list("role", "status")) == sorted(normal.captures.values_list("role", "status"))
