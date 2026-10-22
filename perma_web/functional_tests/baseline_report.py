"""
A review page for a newly rendered baseline set, against the set it would replace.

`build_report` matches the PNGs of two baseline directories by relative path
and classifies each one: unchanged (`image_diff.compare_images` passes at the
tolerance), changed (it does not, a change of size included), added (only in
the new directory) or removed (only in the previous one). In the output
directory it writes, for each changed image, `changed/<path>-expected.png`,
`-actual.png` and `-diff.png`; copies each added image to `added/<path>`; and
writes `index.html`, which needs nothing else: inline CSS, no scripts, images
by relative path.

The baselines workflow (`.github/workflows/baselines.yml`) runs both commands
in the test container:

    python -m functional_tests.baseline_report fetch-previous --into DIR
    python -m functional_tests.baseline_report (--previous DIR | --no-previous) \\
        --new DIR --out DIR [--tolerance N] [--name SET] [--summary-json FILE]

`fetch-previous` installs the set the committed pointer names into DIR with
`baseline_sets.ensure_set` and prints its name, or `none` when there is no
pointer (the first set). The report command prints the totals and exits 0
whether or not anything changed: the report informs a review; it is not a gate.

Pillow and the stdlib only, so it runs without Django.
"""

import argparse
import filecmp
import html
import json
import os
import shutil
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from urllib.parse import quote

from PIL import Image

# POINTER_PATH and fetch_bytes are looked up when a command runs, so tests can substitute them.
from functional_tests.baseline_sets import (
    FETCH_ENV,
    POINTER_PATH,
    BaselineSetError,
    Pointer,
    ensure_set,
    fetch_bytes,
    read_stamp,
)
from functional_tests.image_diff import SNAPSHOT_TOLERANCE, ImageComparison, compare_images

# The suite's own tolerance, so the report counts as changed exactly what assert_snapshot would fail.
DEFAULT_TOLERANCE = SNAPSHOT_TOLERANCE

_CHANGED_DIR = "changed"
_ADDED_DIR = "added"
_TOP_LEVEL = "(top level)"
_PROG = "python -m functional_tests.baseline_report"


class ReportError(ValueError):
    """The report's inputs are unusable: a missing directory, an output directory in use, or a bad tolerance."""


class Kind(Enum):
    """How a baseline differs between the previous set and the new one."""

    CHANGED = "changed"
    ADDED = "added"
    REMOVED = "removed"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class Counts:
    """The number of baselines of each kind."""

    changed: int = 0
    added: int = 0
    removed: int = 0
    unchanged: int = 0


@dataclass(frozen=True)
class ChangedImage:
    """A baseline that differs beyond the tolerance, with the numbers `compare_images` gave; see `ImageComparison`."""

    path: str
    differing_pixels: int
    max_channel_difference: int
    bbox: tuple[int, int, int, int] | None
    baseline_size: tuple[int, int]
    actual_size: tuple[int, int]


@dataclass(frozen=True)
class ReportSummary:
    """
    What `build_report` found.

    `name` is the new set's name, if one was given. `previous_set` names the set
    in the previous directory, from its stamp; it is None when that directory
    has no stamp or there was no previous directory (`has_previous` False).
    `browsers` maps each browser, a path's first component, to its counts, in
    name order. Paths are relative to the baselines directories, with `/`.
    """

    name: str | None
    has_previous: bool
    previous_set: str | None
    tolerance: int
    totals: Counts
    browsers: Mapping[str, Counts]
    changed: tuple[ChangedImage, ...]
    added: tuple[str, ...]
    removed: tuple[str, ...]

    def to_markdown(self) -> str:
        """
        Render what was compared and the per-browser counts as Markdown, for a GitHub job summary.

        Returns one sentence naming the comparison, a blank line, and a table
        with a row per browser and a final row of totals.
        """
        if not self.has_previous:
            against = "No previous set: every image counts as added."
        else:
            previous = f"set `{self.previous_set}`" if self.previous_set else "the previous baselines"
            against = f"Compared with {previous}; a pixel differs when a channel is off by more than {self.tolerance} of 255."
        totals = self.totals
        return "\n".join([
            against,
            "",
            "| Browser | Changed | Added | Removed | Unchanged |",
            "| --- | ---: | ---: | ---: | ---: |",
            *(
                f"| {browser.replace('|', '&#124;')} | {counts.changed} | {counts.added} | {counts.removed} | {counts.unchanged} |"
                for browser, counts in self.browsers.items()
            ),
            f"| **All** | **{totals.changed}** | **{totals.added}** | **{totals.removed}** | **{totals.unchanged}** |",
        ]) + "\n"

    def to_dict(self) -> dict:
        """Return the summary as JSON-ready data, with the `to_markdown` text under `markdown`."""
        return {**asdict(self), "markdown": self.to_markdown()}


def _pngs(root: Path) -> dict[str, Path]:
    return {path.relative_to(root).as_posix(): path for path in root.rglob("*.png") if path.is_file()}


def _browser(path: str) -> str:
    first, slash, _ = path.partition("/")
    return first if slash else _TOP_LEVEL


def _change_files(path: str) -> dict[str, str]:
    stem = f"{_CHANGED_DIR}/{path.removesuffix('.png')}"
    return {role: f"{stem}-{role}.png" for role in ("expected", "actual", "diff")}


def _compare(baseline: Path, actual: Path, tolerance: int) -> ImageComparison | None:
    """The failed comparison of two baselines, or None when they match; identical files are not decoded."""
    if filecmp.cmp(baseline, actual, shallow=False):
        return None
    with Image.open(baseline) as expected_image, Image.open(actual) as actual_image:
        comparison = compare_images(expected_image, actual_image, tolerance)
    return None if comparison.passed else comparison


def _write_change(out_dir: Path, path: str, baseline: Path, actual: Path, comparison: ImageComparison) -> ChangedImage:
    files = _change_files(path)
    (out_dir / files["expected"]).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(baseline, out_dir / files["expected"])
    shutil.copyfile(actual, out_dir / files["actual"])
    comparison.diff_image.save(out_dir / files["diff"])
    return ChangedImage(
        path=path,
        differing_pixels=comparison.differing_pixels,
        max_channel_difference=comparison.max_channel_difference,
        bbox=comparison.bbox,
        baseline_size=comparison.baseline_size,
        actual_size=comparison.actual_size,
    )


def build_report(
    previous_dir: Path | None,
    new_dir: Path,
    out_dir: Path,
    tolerance: int,
    *,
    name: str | None = None,
) -> ReportSummary:
    """
    Compare newly rendered baselines with the previous set and write the review page.

    Images are written as each is compared, so memory holds one diff at a time.

    Args:
        previous_dir: The set being replaced, or None when there is none (every image is then added).
        new_dir: The newly rendered baselines.
        out_dir: Where `index.html` and its images go; created if absent, and it must be empty.
        tolerance: Largest per-channel difference, out of 255, that still counts as equal.
        name: The new set's name, shown on the page and kept in the summary.

    Returns the ReportSummary.

    Raises:
        ReportError: If the tolerance is outside 0-255, an input directory does
            not exist, or `out_dir` is a file or a directory that is not empty.
    """
    if not 0 <= tolerance <= 255:
        raise ReportError(f"tolerance must be between 0 and 255, got {tolerance}")
    for directory in (previous_dir, new_dir):
        if directory is not None and not directory.is_dir():
            raise ReportError(f"{directory} is not a directory")
    # A reused directory would mix a stale run's diffs into this report.
    if out_dir.exists() and (not out_dir.is_dir() or any(out_dir.iterdir())):
        raise ReportError(f"{out_dir} is not an empty directory; the report needs a fresh one")
    out_dir.mkdir(parents=True, exist_ok=True)

    before = _pngs(previous_dir) if previous_dir is not None else {}
    after = _pngs(new_dir)
    per_kind: Counter[Kind] = Counter()
    per_browser: Counter[tuple[str, Kind]] = Counter()
    changed, added, removed = [], [], []
    for path in sorted(before.keys() | after.keys()):
        if path not in before:
            kind = Kind.ADDED
            added.append(path)
            copy = out_dir / _ADDED_DIR / path
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(after[path], copy)
        elif path not in after:
            kind = Kind.REMOVED
            removed.append(path)
        else:
            comparison = _compare(before[path], after[path], tolerance)
            kind = Kind.UNCHANGED if comparison is None else Kind.CHANGED
            if comparison is not None:
                changed.append(_write_change(out_dir, path, before[path], after[path], comparison))
        per_kind[kind] += 1
        per_browser[_browser(path), kind] += 1

    browsers = sorted({browser for browser, _ in per_browser})
    stamp = read_stamp(previous_dir) if previous_dir is not None else None
    summary = ReportSummary(
        name=name,
        has_previous=previous_dir is not None,
        previous_set=stamp.name if stamp else None,
        tolerance=tolerance,
        totals=Counts(**{kind.value: per_kind[kind] for kind in Kind}),
        browsers={browser: Counts(**{kind.value: per_browser[browser, kind] for kind in Kind}) for browser in browsers},
        changed=tuple(changed),
        added=tuple(added),
        removed=tuple(removed),
    )
    (out_dir / "index.html").write_text(_render_page(summary), encoding="utf-8")
    return summary


_CSS = """
:root { color-scheme: light dark; --rule: #8886; }
body { font: 15px/1.5 system-ui, sans-serif; max-width: 1500px; margin: 0 auto; padding: 1rem 1.5rem 4rem; }
code { font-family: ui-monospace, monospace; font-size: .9em; overflow-wrap: anywhere; }
nav a { margin-right: 1rem; }
.totals span { margin-right: 1.5rem; }
.totals strong { font-size: 1.5em; }
table { border-collapse: collapse; }
th, td { padding: .25rem .75rem; border-bottom: 1px solid var(--rule); text-align: right; }
th:first-child, td:first-child { text-align: left; }
.change { border-top: 1px solid var(--rule); margin-top: 2rem; padding-top: .5rem; }
dl { display: grid; grid-template-columns: max-content 1fr; gap: .1rem 1rem; }
dd { margin: 0; }
.trio { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; align-items: start; }
figure { margin: 0; }
img { display: block; max-width: 100%; height: auto; border: 1px solid var(--rule); }
.thumbs { display: flex; flex-wrap: wrap; gap: 1rem; list-style: none; padding: 0; }
.thumbs li { width: 180px; }
.thumbs img { width: 180px; height: 260px; object-fit: cover; object-position: top; }
@media (max-width: 700px) { .trio { grid-template-columns: 1fr; } }
"""


def _e(text: object) -> str:
    return html.escape(str(text))


def _href(relative: str) -> str:
    return _e(quote(relative))


def _size(size: tuple[int, int]) -> str:
    return f"{size[0]:,} × {size[1]:,}"


def _counts_cells(counts: Counts, cell: str = "td") -> str:
    return "".join(f"<{cell}>{getattr(counts, kind.value):,}</{cell}>" for kind in Kind)


def _render_change(number: int, change: ChangedImage) -> str:
    files = _change_files(change.path)
    union = tuple(max(a, b) for a, b in zip(change.baseline_size, change.actual_size))
    sizes = {"expected": change.baseline_size, "actual": change.actual_size, "diff": union}
    if change.baseline_size == change.actual_size:
        size = _size(change.actual_size)
    else:
        size = f"{_size(change.baseline_size)} expected, {_size(change.actual_size)} actual (sizes differ)"
    bbox = ", ".join(str(edge) for edge in change.bbox) if change.bbox else "none in the shared area"
    figures = "".join(
        f'<figure><figcaption>{role.capitalize()}</figcaption><a href="{_href(files[role])}">'
        f'<img src="{_href(files[role])}" width="{sizes[role][0]}" height="{sizes[role][1]}" loading="lazy" '
        f'alt="{role.capitalize()}: {_e(change.path)}"></a></figure>'
        for role in ("expected", "actual", "diff")
    )
    return (
        f'<article class="change" id="change-{number}">\n'
        f"<h3><code>{_e(change.path)}</code></h3>\n"
        "<dl>"
        f"<dt>Differing pixels</dt><dd>{change.differing_pixels:,}</dd>"
        f"<dt>Worst channel difference</dt><dd>{change.max_channel_difference} of 255</dd>"
        f"<dt>Bounding box (left, top, right, bottom)</dt><dd>{bbox}</dd>"
        f"<dt>Size</dt><dd>{size}</dd>"
        "</dl>\n"
        f'<div class="trio">{figures}</div>\n'
        "</article>"
    )


def _render_page(summary: ReportSummary) -> str:
    title = f"Baseline set {summary.name}" if summary.name else "Baseline report"
    heading = f"Baseline set <code>{_e(summary.name)}</code>" if summary.name else "Baseline report"
    if not summary.has_previous:
        against = "No previous set: every image counts as added."
    else:
        previous = f"set <code>{_e(summary.previous_set)}</code>" if summary.previous_set else "the previous baselines"
        against = (
            f"Compared with {previous}. A pixel differs when any colour channel is off by more than "
            f"{summary.tolerance} of 255; a change of size always counts."
        )
    totals = "".join(f"<span><strong>{getattr(summary.totals, kind.value):,}</strong> {kind.value}</span>" for kind in Kind)
    rows = "\n".join(f"<tr><td>{_e(browser)}</td>{_counts_cells(counts)}</tr>" for browser, counts in summary.browsers.items())
    changes = "\n".join(_render_change(number, change) for number, change in enumerate(summary.changed, start=1))
    added = "\n".join(
        f'<li><a href="{_href(f"{_ADDED_DIR}/{path}")}"><img src="{_href(f"{_ADDED_DIR}/{path}")}" loading="lazy" '
        f'alt="Added: {_e(path)}"></a><code>{_e(path)}</code></li>'
        for path in summary.added
    )
    removed = "\n".join(f"<li><code>{_e(path)}</code></li>" for path in summary.removed)
    none = "<p>None.</p>"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(title)}</title>
<style>{_CSS}</style>
</head>
<body>
<header>
<h1>{heading}</h1>
<p>{against}</p>
<p class="totals">{totals}</p>
<nav><a href="#changed">Changed</a><a href="#added">Added</a><a href="#removed">Removed</a></nav>
</header>
<section id="browsers">
<h2>By browser</h2>
<table>
<thead><tr><th>Browser</th>{"".join(f"<th>{kind.value.capitalize()}</th>" for kind in Kind)}</tr></thead>
<tbody>
{rows}
</tbody>
<tfoot><tr><th>All</th>{_counts_cells(summary.totals, "th")}</tr></tfoot>
</table>
</section>
<section id="changed">
<h2>Changed ({len(summary.changed):,})</h2>
{changes or none}
</section>
<section id="added">
<h2>Added ({len(summary.added):,})</h2>
{f'<ul class="thumbs">{added}</ul>' if added else none}
</section>
<section id="removed">
<h2>Removed ({len(summary.removed):,})</h2>
{f"<ul>{removed}</ul>" if removed else none}
</section>
</body>
</html>
"""


def fetch_previous(into: Path) -> Pointer | None:
    """
    Install the set the committed pointer names into a directory, to compare a new render with.

    Goes through `ensure_set` with its default lock, so a directory that already
    holds the set is not downloaded again, and `PERMA_BASELINES_URL` applies.
    `PERMA_BASELINES_FETCH` is ignored: this asks for the set explicitly.

    Args:
        into: The directory to hold the set; its parent is created if missing.

    Returns the committed Pointer, or None when there is no pointer file (the first set).

    Raises:
        BaselineSetError: If the pointer does not parse, or the set is missing,
            cannot be downloaded, has the wrong sha256 or cannot be extracted.
    """
    environ = {key: value for key, value in os.environ.items() if key != FETCH_ENV}
    into.parent.mkdir(parents=True, exist_ok=True)
    return ensure_set(POINTER_PATH, into, fetch=fetch_bytes, environ=environ).pointer


def _tolerance(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not a whole number") from None
    if not 0 <= number <= 255:
        raise argparse.ArgumentTypeError(f"{number} is outside 0-255")
    return number


def _report_command(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(
        prog=_PROG,
        description="Compare newly rendered baselines with the previous set and write a review page.",
        epilog=f"`{_PROG} fetch-previous --into DIR` installs the committed set into DIR first.",
    )
    previous = parser.add_mutually_exclusive_group(required=True)
    previous.add_argument("--previous", type=Path, metavar="DIR", help="The set being replaced.")
    previous.add_argument("--no-previous", action="store_true", help="There is no previous set: every image is added.")
    parser.add_argument("--new", type=Path, required=True, metavar="DIR", help="The newly rendered baselines.")
    parser.add_argument("--out", type=Path, required=True, metavar="DIR", help="Where to write index.html; must be empty or absent.")
    parser.add_argument("--tolerance", type=_tolerance, default=DEFAULT_TOLERANCE, metavar="N",
                        help=f"Largest per-channel difference, out of 255, that counts as equal (default {DEFAULT_TOLERANCE}).")
    parser.add_argument("--name", metavar="SET", help="The new set's name, shown on the page.")
    parser.add_argument("--summary-json", type=Path, metavar="FILE", help="Also write the counts, paths and Markdown table as JSON.")
    args = parser.parse_args(argv)
    try:
        summary = build_report(args.previous, args.new, args.out, args.tolerance, name=args.name)
    except ReportError as error:
        parser.error(str(error))
    if args.summary_json:
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(json.dumps(summary.to_dict(), indent=2) + "\n", encoding="utf-8")
    totals = summary.totals
    print(
        f"baseline report: {totals.changed} changed, {totals.added} added, {totals.removed} removed, "
        f"{totals.unchanged} unchanged; written to {args.out / 'index.html'}"
    )
    return 0


def _fetch_previous_command(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(
        prog=f"{_PROG} fetch-previous",
        description="Install the set functional_tests/BASELINE_SET names into DIR and print its name, or `none` without a pointer.",
    )
    parser.add_argument("--into", type=Path, required=True, metavar="DIR", help="Where to install the set.")
    args = parser.parse_args(argv)
    try:
        pointer = fetch_previous(args.into)
    except BaselineSetError as error:
        print(error, file=sys.stderr)
        return 1
    print(pointer.name if pointer else "none")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """
    Run `fetch-previous` when it is the first argument, and the report otherwise; see the module docstring.

    Args:
        argv: The arguments, without the program name; `sys.argv[1:]` by default.

    Returns the exit status: 0, or 1 when `fetch-previous` fails. Usage errors exit with status 2.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["fetch-previous"]:
        return _fetch_previous_command(argv[1:])
    return _report_command(argv)


if __name__ == "__main__":
    sys.exit(main())
