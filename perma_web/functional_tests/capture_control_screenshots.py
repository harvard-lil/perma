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

from functional_tests.control_pages import PAGES, WIDTHS, open_control_page


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
    open_control_page(page, request, slug, width)

    out = screenshot_dir / browser_name / f"{slug}@{width}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out), full_page=True)
