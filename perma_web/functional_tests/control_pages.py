"""
The fixed set of pages, widths and roles shared by the screenshot capture tool and the accessibility gate.

Nothing here is named test_*: pytest would collect it wherever it is imported.
"""

from functional_tests.page_settling import settle_page

HEIGHT = 900
WIDTHS = [320, 375, 768, 990, 1200]

# slug -> (role, view name); "archive" is the WARC-backed playback page
PAGES = {
    "landing": ("anonymous", "landing"),
    "about": ("anonymous", "about"),
    "contact": ("anonymous", "contact"),
    "docs": ("anonymous", "docs"),
    "docs-faq": ("anonymous", "docs_faq"),
    "docs-registrars": ("anonymous", "docs_registrars"),
    "sign-up": ("anonymous", "sign_up"),
    "login": ("anonymous", "user_management_limited_login"),
    "create-link": ("user", "create_link"),
    "settings-profile": ("user", "settings_profile"),
    "settings-password": ("user", "settings_password"),
    "settings-tools": ("user", "settings_tools"),
    "settings-usage-plan": ("user", "settings_usage_plan"),
    "admin-stats": ("staff", "admin_stats"),
    "manage-organizations": ("staff", "user_management_manage_organization"),
    "manage-registrars": ("staff", "user_management_manage_registrar"),
    "manage-users": ("staff", "user_management_manage_user"),
    "manage-admin-users": ("staff", "user_management_manage_admin_user"),
    "archive-anonymous": ("anonymous", "archive"),
    "archive-logged-in": ("user", "archive"),
}


def open_control_page(page, request, slug, width):
    """
    Size the viewport, log in as the page's role, load the page and settle it.

    `urls` builds a stored WARC, which only the archive pages should pay for,
    so it is fetched through `request`. The calling test must still list
    `ui_urls`, `user`, `staff_user` and `log_in` among its own arguments:
    conftest decides from a test's declared fixtures whether it needs the live
    server and a flushed database, and a fixture fetched only through `request`
    doesn't count (the archive link would then be invisible to the server).
    The archive's replay frame is drawn after the page settles; callers that
    need it wait for it themselves.

    Args:
        page: The Playwright page to drive.
        request: The calling test's pytest `request`, used to fetch the archive fixtures lazily.
        slug: A key of `PAGES`.
        width: Viewport width in px; the height is `HEIGHT`.

    Raises:
        KeyError: `slug` is not in `PAGES`.
    """
    role, view_name = PAGES[slug]

    if view_name == "archive":
        target = request.getfixturevalue("urls").perma_link_with_warc
        log_in_as = request.getfixturevalue("log_in_user")
    else:
        target = request.getfixturevalue("ui_urls")(view_name)
        log_in_as = request.getfixturevalue("log_in")

    page.set_viewport_size({"width": width, "height": HEIGHT})
    if role == "user":
        log_in_as(page, request.getfixturevalue("user"))
    elif role == "staff":
        log_in_as(page, request.getfixturevalue("staff_user"))

    page.goto(target)
    settle_page(page)
