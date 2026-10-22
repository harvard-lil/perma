"""
Named, immutable sets of visual baselines, fetched on demand.

The PNG baselines live outside git. A committed pointer file,
`functional_tests/BASELINE_SET`, names one set and the sha256 of its tarball:

    set=2026-10-28-bootstrap3
    sha256=<64 lowercase hex digits>

`ensure_set` makes the working copy, `functional_tests/baselines/`, hold that
set. It downloads `<base><name>.tar` (base `DEFAULT_BASE_URL`, or the value of
`PERMA_BASELINES_URL`), checks the hash, extracts the archive into a sibling
staging directory, moves the old copy to `baselines.prev/`, moves the new one
into place, and writes the stamp `baselines/.set` (the pointer's format) last.
A copy whose stamp already matches the pointer is used without any network.

`install_set` installs a set by name with no hash to check (a preview), and
`adopt_set` writes the pointer for a set and counts the PNGs that changed
(`diff_trees`). `tasks/baselines.py` exposes these and `ensure_set` as
`d invoke baselines.fetch` and `d invoke baselines.adopt`.

- The archive holds the directory's contents, not a wrapping folder: its top
  level is `<browser>/...`. A leading `./`, as GNU tar writes it, is fine.
  Only regular files and directories are accepted.
- No pointer file means legacy mode: the directory is used as it is.
- `PERMA_BASELINES_FETCH=0` (or `false`, `no`) turns all of this off; the
  capture workflow uses it to render a set into an empty directory.
- Under pytest-xdist every worker calls `ensure_set`. An exclusive lock on
  `baselines.lock` lets one worker download while the others wait and then
  find the stamp current.

Stdlib only, apart from the `filelock` package behind the default lock.
"""

import hashlib
import http.client
import io
import os
import re
import shutil
import sys
import tarfile
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import NamedTuple

_HERE = Path(__file__).parent

POINTER_PATH = _HERE / "BASELINE_SET"
BASELINES_DIR = _HERE / "baselines"
STAMP_NAME = ".set"

FETCH_ENV = "PERMA_BASELINES_FETCH"
URL_ENV = "PERMA_BASELINES_URL"
DEFAULT_BASE_URL = "https://test-baselines.perma.cc/sets/"

USER_AGENT = "perma-baselines/1 (+https://github.com/harvard-lil/perma)"
FETCH_TIMEOUT_SECONDS = 120

_SET_NAME = re.compile(r"\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*", re.ASCII)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_OFF_VALUES = {"0", "false", "no"}
_OFFLINE_HINT = f"To run against the local functional_tests/baselines as it is, set {FETCH_ENV}=0."
_RETRY_HINT = "The fetch can be retried with `d invoke baselines.fetch`."


class BaselineSetError(RuntimeError):
    """A baseline set could not be read, fetched, verified or installed; the message says what to check."""


class SetNotFoundError(BaselineSetError):
    """No set at the URL. The bucket grants no ListBucket, so a missing key answers 403, not 404."""


@dataclass(frozen=True)
class Pointer:
    """
    A set name and the sha256 of its tarball, as held by the pointer file and by the stamp.

    Raises BaselineSetError on construction if the name is not
    `YYYY-MM-DD-<slug>` (lowercase letters, digits, hyphens) or the hash is not
    64 lowercase hex digits.
    """

    name: str
    sha256: str

    def __post_init__(self):
        _validate_set_name(self.name)
        if not _SHA256.fullmatch(self.sha256):
            raise BaselineSetError(f"sha256 {self.sha256!r} is not 64 lowercase hex digits")


class Status(Enum):
    """What `ensure_set` did."""

    DISABLED = "disabled"      # PERMA_BASELINES_FETCH turned it off
    NO_POINTER = "no-pointer"  # legacy mode: no pointer file
    CURRENT = "current"        # the stamp already matched; no network
    FETCHED = "fetched"


@dataclass(frozen=True)
class Outcome:
    """The result of `ensure_set`: what it did, the working copy, and the pointer it acted on (None unless read)."""

    status: Status
    directory: Path
    pointer: Pointer | None = None


class TreeDiff(NamedTuple):
    """How the PNG files of two baseline directories differ, matched by relative path and compared by sha256."""

    changed: int
    added: int
    removed: int


@dataclass(frozen=True)
class Adoption:
    """
    The result of `adopt_set`.

    `pointer` is what the pointer file now holds. `already_adopted` means the
    pointer already named the set and the working copy held it, so nothing was
    written. Otherwise `previous_dir` is where the copy displaced by the last
    install is kept, `previous_set` is its stamp (None if it has none), and
    `changes` counts the PNGs that differ from it to the working copy (None when
    there is no previous copy).
    """

    pointer: Pointer
    already_adopted: bool = False
    previous_dir: Path | None = None
    previous_set: Pointer | None = None
    changes: TreeDiff | None = None


def _validate_set_name(name: str) -> None:
    # fullmatch, not `$`: `$` would accept a trailing newline.
    if not _SET_NAME.fullmatch(name):
        raise BaselineSetError(
            f"set name {name!r} is not YYYY-MM-DD-<slug> (lowercase letters, digits and hyphens)"
        )


def parse_pointer(text: str, source: str | Path) -> Pointer:
    """
    Parse the pointer (or stamp) format: a `set=<name>` line and a `sha256=<hex>` line, in either order.

    Blank lines and lines starting with `#` are ignored.

    Args:
        text: The file's contents.
        source: Where the text came from, quoted in error messages.

    Returns the Pointer.

    Raises:
        BaselineSetError: On any other line, a repeated or missing key, or a
            malformed name or hash; the message names `source`.
    """
    fields = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, equals, value = line.partition("=")
        key = key.strip()
        if not equals or key not in ("set", "sha256"):
            raise BaselineSetError(f"{source}, line {number}: expected `set=<name>` or `sha256=<hex>`, got {raw!r}")
        if key in fields:
            raise BaselineSetError(f"{source}, line {number}: `{key}` is given twice")
        fields[key] = value.strip()
    missing = [key for key in ("set", "sha256") if key not in fields]
    if missing:
        raise BaselineSetError(f"{source}: no {' or '.join(f'`{key}=`' for key in missing)} line")
    try:
        return Pointer(fields["set"], fields["sha256"])
    except BaselineSetError as error:
        raise BaselineSetError(f"{source}: {error}") from error


def format_pointer(pointer: Pointer) -> str:
    """
    Render a Pointer in the pointer-file format that `parse_pointer` reads.

    Args:
        pointer: The set to name.

    Returns two newline-terminated lines, `set=` first.
    """
    return f"set={pointer.name}\nsha256={pointer.sha256}\n"


def read_pointer(path: Path = POINTER_PATH) -> Pointer | None:
    """
    Read the committed pointer file.

    Args:
        path: The pointer file; `POINTER_PATH` by default.

    Returns the Pointer, or None when the file does not exist (legacy mode).

    Raises:
        BaselineSetError: If the file exists but does not parse.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None
    return parse_pointer(text, path)


def read_stamp(directory: Path) -> Pointer | None:
    """
    Read the stamp naming the set a working copy holds.

    Args:
        directory: The working copy, e.g. `BASELINES_DIR`.

    Returns the Pointer, or None when there is no stamp or it does not parse
    (an unreadable stamp means an unverified copy, which is fetched again).
    """
    stamp = directory / STAMP_NAME
    try:
        return parse_pointer(stamp.read_text(encoding="utf-8", errors="replace"), stamp)
    except (FileNotFoundError, NotADirectoryError, BaselineSetError):
        return None


def write_stamp(directory: Path, pointer: Pointer) -> Path:
    """
    Record which set a working copy holds.

    Args:
        directory: The working copy; it must exist.
        pointer: The set now in it.

    Returns the stamp's path.
    """
    stamp = directory / STAMP_NAME
    stamp.write_text(format_pointer(pointer), encoding="utf-8")
    return stamp


def set_url(name: str, environ: Mapping[str, str] | None = None) -> str:
    """
    Build the download URL of a set.

    Args:
        name: The set name; validated before use.
        environ: Where to look up `PERMA_BASELINES_URL`; `os.environ` by default.

    Returns `<base><name>.tar`, where base is `PERMA_BASELINES_URL` if set
    (given exactly one trailing slash) and `DEFAULT_BASE_URL` otherwise.

    Raises:
        BaselineSetError: If the name is malformed.
    """
    _validate_set_name(name)
    environ = os.environ if environ is None else environ
    base = environ.get(URL_ENV, "").strip() or DEFAULT_BASE_URL
    return f"{base.rstrip('/')}/{name}.tar"


def _http_failure(url: str, error: urllib.error.HTTPError) -> BaselineSetError:
    """The exception `fetch_bytes` raises for an HTTP error status."""
    headers = error.headers or {}
    if error.code == 403 and headers.get("cf-mitigated"):
        return BaselineSetError(
            f"baselines: {url} answered with a Cloudflare challenge (HTTP 403, cf-mitigated), "
            f"so the request never reached the bucket; the hostname's firewall skip is missing. {_OFFLINE_HINT}"
        )
    if error.code == 403:
        return SetNotFoundError(f"baselines: {url} answered HTTP 403, which the bucket returns for a missing key")
    origin_hint = (
        " Cloudflare could not use the bucket as origin; check the hostname's origin rule."
        if 520 <= error.code <= 530 else ""
    )
    return BaselineSetError(
        f"baselines: {url} answered HTTP {error.code} {error.reason}.{origin_hint} {_RETRY_HINT} {_OFFLINE_HINT}"
    )


def fetch_bytes(url: str, timeout: float = FETCH_TIMEOUT_SECONDS) -> bytes:
    """
    Download a URL with a descriptive User-Agent; the default fetcher of this module. Never retries.

    Args:
        url: What to download, normally from `set_url`.
        timeout: Seconds allowed for connecting and for each read.

    Returns the response body.

    Raises:
        SetNotFoundError: On HTTP 403, which is how the bucket reports a missing set.
        BaselineSetError: On any other HTTP status, a Cloudflare challenge, a
            malformed URL, or a network failure (offline, DNS, timeout, truncated body).
    """
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        raise _http_failure(url, error) from error
    except (OSError, ValueError, http.client.HTTPException) as error:  # ValueError: a malformed PERMA_BASELINES_URL
        reason = getattr(error, "reason", error)
        raise BaselineSetError(f"baselines: could not download {url}: {reason}. {_RETRY_HINT} {_OFFLINE_HINT}") from error


def _check_member(member: tarfile.TarInfo) -> None:
    path = PurePosixPath(member.name)
    # The data filter strips a leading `/` rather than refusing it, so check the raw name first.
    if path.is_absolute() or ".." in path.parts:
        raise BaselineSetError(
            f"baselines: the set's tarball contains {member.name!r}; only paths relative to the baselines directory are allowed"
        )
    # The data filter admits symlinks that stay inside the destination; a set has no use for them.
    if not (member.isfile() or member.isdir()):
        raise BaselineSetError(
            f"baselines: the set's tarball contains {member.name!r}, which is not a regular file or directory"
        )


def extract_set(data: bytes, destination: Path) -> int:
    """
    Extract a set's tarball into a directory, admitting only regular files and directories.

    Every member is checked before anything is written, so a refused archive
    leaves `destination` as it was. tarfile's `data` filter is applied as well.

    Args:
        data: An uncompressed tar archive of the baselines directory's contents.
        destination: An existing directory, normally empty.

    Returns the number of regular files extracted.

    Raises:
        BaselineSetError: If the bytes are not an uncompressed tar, or a member
            has an absolute path or a `..` component, or is a link, device or FIFO.
    """
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as archive:
            members = archive.getmembers()
            for member in members:
                _check_member(member)
            archive.extractall(destination, members=members, filter="data")
    except tarfile.TarError as error:
        raise BaselineSetError(f"baselines: the set's tarball cannot be extracted: {error}") from error
    return sum(1 for member in members if member.isfile())


def _sibling(directory: Path, suffix: str) -> Path:
    return directory.with_name(directory.name + suffix)


def _human_size(size: int) -> str:
    if size < 1_000_000:
        return f"{size / 1000:.0f} kB"
    return f"{size / 1_000_000:.1f} MB"


def _log_to_stderr(line: str) -> None:
    print(line, file=sys.stderr)


def _file_lock(path: Path) -> AbstractContextManager:
    # Imported on use so the rest of the module, and its unit tests, need only the stdlib.
    from filelock import FileLock
    return FileLock(str(path))


def set_not_found_message(name: str, url: str, pointer_path: Path | None = None) -> str:
    """
    Explain a set that is not at its URL (HTTP 403); every download in this module raises SetNotFoundError with it.

    Args:
        name: The set asked for.
        url: Where it was looked for.
        pointer_path: The pointer file naming the set, or None when the set was
            asked for by name (a preview or an adoption).

    Returns the message: the set, the URL, both likely causes, and the note
    that a cached 403 can hide a set uploaded minutes ago.
    """
    if pointer_path is None:
        subject = f"set {name!r}"
        cause = "no set by that name was ever uploaded (`git tag -l 'baselines/*'` lists the sets requested so far)"
    else:
        subject = f"set {name!r}, named in {pointer_path},"
        cause = "the pointer names a set that was never uploaded"
    return (
        f"baselines: {subject} is not at {url} (HTTP 403). Either {cause}, or {URL_ENV} points at the wrong place. "
        "A set uploaded in the last few minutes can still be hidden by a cached 403: retry shortly before suspecting the upload."
    )


def _download(name: str, url: str, fetch: Callable[[str], bytes], pointer_path: Path | None) -> bytes:
    try:
        return fetch(url)
    except SetNotFoundError as error:
        raise SetNotFoundError(set_not_found_message(name, url, pointer_path)) from error


def _install(data: bytes, baselines_dir: Path) -> tuple[int, bool]:
    """Swap the extracted set in; return the file count and whether a previous copy was kept."""
    staging = _sibling(baselines_dir, ".tmp")
    if staging.exists():
        # Left by a run killed mid-extraction; only this function writes there, and only under the lock.
        shutil.rmtree(staging)
    staging.mkdir()
    try:
        files = extract_set(data, staging)
    except BaseException:
        shutil.rmtree(staging)
        raise
    previous = _sibling(baselines_dir, ".prev")
    kept_previous = baselines_dir.exists()
    if kept_previous:
        if previous.exists():
            shutil.rmtree(previous)
        baselines_dir.rename(previous)
    staging.rename(baselines_dir)
    return files, kept_previous


class _Installed(NamedTuple):
    pointer: Pointer
    files: int
    size: int
    kept_previous: bool


def _fetch_and_install(
    name: str,
    baselines_dir: Path,
    *,
    fetch: Callable[[str], bytes],
    environ: Mapping[str, str] | None,
    pointer_path: Path | None = None,
    expected_sha256: str | None = None,
) -> _Installed:
    """The one download, verify and install path; the caller holds the lock. The stamp records the actual hash."""
    url = set_url(name, environ)
    data = _download(name, url, fetch, pointer_path)
    actual = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None and actual != expected_sha256:
        raise BaselineSetError(
            f"baselines: {url} has sha256 {actual}, but {pointer_path} expects {expected_sha256}; "
            f"{baselines_dir} was left as it was. Either the pointer's hash is wrong or the stored set "
            "changed: find out which before editing the hash. If the stored set is the right one, "
            f"`d invoke baselines.adopt {name}` rewrites the pointer from a fresh download."
        )
    files, kept_previous = _install(data, baselines_dir)
    pointer = Pointer(name, actual)
    write_stamp(baselines_dir, pointer)
    return _Installed(pointer, files, len(data), kept_previous)


def _fetched_line(installed: _Installed, baselines_dir: Path) -> str:
    kept = f"; previous copy kept at {_sibling(baselines_dir, '.prev').name}" if installed.kept_previous else ""
    return (
        f"baselines: fetched set {installed.pointer.name} ({installed.files} files, {_human_size(installed.size)}) "
        f"into {baselines_dir.parent.name}/{baselines_dir.name}{kept}"
    )


def ensure_set(
    pointer_path: Path = POINTER_PATH,
    baselines_dir: Path = BASELINES_DIR,
    *,
    fetch: Callable[[str], bytes] = fetch_bytes,
    log: Callable[[str], None] = _log_to_stderr,
    lock: Callable[[Path], AbstractContextManager] = _file_lock,
    environ: Mapping[str, str] | None = None,
    force: bool = False,
) -> Outcome:
    """
    Make the working copy hold the set the pointer names, downloading it only when the stamp differs.

    Does nothing when `PERMA_BASELINES_FETCH` is `0`, `false` or `no`, or when
    there is no pointer file. Otherwise, holding `lock` on `<baselines_dir>.lock`,
    it compares the stamp with the pointer; on a difference it fetches the set,
    checks its sha256, extracts it beside the working copy, moves the working
    copy to `<baselines_dir>.prev` (replacing an older one), moves the new set
    into place, writes the stamp, and logs one line. The working copy itself is
    never deleted.

    Args:
        pointer_path: The pointer file; `POINTER_PATH` by default.
        baselines_dir: The working copy; `BASELINES_DIR` by default.
        fetch: Returns the bytes at a URL; raises SetNotFoundError for a missing
            set and BaselineSetError for other failures. `fetch_bytes` by default.
        log: Receives the one-line report of a download; stderr by default.
        lock: Returns an exclusive, blocking context manager for a lock-file
            path; `filelock.FileLock` by default.
        environ: Where to read `PERMA_BASELINES_FETCH` and `PERMA_BASELINES_URL`;
            `os.environ` by default.
        force: Fetch even when the stamp matches the pointer. A disabled fetch
            or a missing pointer still does nothing, and the hash is still checked.

    Returns an Outcome whose status is DISABLED, NO_POINTER, CURRENT or FETCHED.

    Raises:
        SetNotFoundError: If the set is not at its URL (the message names the
            set, the URL and the likely causes).
        BaselineSetError: If the pointer does not parse, the download fails,
            the sha256 differs (the working copy and stamp are then untouched),
            or the tarball is unsafe or unreadable.
    """
    environ = os.environ if environ is None else environ
    if environ.get(FETCH_ENV, "").strip().lower() in _OFF_VALUES:
        return Outcome(Status.DISABLED, baselines_dir)
    pointer = read_pointer(pointer_path)
    if pointer is None:
        return Outcome(Status.NO_POINTER, baselines_dir)

    with lock(_sibling(baselines_dir, ".lock")):
        # Read only now: another worker may have installed the set while this one waited.
        if not force and read_stamp(baselines_dir) == pointer:
            return Outcome(Status.CURRENT, baselines_dir, pointer)
        installed = _fetch_and_install(
            pointer.name,
            baselines_dir,
            fetch=fetch,
            environ=environ,
            pointer_path=pointer_path,
            expected_sha256=pointer.sha256,
        )
    log(_fetched_line(installed, baselines_dir))
    return Outcome(Status.FETCHED, baselines_dir, pointer)


def install_set(
    name: str,
    baselines_dir: Path = BASELINES_DIR,
    *,
    fetch: Callable[[str], bytes] = fetch_bytes,
    log: Callable[[str], None] = _log_to_stderr,
    lock: Callable[[Path], AbstractContextManager] = _file_lock,
    environ: Mapping[str, str] | None = None,
    force: bool = False,
) -> Pointer:
    """
    Download a set by name and install it as `ensure_set` does, with no expected hash to check.

    For previewing a set that no pointer names yet. When the stamp already
    names the set, nothing is downloaded unless `force` is given. It ignores
    `PERMA_BASELINES_FETCH`, since the set was asked for by name. The stamp
    records the hash of what was downloaded.

    Args:
        name: The set, `YYYY-MM-DD-<slug>`.
        baselines_dir: The working copy; `BASELINES_DIR` by default.
        fetch, log, lock, environ: As for `ensure_set`; `log` gets one line either way.
        force: Download and install the set even when the stamp already names it.

    Returns the Pointer naming the set and the sha256 of its tarball (the
    stamp's, when nothing was downloaded).

    Raises:
        SetNotFoundError: If the set is not at its URL.
        BaselineSetError: If the name is malformed, the download fails, or the
            tarball is unsafe or unreadable; the working copy is then untouched.
    """
    _validate_set_name(name)
    with lock(_sibling(baselines_dir, ".lock")):
        held = read_stamp(baselines_dir)
        installed = None
        if force or held is None or held.name != name:
            installed = _fetch_and_install(name, baselines_dir, fetch=fetch, environ=environ)
    if installed is None:
        log(
            f"baselines: set {name} is already in {baselines_dir.parent.name}/{baselines_dir.name}; "
            "nothing downloaded (pass --force to download it again)"
        )
        return held
    log(_fetched_line(installed, baselines_dir))
    return installed.pointer


def _png_digests(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*.png")
        if path.is_file()
    }


def diff_trees(previous_dir: Path, new_dir: Path) -> TreeDiff:
    """
    Count the PNG files that differ between two copies of the baselines; the stamp and other files are ignored.

    Args:
        previous_dir: The older copy, e.g. `baselines.prev`; a missing directory counts as empty.
        new_dir: The newer copy.

    Returns a TreeDiff of the paths in both whose sha256 differs (changed),
    the paths only in `new_dir` (added), and those only in `previous_dir` (removed).
    """
    before, after = _png_digests(previous_dir), _png_digests(new_dir)
    return TreeDiff(
        changed=sum(1 for path in before.keys() & after.keys() if before[path] != after[path]),
        added=len(after.keys() - before.keys()),
        removed=len(before.keys() - after.keys()),
    )


def adopt_set(
    name: str,
    pointer_path: Path = POINTER_PATH,
    baselines_dir: Path = BASELINES_DIR,
    *,
    fetch: Callable[[str], bytes] = fetch_bytes,
    log: Callable[[str], None] = _log_to_stderr,
    lock: Callable[[Path], AbstractContextManager] = _file_lock,
    environ: Mapping[str, str] | None = None,
) -> Adoption:
    """
    Make a set the committed one: write the pointer file naming it and its sha256.

    If the working copy's stamp already names the set (after `install_set`,
    say), its hash is reused and nothing is downloaded; otherwise the set is
    downloaded and installed as `install_set` does, and its hash computed. The
    pointer is written under the lock, so a pytest run started meanwhile waits
    and then finds the working copy current. A pointer file that does not parse
    is overwritten. `PERMA_BASELINES_FETCH` is ignored.

    Args:
        name: The set, `YYYY-MM-DD-<slug>`.
        pointer_path: The pointer file; `POINTER_PATH` by default.
        baselines_dir: The working copy; `BASELINES_DIR` by default.
        fetch, log, lock, environ: As for `ensure_set`; `log` gets the line of a download.

    Returns an Adoption: the pointer written, or `already_adopted` when the
    pointer already named the set and the stamp held it (nothing is written),
    plus the PNG changes from `baselines.prev` when there is one.

    Raises:
        SetNotFoundError: If the set had to be downloaded and is not at its URL.
        BaselineSetError: If the name is malformed, the download fails, or the
            tarball is unsafe or unreadable; the pointer and working copy are then untouched.
    """
    _validate_set_name(name)
    with lock(_sibling(baselines_dir, ".lock")):
        try:
            committed = read_pointer(pointer_path)
        except BaselineSetError:
            committed = None  # a broken pointer is one reason to adopt
        held = read_stamp(baselines_dir)
        installed = None
        if held is not None and held.name == name:
            if committed == held:
                return Adoption(held, already_adopted=True)
            pointer = held
        else:
            installed = _fetch_and_install(name, baselines_dir, fetch=fetch, environ=environ)
            pointer = installed.pointer
        pointer_path.write_text(format_pointer(pointer), encoding="utf-8")
        previous_dir = _sibling(baselines_dir, ".prev")
        if previous_dir.is_dir():
            adoption = Adoption(pointer, previous_dir=previous_dir, previous_set=read_stamp(previous_dir),
                                changes=diff_trees(previous_dir, baselines_dir))
        else:
            adoption = Adoption(pointer, previous_dir=previous_dir)
    if installed is not None:
        log(_fetched_line(installed, baselines_dir))
    return adoption
