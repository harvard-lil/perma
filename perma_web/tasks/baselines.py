"""
Developer commands for visual baseline sets: `d invoke baselines.fetch`, `baselines.adopt` and `baselines.report`.

Each task parses its options, calls `functional_tests/baseline_sets.py` or
`functional_tests/baseline_report.py` and prints what happened, one fact per
line. A BaselineSetError or ReportError ends the task with its message and exit
status 1. See "Baseline sets" in developer.md.
"""

import os
import shutil
import tempfile
from pathlib import Path

from invoke import Exit, task

from functional_tests import baseline_sets
from functional_tests.baseline_report import (
    DEFAULT_TOLERANCE,
    PREVIOUS_COPY,
    Previous,
    ReportError,
    ReportSummary,
    build_report,
    resolve_previous,
)
from functional_tests.baseline_sets import Adoption, BaselineSetError, Outcome, Pointer, Status, fetch_bytes

# Looked up when a task runs, so tests can aim the tasks at a temporary tree.
PERMA_WEB = Path(__file__).resolve().parent.parent
POINTER_PATH = baseline_sets.POINTER_PATH
BASELINES_DIR = baseline_sets.BASELINES_DIR
# Inside pytest-playwright's --output directory: ignored by git and Docker, and visible on the host through the bind mount.
REPORT_DIR = PERMA_WEB / "failed_test_files" / "baseline-report"


def _shown(path: Path) -> str:
    return f"{path.parent.name}/{path.name}"


def _held(stamp: Pointer | None) -> str:
    return f"set {stamp.name}" if stamp else "no stamp"


def _as_host_sees(path: Path) -> str:
    """The path from the repository root when it is under perma_web, which the container bind-mounts; else as it is."""
    resolved, perma_web = path.resolve(), PERMA_WEB.resolve()
    if resolved.is_relative_to(perma_web):
        return (Path(perma_web.name) / resolved.relative_to(perma_web)).as_posix()
    return str(resolved)


def _status_line(outcome: Outcome) -> str:
    directory = _shown(outcome.directory)
    if outcome.status is Status.DISABLED:
        value = os.environ.get(baseline_sets.FETCH_ENV, "").strip()
        return f"baselines: fetching is off ({baseline_sets.FETCH_ENV}={value}); {directory} is used as it is"
    if outcome.status is Status.NO_POINTER:
        return f"baselines: legacy mode: there is no {_shown(POINTER_PATH)}, so {directory} is used as it is"
    return f"baselines: set {outcome.pointer.name} is current in {directory}; nothing downloaded"


def _preview_line(name: str, committed: Pointer | None) -> str:
    if committed is None:
        return f"baselines: there is no {_shown(POINTER_PATH)}, so pytest uses this copy as it is until a set is adopted"
    if committed.name == name:
        return f"baselines: {_shown(POINTER_PATH)} already names set {name}"
    return (
        f"baselines: this is a preview; the next pytest run swaps set {committed.name} back in "
        f"unless you adopt this one with `d invoke baselines.adopt {name}`"
    )


def _changes_line(adoption: Adoption) -> str:
    previous = adoption.previous_dir.name
    if adoption.changes is None:
        return f"baselines: no previous copy ({previous}) to compare with"
    changed, added, removed = adoption.changes
    return (
        f"baselines: PNG files against {previous} ({_held(adoption.previous_set)}): "
        f"{changed} changed, {added} added, {removed} removed"
    )


def _report_lines(previous: Previous, working: Pointer | None, summary: ReportSummary, out_dir: Path) -> list[str]:
    new = f"{_shown(BASELINES_DIR)} ({_held(working)})"
    if previous.directory is None:
        compared = f"baselines: there is no {previous.label}, so every image in {new} counts as added"
    else:
        compared = f"baselines: compared {new} with {previous.label}"
    totals = summary.totals
    lines = [
        compared,
        f"baselines: PNG files: {totals.changed} changed, {totals.added} added, "
        f"{totals.removed} removed, {totals.unchanged} unchanged",
        f"baselines: report written to {_as_host_sees(out_dir / 'index.html')}",
    ]
    emptied = REPORT_DIR.parent
    if out_dir.resolve().is_relative_to(emptied.resolve()):
        lines.append(f"baselines: the next pytest run empties {emptied.name}/; copy the report out, or pass --out, to keep it")
    return lines


@task(help={
    "name": "Install this set instead of the pointer's: a preview that lasts until the next pytest run, unless adopted.",
    "force": "Download the set (the pointer's, or --name's) again even when the working copy already holds it.",
})
def fetch(ctx, name=None, force=False):
    """
    Bring functional_tests/baselines to the set functional_tests/BASELINE_SET names, and say what happened.
    """
    try:
        if name:
            committed = baseline_sets.read_pointer(POINTER_PATH)
            baseline_sets.install_set(name, BASELINES_DIR, fetch=fetch_bytes, log=print, force=force)
            print(_preview_line(name, committed))
            return
        outcome = baseline_sets.ensure_set(POINTER_PATH, BASELINES_DIR, fetch=fetch_bytes, log=print, force=force)
    except BaselineSetError as error:
        raise Exit(str(error), code=1) from error
    # ensure_set has already printed the line of a download.
    if outcome.status is not Status.FETCHED:
        print(_status_line(outcome))


@task(help={"name": "The set to adopt, YYYY-MM-DD-<slug>; `gh release list` or `git tag -l 'baselines-*'` lists them."})
def adopt(ctx, name):
    """
    Make NAME the committed set: write functional_tests/BASELINE_SET and count the PNGs that changed.
    """
    try:
        adoption = baseline_sets.adopt_set(name, POINTER_PATH, BASELINES_DIR, fetch=fetch_bytes, log=print)
    except BaselineSetError as error:
        raise Exit(str(error), code=1) from error
    pointer_file = _shown(POINTER_PATH)
    if adoption.already_adopted:
        print(f"baselines: {pointer_file} already names set {name} and {_shown(BASELINES_DIR)} holds it; nothing changed")
        return
    print(f"baselines: wrote {pointer_file}:")
    print(baseline_sets.format_pointer(adoption.pointer), end="")
    print(_changes_line(adoption))
    print(f"baselines: commit {pointer_file} to record set {name} with the code")


@task(help={
    "against": "What to compare the working copy with: prev (baselines.prev, the default), committed (the pointer's set) or a set name.",
    "out": "Write the report to this directory, which must be empty or absent, instead of failed_test_files/baseline-report/.",
})
def report(ctx, against=PREVIOUS_COPY, out=None):
    """
    Write a review page comparing the working copy's PNGs with baselines.prev, the committed set or a named set.
    """
    out_dir = Path(out) if out else REPORT_DIR
    working = baseline_sets.read_stamp(BASELINES_DIR)
    try:
        # A set to compare with is installed here, never into the working copy, and removed afterwards.
        with tempfile.TemporaryDirectory(prefix="baseline-report-") as scratch:
            previous = resolve_previous(
                against, BASELINES_DIR, Path(scratch), pointer_path=POINTER_PATH, fetch=fetch_bytes, log=print
            )
            # Only the default is cleared; a directory the user names must be empty, as build_report requires.
            if not out and out_dir.is_dir():
                shutil.rmtree(out_dir)
            summary = build_report(
                previous.directory, BASELINES_DIR, out_dir, DEFAULT_TOLERANCE, name=working.name if working else None
            )
    except BaselineSetError as error:
        raise Exit(str(error), code=1) from error
    except ReportError as error:
        raise Exit(f"baselines: {error}", code=1) from error
    for line in _report_lines(previous, working, summary, out_dir):
        print(line)
