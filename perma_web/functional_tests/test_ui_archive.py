"""
Behavioral and visual contract for the archive playback page.

The archive page is styled by its own entry point (`style-responsive-archive.scss`
-> `single-link.css`) and imports a *different*, smaller Bootstrap subset than
the rest of the site. It is therefore the surface most likely to lose a rule
quietly when Bootstrap 3 is swapped out, and the one no other 4A file covers.

As everywhere in 4A, assertions target behavior and computed style, never
Bootstrap's own class names.
"""

import pytest
from playwright.sync_api import expect

DESKTOP_VIEWPORT = {"width": 1200, "height": 900}


def computed(page, selector, prop):
    """Read one resolved CSS property, which is what 'preserve appearance' means here."""
    return page.eval_on_selector(
        selector,
        "(el, prop) => getComputedStyle(el).getPropertyValue(prop)",
        prop,
    )


@pytest.mark.uses_storage
def test_details_tray_is_hidden_until_the_details_button_is_used(page, urls) -> None:
    """
    The record-details tray is a disclosure driven entirely by Perma's own JS.

    `single-link.module.js` sets `style.display` directly; it does not call
    Bootstrap's collapse plugin. The `collapse` class on #collapse-details is
    inert on this page -- the archive stylesheet compiles no bare `.collapse`
    rule at all, and `.ui-tray { display: none }` is what actually hides it.
    Bootstrap 5 introduces `.collapse:not(.show) { display: none }`, so this
    pins the behavior that must not shift when that rule starts existing.
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(urls.perma_link_with_warc)

    tray = page.locator("#collapse-details")
    view_mode = page.locator(".view-mode")
    button = page.locator("#details-button")

    expect(tray).to_be_hidden()
    expect(view_mode).to_be_visible()
    expect(button).to_have_text("Show record details")

    button.click()
    expect(tray).to_be_visible()
    expect(button).to_have_text("Hide record details")
    expect(view_mode).to_be_hidden()

    button.click()
    expect(tray).to_be_hidden()
    expect(button).to_have_text("Show record details")
    expect(view_mode).to_be_visible()


@pytest.mark.uses_storage
def test_details_tray_exposes_the_source_url_as_a_labeled_readonly_field(page, urls) -> None:
    """The one tray field a non-owner sees keeps its label association and its value."""
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(urls.perma_link_with_warc)
    page.locator("#details-button").click()

    source_url = page.get_by_label("Source page URL", exact=False)
    expect(source_url).to_be_visible()
    expect(source_url).to_have_value("http://example.com")
    expect(source_url).to_have_attribute("readonly", "")


@pytest.mark.uses_storage
def test_view_mode_toggle_marks_the_active_capture(page, urls) -> None:
    """
    Standard/Screenshot is a link pair whose selected state is carried by the
    `active` class -- one of the few Bootstrap 3 names Bootstrap 5 keeps.
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(urls.perma_link_with_warc)

    toggle = page.locator(".server-client-toggle")
    expect(toggle.get_by_role("link", name="Standard")).to_be_visible()
    expect(toggle.get_by_role("link", name="Screenshot")).to_be_visible()
    expect(toggle.locator("a.active")).to_have_count(1)
    expect(toggle.locator("a.active")).to_have_text("Standard")


@pytest.mark.uses_storage
def test_archive_header_and_playback_frame_are_present(page, urls) -> None:
    """The page's two structural halves: the Perma header band and the capture frame."""
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(urls.perma_link_with_warc)

    expect(page.get_by_role("banner")).to_have_count(1)
    expect(page.locator(".primary-segment")).to_be_visible()
    expect(page.locator(".archive-iframe")).to_have_count(1)
    expect(page.get_by_role("link", name="View the live page")).to_be_visible()


@pytest.mark.uses_storage
def test_archive_tray_keeps_its_own_visual_treatment(page, urls) -> None:
    """
    Computed-style contract for the archive-only chrome.

    These values come from `style-responsive-archive.scss`, not from Bootstrap,
    but they are rendered on top of the Bootstrap reset the archive entry point
    pulls in -- so a reboot change is exactly what would move them.
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(urls.perma_link_with_warc)
    page.locator("#details-button").click()

    assert computed(page, "#collapse-details", "background-color") == "rgb(255, 255, 255)"
    assert computed(page, "#collapse-details", "position") == "absolute"
    assert computed(page, "#collapse-details", "border-bottom-color") == "rgb(45, 118, 238)"
    assert computed(page, "#collapse-details", "z-index") == "100"


@pytest.mark.uses_storage
def test_archive_nav_toggle_is_currently_unlabeled_for_logged_in_users(page, urls, user, log_in_user) -> None:
    """
    Characterization, not endorsement: the archive page's nav toggle has no
    accessible name and no aria-expanded, unlike the one in base-responsive.html
    which has both.

    This is a pre-existing accessibility gap, recorded in the phase plan for
    separate remediation. It is pinned here so the Bootstrap 5 migration neither
    silently fixes it (an unrequested product change) nor silently worsens it.
    Deleting this test is the correct move once the gap is fixed deliberately.
    """
    page.set_viewport_size({"width": 375, "height": 800})
    log_in_user(page, user)
    page.goto(urls.perma_link_with_warc)

    # Matched by shape, not by Bootstrap's attribute name, which the migration renames.
    toggle = page.locator("header button.navbar-toggler")
    expect(toggle).to_have_count(1)
    assert toggle.get_attribute("aria-expanded") is None
    assert toggle.inner_text().strip() == ""
