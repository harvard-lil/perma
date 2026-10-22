"""
Developer commands for visual baseline sets: `d invoke baselines.fetch` and `d invoke baselines.adopt`.

Each task parses its options, calls `functional_tests/baseline_sets.py` and
prints what happened, one fact per line. A BaselineSetError ends the task with
its message and exit status 1. See "Baseline sets" in developer.md.
"""

import os
from pathlib import Path

from invoke import Exit, task

from functional_tests import baseline_sets
from functional_tests.baseline_sets import Adoption, BaselineSetError, Outcome, Pointer, Status, fetch_bytes

# Looked up when a task runs, so tests can aim the tasks at a temporary tree.
POINTER_PATH = baseline_sets.POINTER_PATH
BASELINES_DIR = baseline_sets.BASELINES_DIR


def _shown(path: Path) -> str:
    return f"{path.parent.name}/{path.name}"


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
    held = f"set {adoption.previous_set.name}" if adoption.previous_set else "no stamp"
    changed, added, removed = adoption.changes
    return f"baselines: PNG files against {previous} ({held}): {changed} changed, {added} added, {removed} removed"


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


@task(help={"name": "The set to adopt, YYYY-MM-DD-<slug>; `git tag -l 'baselines/*'` lists them."})
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
