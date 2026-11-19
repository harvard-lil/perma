"""
Browser tests of the `assert_snapshot` fixture, on pages built with `set_content`.

No live server is needed. Baselines live under tmp_path; none are committed.
"""

import io
import re
from pathlib import Path

from PIL import Image
import pytest

from functional_tests.image_diff import compare_images

PAGE = """
<style>
  body { margin: 0; background: #fff; }
  #box { position: absolute; left: 10px; top: 10px; width: 40px; height: 40px; background: #000; }
  #stamp { position: absolute; left: 100px; top: 10px; width: 20px; height: 20px; background: #0a0; }
</style>
<div id="box"></div>
<div id="stamp"></div>
"""
NAME = "page"


@pytest.fixture
def snapshot_dir(tmp_path):
    return tmp_path / "baselines"


@pytest.fixture
def update_snapshots():
    # A `--update-snapshots` run must not turn these comparisons into writes.
    return False


@pytest.fixture
def baseline_path(snapshot_dir, browser_name, request):
    """Where the fixture is documented to read this test's baseline."""
    return snapshot_dir / browser_name / Path(__file__).stem / request.node.originalname / f"{NAME}.png"


def _store_baseline(page, path, mask=()):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(page.screenshot(full_page=True, animations="disabled", mask=list(mask)))


@pytest.fixture
def stored_baseline(page, baseline_path):
    page.set_content(PAGE)
    _store_baseline(page, baseline_path)
    return baseline_path


def _expected_files(output_path):
    return {f"{NAME}-{kind}.png": Path(output_path, f"{NAME}-{kind}.png") for kind in ("expected", "actual", "diff")}


@pytest.mark.parametrize("update_snapshots", [True])
def test_update_flag_writes_the_baseline_and_passes(page, assert_snapshot, baseline_path, output_path):
    page.set_content(PAGE)

    assert_snapshot(page, NAME)

    assert baseline_path.is_file()
    with Image.open(baseline_path) as written, Image.open(io.BytesIO(page.screenshot(full_page=True))) as fresh:
        assert compare_images(written, fresh, 0).passed
    assert not Path(output_path).exists()


def test_unchanged_page_matches_its_baseline(page, assert_snapshot, stored_baseline, output_path):
    assert_snapshot(page, NAME)

    assert not Path(output_path).exists()


def test_one_pixel_css_change_fails_with_expected_actual_and_diff(page, assert_snapshot, stored_baseline, output_path):
    page.add_style_tag(content="#box { left: 11px; }")

    with pytest.raises(AssertionError) as failure:
        assert_snapshot(page, NAME)

    files = _expected_files(output_path)
    assert all(path.is_file() for path in files.values())
    message = str(failure.value)
    # One column leaves the box and one joins it: 2 x 40 pixels.
    assert re.search(r"80 pixels over tolerance \d+", message)
    assert "worst channel difference 255" in message
    assert "bounding box (10, 10, 51, 50)" in message
    assert "baseline size (1280, 720), actual size (1280, 720)" in message
    assert all(str(path) in message for path in files.values())
    with Image.open(files[f"{NAME}-diff.png"]) as diff:
        assert diff.getpixel((10, 20)) == (255, 0, 0)
    assert files[f"{NAME}-expected.png"].read_bytes() == stored_baseline.read_bytes()


def test_missing_baseline_fails_and_saves_the_actual(page, assert_snapshot, snapshot_dir, output_path):
    page.set_content(PAGE)

    with pytest.raises(AssertionError, match=r"No baseline at .*page\.png.*--update-snapshots") as failure:
        assert_snapshot(page, NAME)

    actual = Path(output_path, f"{NAME}-actual.png")
    assert actual.is_file()
    assert str(actual) in str(failure.value)
    assert not snapshot_dir.exists()


@pytest.mark.parametrize("update_snapshots", [True])
def test_update_flag_leaves_a_baseline_within_tolerance_untouched(page, assert_snapshot, stored_baseline, output_path):
    # An unchanged page re-shoots byte-identically, so nudge the stored PNG to tell "untouched" from "rewritten".
    with Image.open(stored_baseline) as image:
        image = image.convert("RGB")
        image.putpixel((20, 20), (2, 0, 0))
        image.save(stored_baseline)
    nudged = stored_baseline.read_bytes()

    assert_snapshot(page, NAME)

    assert stored_baseline.read_bytes() == nudged
    assert not Path(output_path).exists()


@pytest.mark.parametrize("update_snapshots", [True])
def test_update_flag_rewrites_a_baseline_that_fails(page, assert_snapshot, stored_baseline, output_path):
    original = stored_baseline.read_bytes()
    page.add_style_tag(content="#box { left: 11px; }")

    assert_snapshot(page, NAME)

    assert stored_baseline.read_bytes() != original
    with Image.open(stored_baseline) as written, Image.open(io.BytesIO(page.screenshot(full_page=True))) as fresh:
        assert compare_images(written, fresh, 0).passed
    assert not Path(output_path).exists()


def test_masked_region_is_ignored(page, assert_snapshot, baseline_path):
    page.set_content(PAGE)
    stamp = page.locator("#stamp")
    _store_baseline(page, baseline_path, mask=[stamp])
    _store_baseline(page, baseline_path.with_name("unmasked.png"))
    page.add_style_tag(content="#stamp { background: #a00; }")

    assert_snapshot(page, NAME, mask=[stamp])
    # Without the mask the same change is visible against the unmasked baseline.
    with pytest.raises(AssertionError, match="differs from"):
        assert_snapshot(page, "unmasked")
