"""
Behavioral contract for tabs, modals/dialogs, collapse panels, pagination,
and tables.

These assertions are written against Bootstrap 3 and must keep passing on
Bootstrap 5. They describe *behavior and semantics* -- visibility, ARIA
state, accessible name/role, landmark structure -- and never Bootstrap's own
class names (`.nav-tabs`, `.tab-pane.active`, `.collapse`, `.pagination`,
`.active`/`.disabled`, `.sr-only`, `data-toggle`, `data-dismiss`, `.close`),
all of which the Bootstrap 5 migration is expected to rename or restructure.

Two components named in the assignment turned out to be unreachable through
any live page and are deliberately not covered here (see the final report
rather than this docstring for the full explanation):

- `perma/templates/errors/view.html` is not wired to any URL in
  `perma/urls.py` -- the route that used to render it was removed years ago
  and the template was left behind as dead code.
- `perma/templates/archive/includes/upload_your_own.html` and
  `link_batch_modal.html` are `{% include %}`d into `create-link.html` but
  have no `data-target`/`.modal()` trigger anywhere; the real, reachable
  modals on that page are the Vue components `UploadForm.vue` and
  `CreateLinkBatch.vue` (each wrapping a shared `Dialog.vue` built on the
  native `<dialog>` element), which this file tests instead.
"""

import pytest
from playwright.sync_api import expect

# Matches the phase's declared support matrix: the SCSS breakpoints in
# static/css/_vars-global.scss.
MOBILE_VIEWPORT = {"width": 375, "height": 800}
DESKTOP_VIEWPORT = {"width": 1200, "height": 900}

ADMIN_STATS_TABS = [
    ("Celery Queues", "#celery_data"),
    ("Internet Archive", "#rate-limits-pane"),
    ("Capture Jobs", "#capture-job-pane"),
    ("Capture Errors", "#capture-error-pane"),
    ("This Month's Links", "#days-pane"),
    ("Random", "#random-pane"),
    ("Users by Domain", "#emails-pane"),
]


# --- Tabs (admin-stats.html) ------------------------------------------------
#
# Panes are populated over the network (some hit Celery/Redis directly from
# the view), so these tests assert pane visibility/identity only -- never
# loaded content -- to stay independent of whether Celery is up.

@pytest.mark.uses_storage
def test_admin_stats_tabs_show_exactly_one_pane_at_a_time(page, ui_urls, staff_user, log_in) -> None:
    """
    The first tab's pane is visible on load; clicking any other tab (by its
    visible text) shows that tab's pane and hides every other one, so
    exactly one pane is ever visible. Bootstrap 5 replaces `.nav-tabs > li`/
    `.tab-pane.active` with a different structure, so this pins the
    disclosure contract rather than the classes that implement it.
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    log_in(page, staff_user)
    page.goto(ui_urls("admin_stats"))

    panes = {pane_id: page.locator(pane_id) for _, pane_id in ADMIN_STATS_TABS}

    expect(panes["#celery_data"]).to_be_visible()
    for pane_id, locator in panes.items():
        if pane_id != "#celery_data":
            expect(locator).to_be_hidden()

    # Role is "tab", not "link": Bootstrap 5's Tab plugin assigns role="tab" to
    # each toggle at runtime, so the accessible role changes even though the
    # template still renders a plain <a href>. That is upstream behaviour, not a
    # markup choice -- see the Phase 4 plan's note on this being the one existing
    # assertion the migration required changing.
    for name, pane_id in ADMIN_STATS_TABS:
        page.get_by_role("tab", name=name, exact=True).click()
        expect(panes[pane_id]).to_be_visible()
        for other_id, other_locator in panes.items():
            if other_id != pane_id:
                expect(other_locator).to_be_hidden()


# --- Collapse panels ("add" disclosures) ------------------------------------

COLLAPSE_DISCLOSURE_PAGES = [
    ("user_management_manage_registrar", "add registrar"),
    ("user_management_manage_user", "add user"),
    ("user_management_manage_organization", "add organization"),
]


@pytest.mark.uses_storage
@pytest.mark.parametrize("view_name, toggle_name", COLLAPSE_DISCLOSURE_PAGES)
def test_add_disclosure_toggles_open_and_closed(page, ui_urls, staff_user, log_in, view_name, toggle_name) -> None:
    """
    The "add" control is a disclosure: its panel is hidden on load, a click
    reveals it and flips `aria-expanded`, and a second click hides it again.
    Bootstrap 5 renames `data-toggle` to `data-bs-toggle`, so this pins the
    disclosure's visible behavior, not the attribute that wires it up.
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    log_in(page, staff_user)
    page.goto(ui_urls(view_name))

    toggle = page.get_by_role("link", name=toggle_name, exact=True)
    panel = page.locator("#add-member")

    expect(panel).to_be_hidden()
    expect(toggle).to_have_attribute("aria-expanded", "false")

    toggle.click()
    expect(panel).to_be_visible()
    expect(toggle).to_have_attribute("aria-expanded", "true")

    toggle.click()
    expect(panel).to_be_hidden()
    expect(toggle).to_have_attribute("aria-expanded", "false")


# --- Modals / dialogs (create_link page) ------------------------------------
#
# The Django-template modals named in the assignment are dead markup (no
# trigger anywhere reaches them -- see module docstring). The real, reachable
# dialogs on the same page are these two Vue components, both built on a
# native <dialog> element rather than Bootstrap's JS plugin.

@pytest.mark.uses_storage
def test_link_batch_dialog_opens_dismisses_and_escapes(page, ui_urls, user, log_in) -> None:
    """
    The "create multiple links" control opens a real dialog; its close
    control and Escape both dismiss it. The dialog itself currently has no
    accessible name (no aria-label/aria-labelledby/title), so that is not
    asserted here -- see the report for that finding.
    """
    log_in(page, user)

    trigger = page.get_by_role("button", name="create multiple links")
    dialog = page.get_by_role("dialog")

    expect(dialog).to_be_hidden()
    trigger.click()
    expect(dialog).to_be_visible()

    dialog.get_by_role("button", name="Close", exact=True).click()
    expect(dialog).to_be_hidden()

    trigger.click()
    expect(dialog).to_be_visible()
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()


@pytest.mark.uses_storage
def test_upload_your_own_dialog_opens_dismisses_and_escapes(page, ui_urls, user, log_in) -> None:
    """
    The upload dialog is only reachable after a genuine capture failure.
    Reuses the exact request (a domain that cannot resolve) that
    `test_links.py::test_upload_nonexistent` already relies on, so this stays
    a real failure rather than a mocked one, without depending on Celery.
    """
    log_in(page, user)

    url_field = page.locator("#rawUrl")
    url_field.focus()
    url_field.type("https://fakedomain.fakething/")
    page.locator("#addlink").click()
    expect(page.locator("#error-container")).to_contain_text("Couldn't resolve domain.")

    trigger = page.get_by_role("button", name="upload your own archive")
    trigger.click()

    dialog = page.get_by_role("dialog").filter(has_text="Upload a file to Perma.cc")
    expect(dialog).to_be_visible()

    dialog.get_by_role("button", name="Close", exact=True).click()
    expect(dialog).to_be_hidden()

    trigger.click()
    expect(dialog).to_be_visible()
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()


# --- Pagination (user_management/includes/paginator.html) ------------------

@pytest.mark.uses_storage
def test_registrar_pagination_moves_the_listing(page, ui_urls, staff_user, log_in, registrar_factory) -> None:
    """
    The pager lives in a named navigation landmark; the current page is
    marked in a way assistive tech can read (not just a CSS `.active` class);
    and Previous/Next move the listing and flip their own reachability.
    Fixture data alone yields only one page (nav omitted entirely below
    `page.has_other_pages`), so this creates enough registrars to force a
    second page -- otherwise the navigational contract can't be exercised at
    all. Page sizes are asserted precisely (50 then 14) rather than by
    comparing item sets across the two requests, since the default sort
    ('name') has no unique tiebreaker and two Faker-generated names could
    theoretically collide.
    """
    registrar_count = 4 + 60  # existing fixture registrars + newly-created ones
    registrar_factory.create_batch(60)  # pushes the total past MAX_USER_LIST_SIZE (50)
    second_page_size = registrar_count - 50

    page.set_viewport_size(DESKTOP_VIEWPORT)
    log_in(page, staff_user)
    page.goto(ui_urls("user_management_manage_registrar"))

    nav = page.get_by_role("navigation", name="Registrar List pagination")
    expect(nav).to_be_visible()
    expect(page.locator(".item-title")).to_have_count(50)

    # On page 1: Previous is not a link (disabled state renders as plain text).
    expect(nav.get_by_role("link", name="Previous")).to_have_count(0)
    next_link = nav.get_by_role("link", name="Next")
    expect(next_link).to_be_visible()
    expect(nav.get_by_text("(current page)")).to_have_count(1)

    next_link.click()

    # A different, smaller page proves Next actually moved the listing.
    expect(page.locator(".item-title")).to_have_count(second_page_size)

    # On page 2: Previous is now reachable; the current-page marker persists.
    expect(nav.get_by_role("link", name="Previous")).to_be_visible()
    expect(nav.get_by_text("(current page)")).to_have_count(1)


# --- Tables ------------------------------------------------------------------

@pytest.mark.uses_storage
def test_admin_stats_days_table_exposes_table_semantics(page, ui_urls, staff_user, log_in) -> None:
    """
    The "This Month's Links" pane's table exposes a table role with
    columnheader cells, and stays reachable (scrollable into view) at a
    narrow viewport. Uses the one admin-stats pane backed only by the
    database, so this doesn't depend on Celery being up. Bootstrap 5 changes
    `.table-responsive`'s behavior, so reachability is asserted directly
    rather than via that class.
    """
    page.set_viewport_size(MOBILE_VIEWPORT)
    log_in(page, staff_user)
    page.goto(ui_urls("admin_stats"))

    page.get_by_role("tab", name="This Month's Links", exact=True).click()

    table = page.locator("#days").get_by_role("table")
    expect(table).to_be_visible()

    headers = table.get_by_role("columnheader")
    expect(headers).to_have_count(8)
    expect(headers.nth(0)).to_contain_text("Days")
    expect(headers.nth(1)).to_have_text("Count")
    expect(headers.nth(2)).to_have_text("Success")

    last_header = headers.last
    expect(last_header).to_have_text("Top Users")
    last_header.scroll_into_view_if_needed()
    expect(last_header).to_be_in_viewport()


@pytest.mark.uses_storage
def test_opening_a_disclosure_focuses_its_first_text_input(page, ui_urls, staff_user, log_in) -> None:
    """
    Revealing an "add" panel moves focus into its first text input.

    This is wired to Bootstrap's `shown.bs.collapse` event in global.js, and it
    is the one piece of collapse behavior that survives a framework swap only if
    the listener is rewritten: Bootstrap 3 fired the event through jQuery, where
    'shown.bs.collapse' parses as event 'shown' plus namespaces; Bootstrap 5
    dispatches a native event actually named 'shown.bs.collapse'. Nothing else
    in the suite would notice the handler going silent.
    """
    page.set_viewport_size(DESKTOP_VIEWPORT)
    log_in(page, staff_user)
    page.goto(ui_urls("user_management_manage_registrar"))

    page.get_by_role("link", name="add registrar", exact=True).click()

    panel = page.locator("#add-member")
    expect(panel).to_be_visible()
    expect(panel.locator('input[type="text"]').first).to_be_focused()
