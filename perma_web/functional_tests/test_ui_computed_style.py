"""
Computed-style contract for Perma's current, Bootstrap-3-rendered appearance.

The Bootstrap 3 -> 5 migration's fidelity target is "preserve current
appearance" (see `.plans/plan_dependency-upgrade-roadmap-4.md`). Bootstrap 5
renames almost every class Perma's overrides target
(`static/css/_bootstrap-mod.scss`), so a test asserting a Bootstrap class name
would have to be rewritten during the migration and would prove nothing.
Instead, computed style read through `getComputedStyle` is the visual
contract: deterministic, reviewable in a diff, and blind to what the
underlying class is called.

Every element below is located through a Perma-owned id/class, an accessible
role/name, or visible text -- never a Bootstrap class -- so the *locator*
survives the migration as well as the assertion.

The exact values pinned here were traced through the SCSS cascade in
`_bootstrap-mod.scss` / `style-responsive.scss` and cross-checked against the
currently compiled `static/bundles/global.css`, not copied from
`_bootstrap-mod.scss` in isolation -- several of its stated values are
overridden by later, equal-specificity Perma rules and are not what actually
renders (e.g. generic `<input>` border/padding, and `.btn-info`'s
background-color, which loses to Perma's own `.btn` rule on every real
`.btn-info` element because they always carry `.btn` too). See
`.plans/plan_bootstrap-4a-characterization-tests.md` for the full trace.
"""

import pytest
from playwright.sync_api import expect

MOBILE_VIEWPORT = {"width": 375, "height": 800}
DESKTOP_VIEWPORT = {"width": 1200, "height": 900}


def computed_style(locator, property_name: str) -> str:
    """Read one CSS property from an element's computed style, as the browser serializes it."""
    return locator.evaluate(
        "(el, prop) => getComputedStyle(el).getPropertyValue(prop)", property_name
    )


@pytest.mark.uses_storage
def test_body_base_typography_and_background(page, ui_urls) -> None:
    """
    Base typography set in style-responsive.scss's "Defaults"/"Basics"
    sections, plus Bootstrap 3's unoverridden scaffolding font-size/
    line-height (14px / 1.428571429), must survive the migration unchanged.
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(ui_urls("landing"))

    body = page.locator("body")
    assert computed_style(body, "font-family") == '"Roboto Slab", sans-serif'
    assert computed_style(body, "font-size") == "14px"
    assert computed_style(body, "line-height") == "20px"
    assert computed_style(body, "color") == "rgb(34, 34, 34)"
    assert computed_style(body, "background-color") == "rgb(255, 255, 255)"


@pytest.mark.uses_storage
def test_body_text_link_color_states(page, ui_urls) -> None:
    """
    A link inside body copy: default color is inherited from the surrounding
    text (style-responsive.scss's `a:link{color:inherit}` deliberately wins
    over Bootstrap's own blue), hover shows Perma's blue ($color-blue), and
    focus shows the separate `_bootstrap-mod.scss` focus color (#06a) that
    the inherit override does not touch.
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(ui_urls("about"))

    # The about page has two "user guide" links in body copy; either exercises
    # the same rule, so pin the first.
    link = page.get_by_role("link", name="user guide").first
    expect(link).to_be_visible()

    assert computed_style(link, "color") == "rgb(34, 34, 34)"

    link.hover()
    assert computed_style(link, "color") == "rgb(45, 118, 238)"

    # Move the mouse off the link first: :hover lingers wherever the cursor
    # last landed, and a:hover's color would otherwise still win the tie
    # against a:focus once both pseudo-classes are active at once.
    page.mouse.move(0, 0)
    link.focus()
    # Characterization, not endorsement: _bootstrap-mod.scss sets a:focus to
    # #06a, but a later Perma rule restores $color-active for body-copy links,
    # so focus is visually indistinguishable from rest here. Pinned as-is --
    # giving focus its own color would be an accessibility improvement, and a
    # product change this phase has no mandate to make.
    assert computed_style(link, "color") == "rgb(34, 34, 34)"


@pytest.mark.uses_storage
def test_navbar_toggle_background_color(page, ui_urls) -> None:
    """
    The mobile nav toggle renders khaki, not the #09f _bootstrap-mod.scss sets.

    `style-responsive.scss` restyles `.navbar-toggle` twice (3329 and 3629) and,
    being later in the cascade at equal specificity, wins. The khaki is what
    Bootstrap 5 must preserve; the #09f in _bootstrap-mod.scss is dead.
    """
    page.set_viewport_size(MOBILE_VIEWPORT)
    page.goto(ui_urls("landing"))

    toggle = page.get_by_role("button", name="Toggle navigation")
    assert computed_style(toggle, "background-color") == "rgb(246, 248, 241)"


@pytest.mark.uses_storage
def test_select_control_border_padding_and_radius(page, ui_urls) -> None:
    """
    A plain <select> is untouched by any later Perma override, so it keeps
    _bootstrap-mod.scss's values verbatim: #ccc border, 6px/12px padding,
    4px corners.

    The org sign-up page is used because it is the only reachable page that
    renders a real <select>: every select in this codebase comes from a Django
    ChoiceField widget, and FirmUsageForm's is the plainest of them.
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(ui_urls("sign_up_orgs"))

    select = page.locator("#id_estimated_number_of_seats")
    assert computed_style(select, "border-top-color") == "rgb(204, 204, 204)"
    assert computed_style(select, "padding-top") == "6px"
    assert computed_style(select, "padding-left") == "12px"
    assert computed_style(select, "border-top-left-radius") == "4px"


@pytest.mark.uses_storage
def test_email_input_border_padding_and_radius(page, ui_urls) -> None:
    """
    A plain text-like <input> (the contact form's email field) is overridden
    by style-responsive.scss's own global `input{}` rule, which wins over
    _bootstrap-mod.scss's input override (equal specificity, declared later):
    border color rgba(0,0,0,.1) instead of #ccc, 8px padding instead of
    6px/12px. The 4px corner radius is unchanged (same value both places).
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(ui_urls("contact"))

    email_input = page.locator("#id_email")
    assert computed_style(email_input, "border-top-color") == "rgba(0, 0, 0, 0.1)"
    assert computed_style(email_input, "padding-top") == "8px"
    assert computed_style(email_input, "border-top-left-radius") == "4px"


@pytest.mark.uses_storage
def test_message_textarea_border_padding_and_radius(page, ui_urls) -> None:
    """
    A <textarea> (the contact form's message field) gets the same
    style-responsive.scss border-color override as <input>, but -- unlike
    <input> -- keeps _bootstrap-mod.scss's original 6px/12px padding, because
    no later rule touches textarea padding. This asymmetry is exactly the
    kind of drift a naive migration could flatten by accident.
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(ui_urls("contact"))

    message = page.locator("#id_box2")
    assert computed_style(message, "border-top-color") == "rgba(0, 0, 0, 0.1)"
    assert computed_style(message, "padding-top") == "6px"
    assert computed_style(message, "padding-left") == "12px"
    assert computed_style(message, "border-top-left-radius") == "4px"


@pytest.mark.uses_storage
def test_plain_button_box_model(page, ui_urls) -> None:
    """
    A plain `.btn`-only button (the contact form's "Send" button, no other
    Bootstrap contextual class) is styled entirely by Perma's own `.btn`
    rule in style-responsive.scss, not by _bootstrap-mod.scss's generic
    button override -- a class selector always outranks the bare element
    selector regardless of source order. Pinned at the tablet-and-up sizing
    branch (`@include respond-tablet`).
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(ui_urls("contact"))

    send_button = page.get_by_role("button", name="Send")
    assert computed_style(send_button, "border-top-left-radius") == "2px"
    assert computed_style(send_button, "padding-top") == "14px"
    assert computed_style(send_button, "padding-left") == "24px"
    assert computed_style(send_button, "font-size") == "16px"


@pytest.mark.uses_storage
def test_create_link_nav_button_shows_permas_blue(page, ui_urls, user, log_in) -> None:
    """
    The "Create and manage Perma Links" nav button carries both `.btn` and
    `.btn-info`. Perma's own `.btn{background-color:$color-blue}` rule
    (equal specificity, declared later in the compiled stylesheet) wins over
    _bootstrap-mod.scss's `.btn-info{background-color:#0099ff}` -- so the
    color actually on screen today is Perma's blue, not Bootstrap's. This is
    the value that must be preserved, not the raw _bootstrap-mod.scss value.
    """
    log_in(page, user)
    page.set_viewport_size(DESKTOP_VIEWPORT)
    # Not the landing page: it redirects an authenticated user to create_link,
    # where upper_right_menu.html suppresses this very button.
    page.goto(ui_urls("about"))

    # Scoped to the nav's own wrapper class (Perma's, not Bootstrap's) because
    # the same link text also exists, hidden, inside the account dropdown.
    create_button = page.locator("li.navbar-create-button").get_by_role(
        "link", name="Create and manage Perma Links"
    )
    assert computed_style(create_button, "background-color") == "rgb(45, 118, 238)"


@pytest.mark.uses_storage
def test_modal_z_index_and_body_padding(page, ui_urls, user, log_in) -> None:
    """
    The upload-your-own-file modal's z-index and body padding are explicit
    _bootstrap-mod.scss overrides of Bootstrap's defaults (1040 and 15px).
    """
    log_in(page, user)
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(ui_urls("create_link"))

    modal = page.locator("#archive-upload")
    assert computed_style(modal, "z-index") == "104000"

    # The modal-body div is identified by its child form's id, not by
    # Bootstrap's own ".modal-body" class name.
    modal_body = page.locator("div:has(> #archive_upload_form)")
    assert computed_style(modal_body, "padding-top") == "0px"
    assert computed_style(modal_body, "padding-right") == "15px"
