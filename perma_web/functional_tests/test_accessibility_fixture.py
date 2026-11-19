"""
Browser tests of the `assert_a11y_baseline` fixture, on pages built with `set_content`.

No live server is needed. Baselines live under tmp_path; none are committed.
"""

import json
from pathlib import Path

import pytest
from axe_playwright_python.sync_playwright import Axe

from functional_tests import accessibility_baseline

# Fails button-name; the title and landmarks keep other rules quiet.
PAGE = """
<!doctype html><html lang="en"><head><title>Test page</title></head>
<body><main><h1>Heading</h1><p id="note">Some text</p><button id="empty"></button></main></body></html>
"""
NAME = "page"


@pytest.fixture
def a11y_baseline_dir(tmp_path):
    return tmp_path / "baselines"


@pytest.fixture
def update_a11y_baselines():
    # A `--update-a11y-baselines` run must not turn these comparisons into writes.
    return False


@pytest.fixture
def baseline_path(a11y_baseline_dir, browser_name, request):
    """Where the fixture is documented to read this test's baseline."""
    return a11y_baseline_dir / browser_name / Path(__file__).stem / request.node.originalname / f"{NAME}.json"


def _record(page, path):
    response = Axe().run(page).response
    accessibility_baseline.save_baseline(
        path, accessibility_baseline.axe_version(response), accessibility_baseline.violations_from_axe(response)
    )
    return path


@pytest.fixture
def stored_baseline(page, baseline_path):
    """Record PAGE's violations independently of the fixture under test."""
    page.set_content(PAGE)
    return _record(page, baseline_path)


def _rules(path):
    return {(v["rule"], tuple(v["target"])) for v in json.loads(path.read_text())["violations"]}


def _response_file(output_path):
    return Path(output_path, f"{NAME}-axe-response.json")


def test_the_page_has_the_expected_violation(page, stored_baseline):
    assert _rules(stored_baseline) == {("button-name", ("#empty",))}


@pytest.mark.parametrize("update_a11y_baselines", [True])
def test_update_flag_writes_the_baseline_and_passes(page, assert_a11y_baseline, baseline_path, output_path):
    page.set_content(PAGE)

    assert_a11y_baseline(page, NAME)

    assert _rules(baseline_path) == {("button-name", ("#empty",))}
    assert not Path(output_path).exists()


def test_missing_baseline_fails_and_saves_the_response(page, assert_a11y_baseline, a11y_baseline_dir, output_path):
    page.set_content(PAGE)

    with pytest.raises(AssertionError, match=r"No baseline at .*page\.json.*--update-a11y-baselines") as failure:
        assert_a11y_baseline(page, NAME)

    assert str(_response_file(output_path)) in str(failure.value)
    assert json.loads(_response_file(output_path).read_text())["testEngine"]["name"] == "axe-core"
    assert not a11y_baseline_dir.exists()


def test_unchanged_page_matches_its_baseline(page, assert_a11y_baseline, stored_baseline, output_path):
    assert_a11y_baseline(page, NAME)

    assert not Path(output_path).exists()


def test_new_violation_fails_and_is_listed_as_new(page, assert_a11y_baseline, stored_baseline, output_path):
    page.evaluate("document.querySelector('main').insertAdjacentHTML('beforeend', '<img id=\"pic\" src=\"x.png\">')")

    with pytest.raises(AssertionError) as failure:
        assert_a11y_baseline(page, NAME)

    message = str(failure.value)
    assert "New violations (1)" in message
    assert "image-alt" in message and '"#pic"' in message
    assert "Fixed violations" not in message
    assert str(stored_baseline) in message and "--update-a11y-baselines" in message
    saved = json.loads(_response_file(output_path).read_text())
    assert {rule["id"] for rule in saved["violations"]} == {"button-name", "image-alt"}


def test_fixed_violation_fails_and_is_listed_as_fixed(page, assert_a11y_baseline, stored_baseline, output_path):
    page.evaluate("document.querySelector('#empty').setAttribute('aria-label', 'Go')")

    with pytest.raises(AssertionError) as failure:
        assert_a11y_baseline(page, NAME)

    message = str(failure.value)
    assert "Fixed violations (1)" in message
    assert "button-name" in message and '"#empty"' in message
    assert "New violations" not in message
    assert _response_file(output_path).is_file()


def test_the_message_notes_a_different_axe_version(page, assert_a11y_baseline, stored_baseline):
    data = json.loads(stored_baseline.read_text())
    data["axe_version"] = "0.0.1"
    stored_baseline.write_text(json.dumps(data))
    page.evaluate("document.querySelector('#empty').setAttribute('aria-label', 'Go')")

    with pytest.raises(AssertionError, match=r"recorded with axe-core 0\.0\.1"):
        assert_a11y_baseline(page, NAME)


@pytest.mark.parametrize("update_a11y_baselines", [True])
def test_update_flag_leaves_a_matching_baseline_byte_identical(page, assert_a11y_baseline, stored_baseline, output_path):
    # Make the stored file differ in bytes but not in content, so a rewrite would show.
    data = json.loads(stored_baseline.read_text())
    data["axe_version"] = "0.0.1"
    stored_baseline.write_text(json.dumps(data, indent=4))
    before = stored_baseline.read_bytes()

    assert_a11y_baseline(page, NAME)

    assert stored_baseline.read_bytes() == before
    assert not Path(output_path).exists()


@pytest.mark.parametrize("update_a11y_baselines", [True])
def test_update_flag_rewrites_a_mismatching_baseline(page, assert_a11y_baseline, stored_baseline, output_path):
    before = stored_baseline.read_bytes()
    page.evaluate("document.querySelector('#empty').setAttribute('aria-label', 'Go')")

    assert_a11y_baseline(page, NAME)

    assert stored_baseline.read_bytes() != before
    assert _rules(stored_baseline) == set()
    assert not Path(output_path).exists()


def test_a_change_only_in_the_elements_html_passes(page, assert_a11y_baseline, stored_baseline, output_path):
    page.evaluate("document.querySelector('#empty').dataset.stamp = 'changed'")
    page.evaluate("document.querySelector('#note').textContent = 'Different text'")

    assert_a11y_baseline(page, NAME)

    assert not Path(output_path).exists()
