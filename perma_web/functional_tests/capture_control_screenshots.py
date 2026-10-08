"""
Capture a fixed set of full-page screenshots: ~20 pages x 5 viewport widths.

Used to take the "before" half of before/after visual pairs (Bootstrap 3 control)
and, unchanged, the "after" half once Bootstrap 5 is merged back in.

Run explicitly, once per engine, with an output directory:

    PERMA_CONTROL_SCREENSHOT_DIR=/perma/perma_web/control_shots \\
        pytest functional_tests/capture_control_screenshots.py --browser firefox

PNGs land at <dir>/<browser>/<page-slug>@<width>.png.

This is deliberately not named test_*.py: the suite's `python_files` patterns
(tests.py, test_*.py, *_tests.py) skip it, so normal pytest runs never collect
it. It only runs when the file is passed on the command line.
"""

import os
from pathlib import Path

import pytest

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


@pytest.fixture(scope="session")
def screenshot_dir():
    # Fail loudly: a silent default would scatter PNGs somewhere unexpected.
    value = os.environ.get("PERMA_CONTROL_SCREENSHOT_DIR")
    if not value:
        pytest.fail("Set PERMA_CONTROL_SCREENSHOT_DIR to the output directory.")
    return Path(value)


@pytest.mark.uses_storage
@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("slug", PAGES)
def test_capture(page, request, browser_name, screenshot_dir, slug, width, ui_urls, user, staff_user, log_in):
    role, view_name = PAGES[slug]

    # `urls` builds a stored WARC, so only the archive pages pay for it.
    if view_name == "archive":
        urls = request.getfixturevalue("urls")
        target = urls.perma_link_with_warc
        log_in_as = request.getfixturevalue("log_in_user")
    else:
        target = ui_urls(view_name)
        log_in_as = log_in

    page.set_viewport_size({"width": width, "height": HEIGHT})
    if role == "user":
        log_in_as(page, user)
    elif role == "staff":
        log_in(page, staff_user)

    page.goto(target)
    settle_page(page)

    out = screenshot_dir / browser_name / f"{slug}@{width}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out), full_page=True)
