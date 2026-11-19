"""Tests for the baselines invoke tasks: a temporary tree and a fake fetcher, no network or database."""

import hashlib
import io
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from invoke import Exit, MockContext
from PIL import Image

from functional_tests import baseline_sets
from functional_tests.baseline_sets import Pointer, SetNotFoundError, format_pointer, read_pointer, read_stamp, set_not_found_message
from tasks import baselines, ns

COMMITTED = "2026-10-28-bootstrap3"
CANDIDATE = "2026-11-02-candidate"
MISSING = "2026-11-03-nope"


def _tar(files):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def _png(color):
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color).save(buffer, format="PNG")
    return buffer.getvalue()


# Real PNGs, since the report decodes the ones that differ. Between the two sets the
# Chromium page changes, the Firefox page is the same and the WebKit page is added.
SETS = {
    COMMITTED: _tar({"chromium/t/f/page.png": _png((200, 0, 0)), "firefox/t/f/page.png": _png((100, 100, 100))}),
    CANDIDATE: _tar({
        "chromium/t/f/page.png": _png((0, 0, 200)),
        "firefox/t/f/page.png": _png((100, 100, 100)),
        "webkit/t/f/page.png": _png((0, 200, 0)),
    }),
}


def _pointer(name):
    return Pointer(name, hashlib.sha256(SETS[name]).hexdigest())


def _url(name):
    return f"{baseline_sets.DEFAULT_BASE_URL}baselines-{name}/baselines-{name}.tar"


@dataclass
class FakeFetch:
    """Serves SETS by URL and answers anything else as GitHub does for a missing release, with a 404."""

    urls: list = field(default_factory=list)

    def __call__(self, url):
        self.urls.append(url)
        for name, data in SETS.items():
            if url == _url(name):
                return data
        raise SetNotFoundError(f"baselines: {url} answered HTTP 404")


@dataclass
class Tree:
    pointer_path: Path
    baselines_dir: Path
    fetch: FakeFetch
    report_dir: Path
    temp_dir: Path

    def commit(self, name):
        self.pointer_path.write_text(format_pointer(_pointer(name)))


@pytest.fixture(autouse=True)
def no_network_and_clean_env(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("task tests must not open URLs")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    monkeypatch.delenv(baseline_sets.FETCH_ENV, raising=False)
    monkeypatch.delenv(baseline_sets.URL_ENV, raising=False)


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """
    Aims the tasks at tmp_path/perma_web, served by a FakeFetch; the real file lock is used.

    Temporary directories go to tmp_path/tmp, so a test can see that none is left behind.
    """
    perma_web = tmp_path / "perma_web"
    root = perma_web / "functional_tests"
    root.mkdir(parents=True)
    temp_dir = tmp_path / "tmp"
    temp_dir.mkdir()
    built = Tree(
        root / "BASELINE_SET", root / "baselines", FakeFetch(), perma_web / "failed_test_files" / "baseline-report", temp_dir
    )
    monkeypatch.setattr(baselines, "PERMA_WEB", perma_web)
    monkeypatch.setattr(baselines, "POINTER_PATH", built.pointer_path)
    monkeypatch.setattr(baselines, "BASELINES_DIR", built.baselines_dir)
    monkeypatch.setattr(baselines, "REPORT_DIR", built.report_dir)
    monkeypatch.setattr(baselines, "fetch_bytes", built.fetch)
    monkeypatch.setattr(tempfile, "tempdir", str(temp_dir))
    return built


def _lines(capsys):
    return capsys.readouterr().out.splitlines()


def test_the_collection_holds_exactly_fetch_adopt_and_report():
    assert set(ns.collections["baselines"].tasks) == {"fetch", "adopt", "report"}


# fetch


def test_fetch_without_a_pointer_reports_legacy_mode(tree, capsys):
    baselines.fetch(MockContext())

    assert _lines(capsys) == [
        "baselines: legacy mode: there is no functional_tests/BASELINE_SET, so functional_tests/baselines is used as it is"
    ]
    assert tree.fetch.urls == []


def test_fetch_reports_a_disabled_fetch_and_why(tree, capsys, monkeypatch):
    monkeypatch.setenv(baseline_sets.FETCH_ENV, "no")
    tree.commit(COMMITTED)

    baselines.fetch(MockContext())

    assert _lines(capsys) == [
        "baselines: fetching is off (PERMA_BASELINES_FETCH=no); functional_tests/baselines is used as it is"
    ]
    assert tree.fetch.urls == []


def test_fetch_downloads_the_committed_set_then_reports_it_current(tree, capsys):
    tree.commit(COMMITTED)

    baselines.fetch(MockContext())
    baselines.fetch(MockContext())

    fetched, current = _lines(capsys)
    assert fetched.startswith(f"baselines: fetched set {COMMITTED} (2 files, ")
    assert fetched.endswith(" into functional_tests/baselines")
    assert current == f"baselines: set {COMMITTED} is current in functional_tests/baselines; nothing downloaded"
    assert tree.fetch.urls == [_url(COMMITTED)]


def test_fetch_force_downloads_again_and_keeps_the_previous_copy(tree, capsys):
    tree.commit(COMMITTED)
    baselines.fetch(MockContext())
    capsys.readouterr()

    baselines.fetch(MockContext(), force=True)

    [fetched] = _lines(capsys)
    assert fetched.startswith(f"baselines: fetched set {COMMITTED} (2 files, ")
    assert fetched.endswith("; previous copy kept at baselines.prev")
    assert tree.fetch.urls == [_url(COMMITTED)] * 2


def test_fetch_name_previews_a_candidate_and_warns_it_is_temporary(tree, capsys):
    tree.commit(COMMITTED)
    baselines.fetch(MockContext())
    capsys.readouterr()

    baselines.fetch(MockContext(), name=CANDIDATE)

    fetched, warning = _lines(capsys)
    assert fetched.startswith(f"baselines: fetched set {CANDIDATE} (3 files, ")
    assert fetched.endswith("; previous copy kept at baselines.prev")
    assert warning == (
        f"baselines: this is a preview; the next pytest run swaps set {COMMITTED} back in "
        f"unless you adopt this one with `d invoke baselines.adopt {CANDIDATE}`"
    )
    assert read_stamp(tree.baselines_dir) == _pointer(CANDIDATE)
    assert read_pointer(tree.pointer_path) == _pointer(COMMITTED)


def test_fetch_name_without_a_pointer_says_pytest_keeps_the_copy(tree, capsys):
    baselines.fetch(MockContext(), name=CANDIDATE)

    assert _lines(capsys)[1] == (
        "baselines: there is no functional_tests/BASELINE_SET, so pytest uses this copy as it is until a set is adopted"
    )
    assert not tree.pointer_path.exists()


def test_fetch_name_skips_a_set_the_working_copy_already_holds(tree, capsys):
    tree.commit(COMMITTED)
    baselines.fetch(MockContext(), name=CANDIDATE)
    capsys.readouterr()

    baselines.fetch(MockContext(), name=CANDIDATE)

    present, warning = _lines(capsys)
    assert present == (
        f"baselines: set {CANDIDATE} is already in functional_tests/baselines; "
        "nothing downloaded (pass --force to download it again)"
    )
    assert warning.startswith(f"baselines: this is a preview; the next pytest run swaps set {COMMITTED} back in")
    assert tree.fetch.urls == [_url(CANDIDATE)]
    assert not tree.baselines_dir.with_name("baselines.prev").exists()


def test_fetch_name_with_force_downloads_it_again(tree, capsys):
    baselines.fetch(MockContext(), name=CANDIDATE)
    capsys.readouterr()

    baselines.fetch(MockContext(), name=CANDIDATE, force=True)

    fetched = _lines(capsys)[0]
    assert fetched.startswith(f"baselines: fetched set {CANDIDATE} (3 files, ")
    assert fetched.endswith("; previous copy kept at baselines.prev")
    assert tree.fetch.urls == [_url(CANDIDATE)] * 2
    assert read_stamp(tree.baselines_dir.with_name("baselines.prev")) == _pointer(CANDIDATE)


def test_fetch_name_of_a_missing_set_exits_non_zero_with_the_message(tree, capsys):
    with pytest.raises(Exit) as failure:
        baselines.fetch(MockContext(), name=MISSING)

    assert failure.value.code == 1
    assert failure.value.message == set_not_found_message(MISSING, _url(MISSING))
    assert capsys.readouterr().out == ""
    assert not tree.baselines_dir.exists()


def test_fetch_hash_mismatch_exits_non_zero_naming_adopt(tree, capsys):
    tree.pointer_path.write_text(format_pointer(Pointer(COMMITTED, "a" * 64)))

    with pytest.raises(Exit) as failure:
        baselines.fetch(MockContext())

    assert failure.value.code == 1
    assert f"`d invoke baselines.adopt {COMMITTED}`" in failure.value.message
    assert capsys.readouterr().out == ""


# adopt


def test_adopt_after_a_preview_writes_the_pointer_and_counts_the_changes(tree, capsys):
    tree.commit(COMMITTED)
    baselines.fetch(MockContext())
    baselines.fetch(MockContext(), name=CANDIDATE)
    capsys.readouterr()

    baselines.adopt(MockContext(), CANDIDATE)

    pointer = _pointer(CANDIDATE)
    assert _lines(capsys) == [
        "baselines: wrote functional_tests/BASELINE_SET:",
        f"set={CANDIDATE}",
        f"sha256={pointer.sha256}",
        f"baselines: PNG files against baselines.prev (set {COMMITTED}): 1 changed, 1 added, 0 removed",
        f"baselines: commit functional_tests/BASELINE_SET to record set {CANDIDATE} with the code",
    ]
    assert tree.fetch.urls == [_url(COMMITTED), _url(CANDIDATE)]
    assert read_pointer(tree.pointer_path) == pointer


def test_adopt_from_scratch_downloads_and_has_no_previous_copy(tree, capsys):
    baselines.adopt(MockContext(), CANDIDATE)

    pointer = _pointer(CANDIDATE)
    fetched, *rest = _lines(capsys)
    assert fetched.startswith(f"baselines: fetched set {CANDIDATE} (3 files, ")
    assert rest == [
        "baselines: wrote functional_tests/BASELINE_SET:",
        f"set={CANDIDATE}",
        f"sha256={pointer.sha256}",
        "baselines: no previous copy (baselines.prev) to compare with",
        f"baselines: commit functional_tests/BASELINE_SET to record set {CANDIDATE} with the code",
    ]
    assert read_pointer(tree.pointer_path) == pointer


def test_adopting_the_committed_current_set_is_a_no_op(tree, capsys):
    tree.commit(COMMITTED)
    baselines.fetch(MockContext())
    capsys.readouterr()
    before = tree.pointer_path.read_text()

    baselines.adopt(MockContext(), COMMITTED)

    assert _lines(capsys) == [
        f"baselines: functional_tests/BASELINE_SET already names set {COMMITTED} "
        "and functional_tests/baselines holds it; nothing changed"
    ]
    assert tree.fetch.urls == [_url(COMMITTED)]
    assert tree.pointer_path.read_text() == before


def test_adopt_of_a_missing_set_exits_non_zero_and_leaves_the_pointer(tree, capsys):
    tree.commit(COMMITTED)

    with pytest.raises(Exit) as failure:
        baselines.adopt(MockContext(), MISSING)

    assert failure.value.code == 1
    assert failure.value.message == set_not_found_message(MISSING, _url(MISSING))
    assert read_pointer(tree.pointer_path) == _pointer(COMMITTED)
    assert capsys.readouterr().out == ""


def test_adopt_of_a_malformed_name_exits_non_zero_without_fetching(tree):
    with pytest.raises(Exit) as failure:
        baselines.adopt(MockContext(), "bootstrap3")

    assert failure.value.code == 1
    assert "is not YYYY-MM-DD-<slug>" in failure.value.message
    assert tree.fetch.urls == []


# report


def _contents(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def _counts(changed, added, removed, unchanged):
    return f"baselines: PNG files: {changed} changed, {added} added, {removed} removed, {unchanged} unchanged"


REPORT_WRITTEN = "baselines: report written to perma_web/failed_test_files/baseline-report/index.html"
REPORT_EMPTIED = "baselines: the next pytest run empties failed_test_files/; copy the report out, or pass --out, to keep it"
WORKING_CANDIDATE = f"functional_tests/baselines (set {CANDIDATE})"


@pytest.fixture
def preview(tree, capsys):
    """The working copy holds CANDIDATE, installed by `fetch --name` with no copy before it, so no baselines.prev."""
    baselines.fetch(MockContext(), name=CANDIDATE)
    capsys.readouterr()
    return tree


def test_report_compares_the_working_copy_with_prev_by_default(tree, capsys):
    tree.commit(COMMITTED)
    baselines.fetch(MockContext())
    baselines.fetch(MockContext(), name=CANDIDATE)
    capsys.readouterr()

    baselines.report(MockContext())

    assert _lines(capsys) == [
        f"baselines: compared {WORKING_CANDIDATE} with baselines.prev (set {COMMITTED})",
        _counts(1, 1, 0, 1),
        REPORT_WRITTEN,
        REPORT_EMPTIED,
    ]
    assert (tree.report_dir / "index.html").is_file()
    assert (tree.report_dir / "changed/chromium/t/f/page-diff.png").is_file()
    assert (tree.report_dir / "added/webkit/t/f/page.png").is_file()
    assert f"Baseline set <code>{CANDIDATE}</code>" in (tree.report_dir / "index.html").read_text()
    assert tree.fetch.urls == [_url(COMMITTED), _url(CANDIDATE)]


def test_report_without_prev_counts_every_image_as_added(preview, capsys):
    baselines.report(MockContext(), against="prev")

    assert _lines(capsys) == [
        f"baselines: there is no baselines.prev, so every image in {WORKING_CANDIDATE} counts as added",
        _counts(0, 3, 0, 0),
        REPORT_WRITTEN,
        REPORT_EMPTIED,
    ]
    assert (preview.report_dir / "index.html").is_file()


def test_report_against_committed_installs_it_aside_and_leaves_the_working_copy(preview, capsys):
    preview.commit(COMMITTED)
    before = _contents(preview.baselines_dir)

    baselines.report(MockContext(), against="committed")

    fetched, *rest = _lines(capsys)
    assert fetched.startswith(f"baselines: fetched set {COMMITTED} (2 files, ")
    assert rest == [
        f"baselines: compared {WORKING_CANDIDATE} with the committed set {COMMITTED}",
        _counts(1, 1, 0, 1),
        REPORT_WRITTEN,
        REPORT_EMPTIED,
    ]
    assert preview.fetch.urls == [_url(CANDIDATE), _url(COMMITTED)]
    assert _contents(preview.baselines_dir) == before
    assert read_stamp(preview.baselines_dir) == _pointer(CANDIDATE)
    assert not preview.baselines_dir.with_name("baselines.prev").exists()
    assert list(preview.temp_dir.iterdir()) == []


def test_report_against_committed_without_a_pointer_exits_non_zero_and_keeps_the_last_report(preview, capsys):
    stale = preview.report_dir / "index.html"
    stale.parent.mkdir(parents=True)
    stale.write_text("the last report")

    with pytest.raises(Exit) as failure:
        baselines.report(MockContext(), against="committed")

    assert failure.value.code == 1
    assert failure.value.message == (
        f"baselines: there is no committed set to compare with: {preview.pointer_path} does not exist"
    )
    assert capsys.readouterr().out == ""
    assert preview.fetch.urls == [_url(CANDIDATE)]
    assert stale.read_text() == "the last report"
    assert list(preview.temp_dir.iterdir()) == []


def test_report_against_a_named_set_installs_it_aside(preview, capsys):
    before = _contents(preview.baselines_dir)

    baselines.report(MockContext(), against=COMMITTED)

    fetched, *rest = _lines(capsys)
    assert fetched.startswith(f"baselines: fetched set {COMMITTED} (2 files, ")
    assert rest[:2] == [f"baselines: compared {WORKING_CANDIDATE} with set {COMMITTED}", _counts(1, 1, 0, 1)]
    assert preview.fetch.urls == [_url(CANDIDATE), _url(COMMITTED)]
    assert _contents(preview.baselines_dir) == before
    assert not preview.pointer_path.exists()
    assert list(preview.temp_dir.iterdir()) == []


def test_report_against_a_missing_set_exits_non_zero_with_the_message(preview, capsys):
    with pytest.raises(Exit) as failure:
        baselines.report(MockContext(), against=MISSING)

    assert failure.value.code == 1
    assert failure.value.message == set_not_found_message(MISSING, _url(MISSING))
    assert not preview.report_dir.exists()


def test_report_replaces_the_default_output_directory(preview, capsys):
    stale = preview.report_dir / "changed/chromium/t/f/old-diff.png"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"stale")

    baselines.report(MockContext())

    assert not stale.exists()
    assert sorted(_contents(preview.report_dir)) == [
        "added/chromium/t/f/page.png",
        "added/firefox/t/f/page.png",
        "added/webkit/t/f/page.png",
        "index.html",
    ]


def test_report_out_writes_elsewhere_and_says_where(preview, tmp_path, capsys):
    out = tmp_path / "elsewhere" / "report"

    baselines.report(MockContext(), out=str(out))

    assert _lines(capsys)[1:] == [_counts(0, 3, 0, 0), f"baselines: report written to {out.resolve() / 'index.html'}"]
    assert (out / "index.html").is_file()
    assert not preview.report_dir.exists()


def test_report_out_inside_perma_web_is_shown_from_the_repository_root(preview, capsys):
    out = preview.baselines_dir.parent.parent / "my-report"

    baselines.report(MockContext(), out=str(out))

    assert _lines(capsys)[2:] == ["baselines: report written to perma_web/my-report/index.html"]


def test_report_out_that_is_not_empty_exits_non_zero_and_is_left_alone(preview, tmp_path, capsys):
    out = tmp_path / "mine"
    out.mkdir()
    (out / "keep.txt").write_text("keep")

    with pytest.raises(Exit) as failure:
        baselines.report(MockContext(), out=str(out))

    assert failure.value.code == 1
    assert failure.value.message == f"baselines: {out} is not an empty directory; the report needs a fresh one"
    assert _contents(out) == {"keep.txt": b"keep"}
    assert capsys.readouterr().out == ""


def test_report_without_a_working_copy_exits_non_zero_without_fetching(tree, capsys):
    tree.commit(COMMITTED)

    with pytest.raises(Exit) as failure:
        baselines.report(MockContext(), against="committed")

    assert failure.value.code == 1
    assert failure.value.message.startswith(f"baselines: there is no working copy at {tree.baselines_dir} to report on")
    assert tree.fetch.urls == []
    assert not tree.report_dir.exists()
