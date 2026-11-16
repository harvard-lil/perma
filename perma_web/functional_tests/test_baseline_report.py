"""Unit tests for the baseline review report: PNGs drawn with Pillow in tmp_path and a fake fetcher; no network, browser or database."""

import hashlib
import io
import json
import re
import tarfile
import urllib.request
from html.parser import HTMLParser

import pytest
from PIL import Image

from functional_tests import baseline_report, baseline_sets, image_diff
from functional_tests.baseline_report import (
    ChangedImage,
    Counts,
    Previous,
    ReportError,
    ReportSummary,
    build_report,
    main,
    resolve_previous,
)
from functional_tests.baseline_sets import BaselineSetError, Pointer, SetNotFoundError, format_pointer, read_stamp, write_stamp

TOLERANCE = 3
GREY = (100, 100, 100)
SET = "2026-10-28-bootstrap3"
NEW_SET = "2026-11-02-new-header"


@pytest.fixture(autouse=True)
def no_network_and_clean_env(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("unit tests must not open URLs")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    monkeypatch.delenv(baseline_sets.FETCH_ENV, raising=False)
    monkeypatch.delenv(baseline_sets.URL_ENV, raising=False)


def _png(path, size=(4, 4), color=GREY):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)
    return path


@pytest.fixture
def previous(tmp_path):
    return tmp_path / "previous"


@pytest.fixture
def new(tmp_path):
    return tmp_path / "new"


@pytest.fixture
def out(tmp_path):
    return tmp_path / "report"


@pytest.fixture
def four_kinds(previous, new):
    """Chromium has one baseline of each kind plus two that match; Firefox has one that matches."""
    for root in (previous, new):
        _png(root / "chromium/test_m/test_f/same.png")
        _png(root / "firefox/test_m/test_f/same.png")
    _png(previous / "chromium/test_m/test_f/close.png", color=GREY)
    _png(new / "chromium/test_m/test_f/close.png", color=(103, 100, 100))
    _png(previous / "chromium/test_m/test_f/changed.png", color=GREY)
    _png(new / "chromium/test_m/test_f/changed.png", color=(200, 0, 0))
    _png(new / "chromium/test_m/test_f/added.png")
    _png(previous / "chromium/test_m/test_f/removed.png")


def _files(root):
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


class _Page(HTMLParser):
    """The text of every table row's cells, the page's text, every src and href, and the tags used."""

    def __init__(self, markup):
        super().__init__()
        self.rows, self.links, self.tags, self._text = [], [], set(), []
        self._row = self._cell = None
        self.feed(markup)
        self.text = " ".join(" ".join(self._text).split())

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag)
        self.links += [value for key, value in attrs if key in ("src", "href")]
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        self._text.append(data)
        if self._cell is not None:
            self._cell.append(data)


def _page(out):
    return _Page((out / "index.html").read_text(encoding="utf-8"))


# classification


def test_each_baseline_is_classified_by_its_relative_path(four_kinds, previous, new, out):
    summary = build_report(previous, new, out, TOLERANCE)

    assert summary.totals == Counts(changed=1, added=1, removed=1, unchanged=3)
    assert summary.browsers == {
        "chromium": Counts(changed=1, added=1, removed=1, unchanged=2),
        "firefox": Counts(unchanged=1),
    }
    assert [change.path for change in summary.changed] == ["chromium/test_m/test_f/changed.png"]
    assert summary.added == ("chromium/test_m/test_f/added.png",)
    assert summary.removed == ("chromium/test_m/test_f/removed.png",)
    assert summary.has_previous


def test_the_tolerance_decides_whether_a_small_difference_is_a_change(four_kinds, previous, new, out):
    summary = build_report(previous, new, out, TOLERANCE - 1)

    assert [change.path for change in summary.changed] == [
        "chromium/test_m/test_f/changed.png",
        "chromium/test_m/test_f/close.png",
    ]
    assert summary.changed[1].max_channel_difference == 3


def test_a_change_records_the_comparisons_numbers(previous, new, out):
    _png(previous / "chromium/t/f/page.png", size=(4, 4))
    image = Image.new("RGB", (4, 4), GREY)
    image.putpixel((1, 2), (0, 0, 0))
    image.save(_png(new / "chromium/t/f/page.png"))

    summary = build_report(previous, new, out, TOLERANCE)

    assert summary.changed == (
        ChangedImage("chromium/t/f/page.png", differing_pixels=1, max_channel_difference=100,
                     bbox=(1, 2, 2, 3), baseline_size=(4, 4), actual_size=(4, 4)),
    )


def test_a_change_of_size_is_a_change_even_when_the_shared_area_matches(previous, new, out):
    _png(previous / "webkit/t/f/page.png", size=(4, 4))
    _png(new / "webkit/t/f/page.png", size=(4, 6))

    summary = build_report(previous, new, out, TOLERANCE)

    (change,) = summary.changed
    assert (change.differing_pixels, change.bbox) == (0, None)
    assert (change.baseline_size, change.actual_size) == ((4, 4), (4, 6))
    with Image.open(out / "changed/webkit/t/f/page-diff.png") as diff:
        assert diff.size == (4, 6)
    assert "4 × 4 expected, 4 × 6 actual (sizes differ)" in _page(out).text


def test_files_other_than_pngs_are_ignored(previous, new, out):
    _png(new / "chromium/t/f/page.png")
    write_stamp(new, Pointer(SET, "a" * 64))
    (new / "chromium/notes.txt").write_text("not a baseline")

    summary = build_report(None, new, out, TOLERANCE)

    assert summary.added == ("chromium/t/f/page.png",)


# files written


def test_expected_actual_and_diff_are_written_only_for_changed_images(four_kinds, previous, new, out):
    build_report(previous, new, out, TOLERANCE)

    assert _files(out) == {
        "index.html",
        "changed/chromium/test_m/test_f/changed-expected.png",
        "changed/chromium/test_m/test_f/changed-actual.png",
        "changed/chromium/test_m/test_f/changed-diff.png",
        "added/chromium/test_m/test_f/added.png",
    }
    changed = "chromium/test_m/test_f/changed"
    assert (out / f"changed/{changed}-expected.png").read_bytes() == (previous / f"{changed}.png").read_bytes()
    assert (out / f"changed/{changed}-actual.png").read_bytes() == (new / f"{changed}.png").read_bytes()
    with Image.open(out / f"changed/{changed}-diff.png") as diff:
        assert diff.getpixel((0, 0)) == (255, 0, 0)
    assert (out / "added/chromium/test_m/test_f/added.png").read_bytes() == (
        new / "chromium/test_m/test_f/added.png").read_bytes()


# the page


def test_the_page_shows_the_counts_per_browser_and_in_total(four_kinds, previous, new, out):
    build_report(previous, new, out, TOLERANCE, name=NEW_SET)

    page = _page(out)
    assert page.rows == [
        ["Browser", "Changed", "Added", "Removed", "Unchanged"],
        ["chromium", "1", "1", "1", "2"],
        ["firefox", "0", "0", "0", "1"],
        ["All", "1", "1", "1", "3"],
    ]
    assert f"Baseline set {NEW_SET}" in page.text
    assert "1 changed 1 added 1 removed 3 unchanged" in page.text


def test_the_page_names_every_changed_added_and_removed_path_and_the_numbers(four_kinds, previous, new, out):
    build_report(previous, new, out, TOLERANCE)

    text = _page(out).text
    for path in ("changed", "added", "removed"):
        assert f"chromium/test_m/test_f/{path}.png" in text
    assert "Differing pixels 16" in text
    assert "Worst channel difference 100 of 255" in text
    assert "Bounding box (left, top, right, bottom) 0, 0, 4, 4" in text
    assert "Size 4 × 4" in text


def test_the_page_is_self_contained_and_every_image_it_shows_exists(four_kinds, previous, new, out):
    build_report(previous, new, out, TOLERANCE)

    page = _page(out)
    assert {"style"} <= page.tags
    assert not page.tags & {"script", "link", "iframe"}
    images = [link for link in page.links if not link.startswith("#")]
    assert images
    for link in images:
        assert not re.match(r"[a-z]+:|/", link), link
        assert (out / urllib.request.url2pathname(link)).is_file(), link


def test_paths_are_escaped_in_the_page(previous, new, out):
    _png(previous / "chromium/t/f/a<b>&c.png")
    _png(new / "chromium/t/f/a<b>&c.png", color=(0, 0, 0))

    build_report(previous, new, out, TOLERANCE)

    markup = (out / "index.html").read_text(encoding="utf-8")
    assert "a<b>" not in markup
    assert "a&lt;b&gt;&amp;c.png" in markup


# no previous set, and the previous set's name


def test_without_a_previous_set_every_image_is_added(four_kinds, new, out):
    summary = build_report(None, new, out, TOLERANCE)

    assert summary.totals == Counts(added=5)
    assert not summary.has_previous and summary.previous_set is None
    assert summary.changed == summary.removed == ()
    assert "No previous set: every image counts as added." in _page(out).text
    assert summary.to_markdown().startswith("No previous set: every image counts as added.\n")


def test_the_previous_sets_name_comes_from_its_stamp(four_kinds, previous, new, out):
    write_stamp(previous, Pointer(SET, "a" * 64))

    summary = build_report(previous, new, out, TOLERANCE)

    assert summary.previous_set == SET
    assert f"Compared with set {SET} . A pixel differs" in _page(out).text


# summary


def test_the_markdown_has_one_row_per_browser_and_a_total(four_kinds, previous, new, out):
    write_stamp(previous, Pointer(SET, "a" * 64))

    markdown = build_report(previous, new, out, TOLERANCE).to_markdown()

    assert markdown == (
        f"Compared with set `{SET}`; a pixel differs when a channel is off by more than 3 of 255.\n"
        "\n"
        "| Browser | Changed | Added | Removed | Unchanged |\n"
        "| --- | ---: | ---: | ---: | ---: |\n"
        "| chromium | 1 | 1 | 1 | 2 |\n"
        "| firefox | 0 | 0 | 0 | 1 |\n"
        "| **All** | **1** | **1** | **1** | **3** |\n"
    )


def test_the_markdown_says_when_the_previous_copy_has_no_stamp():
    summary = ReportSummary(None, True, None, 3, Counts(), {}, (), (), ())

    assert summary.to_markdown().splitlines()[0] == (
        "Compared with the previous baselines; a pixel differs when a channel is off by more than 3 of 255."
    )


def test_the_summary_as_data_is_json_ready(four_kinds, previous, new, out):
    summary = build_report(previous, new, out, TOLERANCE, name=NEW_SET)

    data = json.loads(json.dumps(summary.to_dict()))

    assert data["name"] == NEW_SET
    assert data["totals"] == {"changed": 1, "added": 1, "removed": 1, "unchanged": 3}
    assert data["browsers"]["firefox"] == {"changed": 0, "added": 0, "removed": 0, "unchanged": 1}
    assert data["changed"][0]["bbox"] == [0, 0, 4, 4]
    assert data["markdown"] == summary.to_markdown()


# refused inputs


def test_an_output_directory_in_use_is_refused(four_kinds, previous, new, out):
    _png(out / "stale-diff.png")

    with pytest.raises(ReportError, match="not an empty directory"):
        build_report(previous, new, out, TOLERANCE)


def test_a_missing_input_directory_is_refused(new, out, tmp_path):
    with pytest.raises(ReportError, match="is not a directory"):
        build_report(tmp_path / "nowhere", new, out, TOLERANCE)
    with pytest.raises(ReportError, match="is not a directory"):
        build_report(None, tmp_path / "nowhere", out, TOLERANCE)
    assert not out.exists()


def test_a_tolerance_outside_0_to_255_is_refused(new, out):
    with pytest.raises(ReportError, match="between 0 and 255"):
        build_report(None, new, out, 256)


def test_the_default_tolerance_is_the_snapshot_fixtures():
    assert baseline_report.DEFAULT_TOLERANCE == image_diff.SNAPSHOT_TOLERANCE


# the report command


def test_the_command_writes_the_report_and_its_summary_and_exits_0_with_changes(four_kinds, previous, new, out, tmp_path, capsys):
    summary_json = tmp_path / "summary" / "summary.json"

    status = main(["--previous", str(previous), "--new", str(new), "--out", str(out),
                   "--name", NEW_SET, "--summary-json", str(summary_json)])

    assert status == 0
    assert capsys.readouterr().out == (
        f"baseline report: 1 changed, 1 added, 1 removed, 3 unchanged; written to {out / 'index.html'}\n"
    )
    data = json.loads(summary_json.read_text())
    assert (data["name"], data["tolerance"]) == (NEW_SET, baseline_report.DEFAULT_TOLERANCE)
    assert "| chromium | 1 | 1 | 1 | 2 |" in data["markdown"]
    assert (out / "index.html").is_file()


def test_the_command_without_a_previous_set(four_kinds, new, out, capsys):
    assert main(["--no-previous", "--new", str(new), "--out", str(out), "--tolerance", "0"]) == 0

    assert capsys.readouterr().out.startswith("baseline report: 0 changed, 5 added, 0 removed, 0 unchanged;")


@pytest.mark.parametrize("arguments", [
    ["--previous", "p", "--no-previous", "--new", "n", "--out", "o"],
    ["--new", "n", "--out", "o"],
    ["--no-previous", "--new", "n", "--out", "o", "--tolerance", "256"],
    ["--no-previous", "--new", "n", "--out", "o", "--tolerance", "three"],
])
def test_the_command_refuses_bad_arguments_with_status_2(arguments, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(arguments)

    assert exit_info.value.code == 2


def test_the_command_reports_unusable_directories_with_status_2(new, out, tmp_path, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--previous", str(tmp_path / "nowhere"), "--new", str(new), "--out", str(out)])

    assert exit_info.value.code == 2
    assert "nowhere is not a directory" in capsys.readouterr().err


# fetch-previous


def _tar(files):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


COMMITTED_TAR = _tar({"chromium/t/f/page.png": b"committed", "firefox/t/f/page.png": b"ff"})


class FakeFetch:
    """Returns fixed bytes, or raises a fixed exception, recording every URL asked for."""

    def __init__(self, result):
        self.result = result
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


@pytest.fixture
def committed(tmp_path, monkeypatch):
    """Aims fetch-previous at a pointer in tmp_path, served by a FakeFetch; the real file lock is used."""
    pytest.importorskip("filelock")
    pointer_path = tmp_path / "BASELINE_SET"
    fetch = FakeFetch(COMMITTED_TAR)
    monkeypatch.setattr(baseline_report, "POINTER_PATH", pointer_path)
    monkeypatch.setattr(baseline_report, "fetch_bytes", fetch)
    return pointer_path, fetch


def _commit(pointer_path, data=COMMITTED_TAR):
    pointer = Pointer(SET, hashlib.sha256(data).hexdigest())
    pointer_path.write_text(format_pointer(pointer))
    return pointer


def test_fetch_previous_without_a_pointer_prints_none(committed, tmp_path, capsys):
    pointer_path, fetch = committed

    assert main(["fetch-previous", "--into", str(tmp_path / "previous-set")]) == 0

    assert capsys.readouterr().out == "none\n"
    assert fetch.urls == []
    assert not (tmp_path / "previous-set").exists()


def test_fetch_previous_installs_the_committed_set_and_prints_its_name(committed, tmp_path, capsys):
    pointer_path, fetch = committed
    pointer = _commit(pointer_path)
    into = tmp_path / "work" / "previous-set"

    assert main(["fetch-previous", "--into", str(into)]) == 0

    assert capsys.readouterr().out == f"{SET}\n"
    assert fetch.urls == [f"{baseline_sets.DEFAULT_BASE_URL}baselines-{SET}/baselines-{SET}.tar"]
    assert (into / "chromium/t/f/page.png").read_bytes() == b"committed"
    assert read_stamp(into) == pointer


def test_fetch_previous_ignores_a_disabled_fetch_and_honours_the_url(committed, tmp_path, monkeypatch, capsys):
    pointer_path, fetch = committed
    _commit(pointer_path)
    monkeypatch.setenv(baseline_sets.FETCH_ENV, "0")
    monkeypatch.setenv(baseline_sets.URL_ENV, "https://fork.example/sets")

    assert main(["fetch-previous", "--into", str(tmp_path / "previous-set")]) == 0

    assert capsys.readouterr().out == f"{SET}\n"
    assert fetch.urls == [f"https://fork.example/sets/baselines-{SET}/baselines-{SET}.tar"]


def test_fetch_previous_fails_with_status_1_and_the_message(committed, tmp_path, capsys):
    pointer_path, fetch = committed
    _commit(pointer_path)
    fetch.result = SetNotFoundError("answered HTTP 404")

    assert main(["fetch-previous", "--into", str(tmp_path / "previous-set")]) == 1

    output = capsys.readouterr()
    assert output.out == ""
    assert f"set {SET!r}, named in {pointer_path}, is not at" in output.err


def test_fetch_previous_refuses_a_set_whose_hash_differs(committed, tmp_path, capsys):
    pointer_path, fetch = committed
    _commit(pointer_path)
    fetch.result = _tar({"chromium/t/f/page.png": b"tampered"})

    assert main(["fetch-previous", "--into", str(tmp_path / "previous-set")]) == 1

    assert "expects" in capsys.readouterr().err
    assert not (tmp_path / "previous-set").exists()


# resolve_previous


@pytest.fixture
def working(tmp_path):
    """A working copy holding NEW_SET, and an empty scratch directory beside it."""
    baselines_dir = tmp_path / "functional_tests" / "baselines"
    _png(baselines_dir / "chromium/t/f/page.png")
    write_stamp(baselines_dir, Pointer(NEW_SET, "b" * 64))
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    return baselines_dir, scratch


def _contents(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def _set_url(name, base=baseline_sets.DEFAULT_BASE_URL):
    return f"{base}baselines-{name}/baselines-{name}.tar"


def test_prev_is_the_copy_beside_the_working_copy_with_its_stamps_set(working):
    baselines_dir, scratch = working
    previous_dir = baselines_dir.with_name("baselines.prev")
    _png(previous_dir / "chromium/t/f/page.png")
    write_stamp(previous_dir, Pointer(SET, "a" * 64))
    fetch = FakeFetch(AssertionError("prev needs no download"))

    previous = resolve_previous("prev", baselines_dir, scratch, fetch=fetch, log=pytest.fail)

    assert previous == Previous(previous_dir, f"baselines.prev (set {SET})")
    assert fetch.urls == []


def test_prev_without_a_stamp_says_so(working):
    baselines_dir, scratch = working
    previous_dir = baselines_dir.with_name("baselines.prev")
    _png(previous_dir / "chromium/t/f/page.png")

    previous = resolve_previous("prev", baselines_dir, scratch, fetch=FakeFetch(b""), log=pytest.fail)

    assert previous == Previous(previous_dir, "baselines.prev (no stamp)")


def test_a_missing_prev_means_there_is_nothing_to_compare_with(working):
    baselines_dir, scratch = working

    previous = resolve_previous("prev", baselines_dir, scratch, fetch=FakeFetch(b""), log=pytest.fail)

    assert previous == Previous(None, "baselines.prev")


def test_committed_installs_the_pointers_set_into_scratch_and_leaves_the_working_copy_alone(working, tmp_path):
    baselines_dir, scratch = working
    pointer_path = tmp_path / "BASELINE_SET"
    pointer = _commit(pointer_path)
    before = _contents(baselines_dir)
    fetch, lines = FakeFetch(COMMITTED_TAR), []
    environ = {baseline_sets.FETCH_ENV: "0", baseline_sets.URL_ENV: "https://fork.example/sets/"}

    previous = resolve_previous(
        "committed", baselines_dir, scratch, pointer_path=pointer_path, fetch=fetch, log=lines.append, environ=environ
    )

    assert previous == Previous(scratch / "previous", f"the committed set {SET}")
    assert fetch.urls == [_set_url(SET, "https://fork.example/sets/")]
    assert read_stamp(scratch / "previous") == pointer
    assert (scratch / "previous/chromium/t/f/page.png").read_bytes() == b"committed"
    [line] = lines
    assert line.startswith(f"baselines: fetched set {SET} (2 files, ")
    assert _contents(baselines_dir) == before
    assert not baselines_dir.with_name("baselines.prev").exists()
    # No lock file: the scratch directory is the caller's alone.
    assert [path.name for path in scratch.iterdir()] == ["previous"]


def test_committed_without_a_pointer_is_refused_without_a_download(working, tmp_path):
    baselines_dir, scratch = working
    pointer_path = tmp_path / "BASELINE_SET"
    fetch = FakeFetch(COMMITTED_TAR)

    with pytest.raises(ReportError, match="no committed set to compare with") as failure:
        resolve_previous("committed", baselines_dir, scratch, pointer_path=pointer_path, fetch=fetch, log=pytest.fail)

    assert str(pointer_path) in str(failure.value)
    assert fetch.urls == []


def test_committed_still_checks_the_pointers_hash(working, tmp_path):
    baselines_dir, scratch = working
    pointer_path = tmp_path / "BASELINE_SET"
    _commit(pointer_path)
    fetch = FakeFetch(_tar({"chromium/t/f/page.png": b"tampered"}))

    with pytest.raises(BaselineSetError, match="expects"):
        resolve_previous("committed", baselines_dir, scratch, pointer_path=pointer_path, fetch=fetch, log=pytest.fail)

    assert not (scratch / "previous").exists()


def test_a_set_name_is_installed_into_scratch(working, tmp_path):
    baselines_dir, scratch = working
    before = _contents(baselines_dir)
    fetch, lines = FakeFetch(COMMITTED_TAR), []

    previous = resolve_previous(SET, baselines_dir, scratch, pointer_path=tmp_path / "BASELINE_SET", fetch=fetch, log=lines.append)

    assert previous == Previous(scratch / "previous", f"set {SET}")
    assert fetch.urls == [_set_url(SET)]
    assert read_stamp(scratch / "previous") == Pointer(SET, hashlib.sha256(COMMITTED_TAR).hexdigest())
    assert len(lines) == 1
    assert _contents(baselines_dir) == before
    assert not (tmp_path / "BASELINE_SET").exists()


def test_a_missing_set_raises_the_not_found_message(working):
    baselines_dir, scratch = working
    fetch = FakeFetch(SetNotFoundError("answered HTTP 404"))

    with pytest.raises(SetNotFoundError, match=f"set {NEW_SET!r} is not at"):
        resolve_previous(NEW_SET, baselines_dir, scratch, fetch=fetch, log=pytest.fail)


def test_a_malformed_set_name_is_refused_without_a_download(working):
    baselines_dir, scratch = working
    fetch = FakeFetch(COMMITTED_TAR)

    with pytest.raises(BaselineSetError, match="is not YYYY-MM-DD-<slug>"):
        resolve_previous("previous", baselines_dir, scratch, fetch=fetch, log=pytest.fail)

    assert fetch.urls == []


@pytest.mark.parametrize("against", ["prev", "committed", SET])
def test_a_missing_working_copy_is_refused_before_anything_else(against, tmp_path):
    pointer_path = tmp_path / "BASELINE_SET"
    _commit(pointer_path)
    fetch = FakeFetch(COMMITTED_TAR)

    with pytest.raises(ReportError, match="there is no working copy at .* to report on"):
        resolve_previous(against, tmp_path / "baselines", tmp_path, pointer_path=pointer_path, fetch=fetch, log=pytest.fail)

    assert fetch.urls == []
