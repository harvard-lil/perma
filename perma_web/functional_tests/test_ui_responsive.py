"""
Behavioral contract for Perma's responsive layout.

The declared support matrix for this phase is `perma_web/browserslist` plus
the breakpoints computed in `static/css/_vars-global.scss`: $width-mobile
(320px), $width-tablet (768px), $width-desktop (990px), and $width-wide /
$width-max (1200px). These are the *computed* pixel values, confirmed against
the SCSS source rather than its (partly stale) trailing comments -- see
`.plans/plan_bootstrap-4a-characterization-tests.md` for the discrepancy this
uncovered in $width-xmobile.

These assertions are written against Bootstrap 3 and must keep passing on
Bootstrap 5, so -- like `test_ui_navigation.py` -- they describe behavior and
geometry (visibility, bounding-box position, scroll width) and never assert a
Bootstrap class name. Real grid markup is located through Perma's own IDs and
classes, never through `.row`/`.col-*`/etc., so a selector never depends on
markup the migration is expected to change.

`test_ui_navigation.py` already covers the nav collapse contract at 375px
(collapsed) and 1200px (expanded); this file adds the *boundary* cases the
reference file deliberately left out, plus grid stacking, show/hide utility
classes, and a horizontal-scroll regression net across representative pages.
"""

import pytest
from playwright.sync_api import expect

JUST_BELOW_TABLET = {"width": 767, "height": 800}
AT_TABLET = {"width": 768, "height": 800}
JUST_BELOW_DESKTOP = {"width": 989, "height": 800}
AT_DESKTOP = {"width": 990, "height": 800}
JUST_BELOW_WIDE = {"width": 1199, "height": 900}
AT_WIDE = {"width": 1200, "height": 900}
MOBILE_MIN = {"width": 320, "height": 800}

# A column pair is "side by side" when their tops line up; browsers can differ
# by a pixel or two without the layout actually being different.
SAME_ROW_TOLERANCE = 4


@pytest.mark.uses_storage
def test_navbar_collapsed_just_below_tablet_breakpoint(page, ui_urls) -> None:
    """The nav stays collapsed one pixel below $width-tablet (768px)."""
    page.set_viewport_size(JUST_BELOW_TABLET)
    page.goto(ui_urls("landing"))

    expect(page.get_by_role("button", name="Toggle navigation")).to_be_visible()
    expect(page.locator("#upper_right_menu")).to_be_hidden()


@pytest.mark.uses_storage
def test_navbar_expanded_at_tablet_breakpoint(page, ui_urls) -> None:
    """The nav is already expanded exactly at $width-tablet (768px)."""
    page.set_viewport_size(AT_TABLET)
    page.goto(ui_urls("landing"))

    expect(page.get_by_role("button", name="Toggle navigation")).to_be_hidden()
    expect(page.locator("#upper_right_menu")).to_be_visible()


@pytest.mark.uses_storage
def test_hidemobile_element_hidden_just_below_tablet_breakpoint(page, ui_urls, user, log_in) -> None:
    """
    Perma's own `._hideMobile` utility (not a Bootstrap class) hides content
    below $width-tablet. Pinned on the settings-profile page heading.
    """
    # log_in waits on the account dropdown toggle, which the nav itself
    # collapses below the tablet breakpoint -- log in above it, then narrow
    # the viewport for the actual assertion.
    log_in(page, user)
    page.set_viewport_size(JUST_BELOW_TABLET)
    page.goto(ui_urls("settings_profile"))

    expect(page.get_by_role("heading", name="Profile")).to_be_hidden()


@pytest.mark.uses_storage
def test_hidemobile_element_visible_at_tablet_breakpoint(page, ui_urls, user, log_in) -> None:
    """The same `._hideMobile` heading is shown from $width-tablet up."""
    page.set_viewport_size(AT_TABLET)
    log_in(page, user)
    page.goto(ui_urls("settings_profile"))

    expect(page.get_by_role("heading", name="Profile")).to_be_visible()


@pytest.mark.uses_storage
def test_showdesktop_element_hidden_just_below_desktop_breakpoint(page, ui_urls) -> None:
    """
    Perma's own `._showDesktop` utility hides content below $width-desktop
    (990px). Pinned on the landing page's second intro paragraph.
    """
    page.set_viewport_size(JUST_BELOW_DESKTOP)
    page.goto(ui_urls("landing"))

    expect(page.get_by_text("Perma.cc is simple, easy to use")).to_be_hidden()


@pytest.mark.uses_storage
def test_showdesktop_element_visible_at_desktop_breakpoint(page, ui_urls) -> None:
    """The same `._showDesktop` paragraph is shown from $width-desktop up."""
    page.set_viewport_size(AT_DESKTOP)
    page.goto(ui_urls("landing"))

    expect(page.get_by_text("Perma.cc is simple, easy to use")).to_be_visible()


@pytest.mark.uses_storage
def test_landing_intro_columns_stack_below_tablet_breakpoint(page, ui_urls) -> None:
    """
    The landing page's intro row (heading+copy, then the illustration) stacks
    vertically below $width-tablet: the image sits well below the heading.
    """
    page.set_viewport_size(JUST_BELOW_TABLET)
    page.goto(ui_urls("landing"))

    heading_box = page.locator("h1.section-title").bounding_box()
    image_box = page.locator("img.primary-img").bounding_box()

    assert image_box["y"] - heading_box["y"] > 20, (
        "expected the illustration to be stacked well below the heading at a "
        "sub-tablet width"
    )


@pytest.mark.uses_storage
def test_landing_intro_columns_side_by_side_at_tablet_breakpoint(page, ui_urls) -> None:
    """The same two columns share a top edge from $width-tablet up."""
    page.set_viewport_size(AT_TABLET)
    page.goto(ui_urls("landing"))

    heading_box = page.locator("h1.section-title").bounding_box()
    image_box = page.locator("img.primary-img").bounding_box()

    assert abs(image_box["y"] - heading_box["y"]) <= SAME_ROW_TOLERANCE, (
        "expected the heading and illustration to sit in the same row at "
        "the tablet breakpoint"
    )


@pytest.mark.uses_storage
def test_footer_columns_stack_below_wide_breakpoint(page, ui_urls) -> None:
    """
    The footer's two navigation lists stack vertically below $width-wide
    (1200px): the "boilerplate" list sits well below the "footer-nav" list.
    """
    page.set_viewport_size(JUST_BELOW_WIDE)
    page.goto(ui_urls("landing"))

    footer_nav_box = page.locator("#footer-nav").bounding_box()
    boilerplate_box = page.locator("#boilerplate").bounding_box()

    assert boilerplate_box["y"] - footer_nav_box["y"] > 20, (
        "expected the boilerplate list to be stacked below the footer-nav "
        "list just below the wide breakpoint"
    )


@pytest.mark.uses_storage
def test_footer_columns_side_by_side_at_wide_breakpoint(page, ui_urls) -> None:
    """The same two footer lists share a top edge from $width-wide up."""
    page.set_viewport_size(AT_WIDE)
    page.goto(ui_urls("landing"))

    footer_nav_box = page.locator("#footer-nav").bounding_box()
    boilerplate_box = page.locator("#boilerplate").bounding_box()

    assert abs(boilerplate_box["y"] - footer_nav_box["y"]) <= SAME_ROW_TOLERANCE, (
        "expected the footer-nav and boilerplate lists to sit side by side "
        "at the wide breakpoint"
    )


REPRESENTATIVE_PAGES = ["landing", "about", "contact", "docs", "sign_up"]
SUPPORTED_WIDTHS = [320, 375, 768, 1200]


@pytest.mark.uses_storage
@pytest.mark.parametrize("view_name", REPRESENTATIVE_PAGES)
@pytest.mark.parametrize("width", SUPPORTED_WIDTHS)
def test_no_horizontal_scroll_at_supported_widths(page, ui_urls, view_name, width) -> None:
    """
    No representative page should ever scroll horizontally at a supported
    width -- a cheap, broad regression net for grid/gutter changes.
    """
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(ui_urls(view_name))

    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    inner_width = page.evaluate("window.innerWidth")

    assert scroll_width <= inner_width, (
        f"{view_name!r} scrolls horizontally at {width}px "
        f"(scrollWidth={scroll_width}, innerWidth={inner_width})"
    )


@pytest.mark.uses_storage
def test_no_horizontal_scroll_on_create_link_at_mobile_min(page, ui_urls, user, log_in) -> None:
    """
    The authenticated create-link page (richer, form-heavy markup than the
    public pages above) also must not scroll horizontally at the minimum
    supported width, $width-mobile (320px).
    """
    log_in(page, user)
    page.set_viewport_size(MOBILE_MIN)
    page.goto(ui_urls("create_link"))

    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    inner_width = page.evaluate("window.innerWidth")

    assert scroll_width <= inner_width, (
        f"create_link scrolls horizontally at 320px "
        f"(scrollWidth={scroll_width}, innerWidth={inner_width})"
    )
