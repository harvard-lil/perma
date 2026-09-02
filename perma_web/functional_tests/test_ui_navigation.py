"""
Behavioral contract for the site navigation chrome.

These assertions are written against Bootstrap 3 and must keep passing on
Bootstrap 5. They therefore describe *behavior and semantics* -- accessible
names, ARIA state, visibility, keyboard handling -- and never Bootstrap's own
class names, which the migration is expected to change.
"""

import pytest
from playwright.sync_api import expect

# Matches the phase's declared support matrix: the SCSS breakpoints in
# static/css/_vars-global.scss. Below $width-tablet the nav collapses.
MOBILE_VIEWPORT = {"width": 375, "height": 800}
DESKTOP_VIEWPORT = {"width": 1200, "height": 900}


@pytest.mark.uses_storage
def test_navbar_toggle_is_an_accessible_disclosure(page, ui_urls) -> None:
    """
    The small-screen nav toggle is a real button that reports its state.

    Bootstrap 5 renames the element (.navbar-toggle -> .navbar-toggler) and
    switches the attribute prefix to data-bs-*, so this pins the disclosure
    contract rather than the markup that implements it.
    """
    page.set_viewport_size(MOBILE_VIEWPORT)
    page.goto(ui_urls("landing"))

    toggle = page.get_by_role("button", name="Toggle navigation")
    expect(toggle).to_be_visible()
    expect(toggle).to_have_attribute("aria-expanded", "false")

    menu = page.locator("#upper_right_menu")
    expect(menu).to_be_hidden()

    toggle.click()
    expect(menu).to_be_visible()
    expect(toggle).to_have_attribute("aria-expanded", "true")

    toggle.click()
    expect(menu).to_be_hidden()
    expect(toggle).to_have_attribute("aria-expanded", "false")


@pytest.mark.uses_storage
def test_navbar_menu_is_open_and_toggle_hidden_on_desktop(page, ui_urls) -> None:
    """Above the tablet breakpoint the menu is always shown and the toggle is not."""
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(ui_urls("landing"))

    expect(page.locator("#upper_right_menu")).to_be_visible()
    expect(page.get_by_role("button", name="Toggle navigation")).to_be_hidden()


@pytest.mark.uses_storage
def test_logged_out_nav_offers_the_public_entry_points(page, ui_urls) -> None:
    """The anonymous menu links stay reachable by accessible name."""
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(ui_urls("landing"))

    menu = page.locator("#upper_right_menu")
    for name in ["About Perma.cc", "Guide", "Sign up", "Log in"]:
        expect(menu.get_by_role("link", name=name, exact=True)).to_be_visible()


@pytest.mark.uses_storage
def test_user_dropdown_opens_and_closes(page, ui_urls, user, log_in_user) -> None:
    """
    The account dropdown is a keyboard-operable disclosure.

    Bootstrap 5 drops the .open-on-parent pattern for .show-on-menu and
    requires the toggle to be adjacent to its menu, so the migration touches
    this markup. What must survive: click opens, Escape closes, and the state
    is reported through aria-expanded.
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    log_in_user(page, user)

    toggle = page.get_by_role("button", name="Main Dropdown")
    expect(toggle).to_have_attribute("aria-expanded", "false")

    logout = page.get_by_role("button", name="Log out")
    expect(logout).to_be_hidden()

    toggle.click()
    expect(logout).to_be_visible()
    expect(toggle).to_have_attribute("aria-expanded", "true")

    page.keyboard.press("Escape")
    expect(logout).to_be_hidden()
    expect(toggle).to_have_attribute("aria-expanded", "false")


@pytest.mark.uses_storage
def test_skip_links_precede_the_navigation(page, ui_urls) -> None:
    """
    Both skip links are the first things a keyboard user reaches, and each
    points at a target that exists on the page.
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(ui_urls("landing"))

    skip_links = page.locator("a.skip-link")
    expect(skip_links).to_have_count(2)

    page.keyboard.press("Tab")
    expect(skip_links.first).to_be_focused()

    for href in ["#main-skip-target", "#footer-skip-target"]:
        expect(page.locator(f"a.skip-link[href='{href}']")).to_have_count(1)
        assert page.locator(href).count() == 1


@pytest.mark.uses_storage
def test_page_exposes_one_banner_main_and_contentinfo(page, ui_urls) -> None:
    """
    Landmark structure is a Bootstrap-independent accessibility contract, and
    the migration rewrites the elements that carry these roles.
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(ui_urls("landing"))

    expect(page.get_by_role("banner")).to_have_count(1)
    expect(page.get_by_role("main")).to_have_count(1)
    expect(page.get_by_role("contentinfo")).to_have_count(1)
    expect(page.get_by_role("navigation", name="Main Menu")).to_have_count(1)
