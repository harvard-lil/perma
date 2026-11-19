"""Unit tests for baseline-set fetching; in-memory tarballs and a fake fetcher, no network, browser or database."""

import email.message
import gzip
import hashlib
import io
import tarfile
import urllib.error
import urllib.request

import pytest

from functional_tests import baseline_sets
from functional_tests.baseline_sets import (
    Adoption,
    BaselineSetError,
    Pointer,
    SetNotFoundError,
    Status,
    TreeDiff,
    adopt_set,
    diff_trees,
    ensure_set,
    extract_set,
    format_pointer,
    install_set,
    parse_pointer,
    read_pointer,
    read_stamp,
    set_not_found_message,
    set_tag,
    set_url,
    write_stamp,
)


def _asset_url(name, base=baseline_sets.DEFAULT_BASE_URL):
    """Where a set is published: the `<tag>.tar` asset of the release on tag `baselines-<name>`."""
    return f"{base}baselines-{name}/baselines-{name}.tar"


NAME = "2026-10-28-bootstrap3"
OLD_NAME = "2026-09-01-before"
HASH = "a" * 64
URL = _asset_url(NAME)


@pytest.fixture(autouse=True)
def no_network_and_clean_env(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("unit tests must not open URLs")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    monkeypatch.delenv(baseline_sets.FETCH_ENV, raising=False)
    monkeypatch.delenv(baseline_sets.URL_ENV, raising=False)


def _tar(files=None, *, dirs=(), prefix=""):
    """An uncompressed tarball of `files` ({path: bytes}) plus directory members."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name in dirs:
            info = tarfile.TarInfo(prefix + name)
            info.type = tarfile.DIRTYPE
            info.mode = 0o755
            archive.addfile(info)
        for name, content in (files or {}).items():
            info = tarfile.TarInfo(prefix + name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def _tar_with_member(name, kind, linkname=""):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        archive.addfile(tarfile.TarInfo("chromium/fine.png"), io.BytesIO(b""))
        info = tarfile.TarInfo(name)
        info.type = kind
        info.linkname = linkname
        archive.addfile(info, io.BytesIO(b"") if kind == tarfile.REGTYPE else None)
    return buffer.getvalue()


NEW_SET = _tar({"chromium/test_x/test_y/page.png": b"new", "firefox/test_x/test_y/page.png": b"new-ff"}, dirs=("chromium",))


def _pointer_for(data, name=NAME):
    return Pointer(name, hashlib.sha256(data).hexdigest())


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


class FakeLock:
    """Records the lock path and whether it is held; `on_acquire` runs once the lock is taken."""

    def __init__(self, on_acquire=None):
        self.paths = []
        self.held = False
        self.on_acquire = on_acquire

    def __call__(self, path):
        self.paths.append(path)
        return self

    def __enter__(self):
        self.held = True
        if self.on_acquire:
            self.on_acquire()

    def __exit__(self, *exc):
        self.held = False


@pytest.fixture
def paths(tmp_path):
    return tmp_path / "BASELINE_SET", tmp_path / "baselines"


def _ensure(paths, fetch, lock=None, log=None):
    pointer_path, baselines_dir = paths
    return ensure_set(pointer_path, baselines_dir, fetch=fetch, log=log or (lambda line: None), lock=lock or FakeLock())


def _commit_pointer(paths, pointer):
    paths[0].write_text(format_pointer(pointer))


def _old_copy(baselines_dir, name=OLD_NAME, content=b"old"):
    page = baselines_dir / "chromium" / "test_x" / "test_y" / "page.png"
    page.parent.mkdir(parents=True)
    page.write_bytes(content)
    write_stamp(baselines_dir, Pointer(name, "b" * 64))
    return page


# Pointer format


@pytest.mark.parametrize("text", [
    f"set={NAME}\nsha256={HASH}\n",
    f"sha256={HASH}\nset={NAME}",
    f"# the set CI renders\n\nset = {NAME}\n  # its hash\nsha256={HASH}\n\n",
])
def test_pointer_parses_in_either_order_with_comments_and_blank_lines(text):
    assert parse_pointer(text, "BASELINE_SET") == Pointer(NAME, HASH)


def test_pointer_round_trips_through_its_format():
    assert parse_pointer(format_pointer(Pointer(NAME, HASH)), "x") == Pointer(NAME, HASH)


@pytest.mark.parametrize("text, message", [
    (f"set={NAME}\nsha256={HASH}\nlatest=yes\n", r"line 3: expected `set=<name>` or `sha256=<hex>`"),
    (f"set={NAME}\n{HASH}\n", r"line 2: expected"),
    (f"set={NAME}\nset={NAME}\nsha256={HASH}\n", r"line 2: `set` is given twice"),
    (f"set={NAME}\n", r"no `sha256=` line"),
    ("", r"no `set=` or `sha256=` line"),
    (f"set={NAME}\nsha256={HASH.upper()}\n", r"is not 64 lowercase hex digits"),
    (f"set={NAME}\nsha256={HASH[:-1]}\n", r"is not 64 lowercase hex digits"),
    (f"set=bootstrap3\nsha256={HASH}\n", r"is not YYYY-MM-DD-<slug>"),
])
def test_malformed_pointer_raises_naming_the_file(text, message):
    with pytest.raises(BaselineSetError, match=message) as failure:
        parse_pointer(text, "functional_tests/BASELINE_SET")
    assert str(failure.value).startswith("functional_tests/BASELINE_SET")


@pytest.mark.parametrize("name", ["2026-10-28-bootstrap3", "2026-10-28-a", "2026-10-28-0-firefox-fix"])
def test_valid_set_names_are_accepted(name):
    assert Pointer(name, HASH).name == name


@pytest.mark.parametrize("name", [
    "bootstrap3",
    "2026-10-28",
    "2026-10-28-",
    "2026-10-28--leading-hyphen",
    "2026-10-28-Bootstrap3",
    "2026-10-28-a/b",
    "2026-10-28-../../etc",
    "2026-10-28-a.tar",
    "2026-10-28-a\n",
    "２０２６-10-28-fullwidth-digits",
])
def test_malformed_set_names_are_refused_before_any_url_is_built(name):
    with pytest.raises(BaselineSetError, match="is not YYYY-MM-DD-<slug>"):
        set_url(name)


def test_unreadable_stamp_counts_as_no_stamp(tmp_path):
    (tmp_path / baseline_sets.STAMP_NAME).write_text("garbage\n")

    assert read_stamp(tmp_path) is None
    assert read_stamp(tmp_path / "missing") is None


# URLs


@pytest.mark.parametrize("name", [NAME, "2026-10-28-a", "2026-10-28-0-firefox-fix"])
def test_set_tag_prefixes_the_name(name):
    assert set_tag(name) == f"baselines-{name}"


@pytest.mark.parametrize("name", ["bootstrap3", f"baselines-{NAME}", "2026-10-28-a/b", "2026-10-28-Bootstrap3", ""])
def test_set_tag_refuses_a_malformed_name(name):
    with pytest.raises(BaselineSetError, match="is not YYYY-MM-DD-<slug>"):
        set_tag(name)


def test_set_url_uses_the_default_base():
    assert set_url(NAME) == (
        f"https://github.com/harvard-lil/perma/releases/download/baselines-{NAME}/baselines-{NAME}.tar"
    )
    assert set_url(NAME) == URL


@pytest.mark.parametrize("base", [
    "https://github.com/example/perma/releases/download",
    "https://github.com/example/perma/releases/download/",
    "https://github.com/example/perma/releases/download//",
])
def test_set_url_takes_the_base_from_the_environment_with_one_slash(monkeypatch, base):
    monkeypatch.setenv(baseline_sets.URL_ENV, base)

    assert set_url(NAME) == f"https://github.com/example/perma/releases/download/baselines-{NAME}/baselines-{NAME}.tar"


def test_set_url_names_the_tag_as_the_release_and_the_asset():
    *_, release, asset = set_url(NAME).split("/")

    assert release == set_tag(NAME)
    assert asset == f"{set_tag(NAME)}.tar"


def test_ensure_set_fetches_from_the_environment_base(monkeypatch, paths):
    monkeypatch.setenv(baseline_sets.URL_ENV, "https://example.org/sets")
    _commit_pointer(paths, _pointer_for(NEW_SET))
    fetch = FakeFetch(NEW_SET)

    _ensure(paths, fetch)

    assert fetch.urls == [f"https://example.org/sets/baselines-{NAME}/baselines-{NAME}.tar"]


# ensure_set: when nothing happens


def test_absent_pointer_is_a_no_op(paths):
    _, baselines_dir = paths
    page = _old_copy(baselines_dir)
    fetch, lock = FakeFetch(NEW_SET), FakeLock()

    outcome = _ensure(paths, fetch, lock)

    assert outcome.status is Status.NO_POINTER
    assert outcome.directory == baselines_dir
    assert fetch.urls == [] and lock.paths == []
    assert page.read_bytes() == b"old"


@pytest.mark.parametrize("value", ["0", "false", "No", " FALSE "])
def test_disabled_fetch_is_a_no_op_even_with_a_stale_stamp(monkeypatch, paths, value):
    monkeypatch.setenv(baseline_sets.FETCH_ENV, value)
    _, baselines_dir = paths
    page = _old_copy(baselines_dir)
    _commit_pointer(paths, _pointer_for(NEW_SET))
    fetch = FakeFetch(NEW_SET)

    outcome = _ensure(paths, fetch)

    assert outcome.status is Status.DISABLED
    assert fetch.urls == []
    assert page.read_bytes() == b"old"
    assert read_stamp(baselines_dir).name == OLD_NAME


def test_matching_stamp_does_not_fetch(paths):
    _, baselines_dir = paths
    pointer = _pointer_for(NEW_SET)
    _commit_pointer(paths, pointer)
    baselines_dir.mkdir()
    write_stamp(baselines_dir, pointer)
    fetch = FakeFetch(NEW_SET)

    outcome = _ensure(paths, fetch)

    assert outcome.status is Status.CURRENT
    assert outcome.pointer == pointer
    assert fetch.urls == []


# ensure_set: fetching


def test_stale_stamp_fetches_verifies_extracts_stamps_and_keeps_the_previous_copy(paths):
    _, baselines_dir = paths
    _old_copy(baselines_dir)
    older_prev = baselines_dir.with_name("baselines.prev")
    (older_prev / "stale").mkdir(parents=True)
    pointer = _pointer_for(NEW_SET)
    _commit_pointer(paths, pointer)
    fetch, logged = FakeFetch(NEW_SET), []

    outcome = _ensure(paths, fetch, log=logged.append)

    assert outcome.status is Status.FETCHED
    assert outcome.pointer == pointer
    assert fetch.urls == [URL]
    assert (baselines_dir / "chromium/test_x/test_y/page.png").read_bytes() == b"new"
    assert (baselines_dir / "firefox/test_x/test_y/page.png").read_bytes() == b"new-ff"
    assert read_stamp(baselines_dir) == pointer
    assert (older_prev / "chromium/test_x/test_y/page.png").read_bytes() == b"old"
    assert read_stamp(older_prev).name == OLD_NAME
    assert not (older_prev / "stale").exists()
    assert not baselines_dir.with_name("baselines.tmp").exists()
    assert logged == [
        f"baselines: fetched set {NAME} (2 files, {len(NEW_SET) / 1000:.0f} kB) into {baselines_dir.parent.name}/baselines; "
        "previous copy kept at baselines.prev"
    ]


def test_first_fetch_without_a_working_copy_keeps_no_previous_copy(paths):
    _, baselines_dir = paths
    _commit_pointer(paths, _pointer_for(NEW_SET))
    logged = []

    _ensure(paths, FakeFetch(NEW_SET), log=logged.append)

    assert (baselines_dir / "chromium/test_x/test_y/page.png").is_file()
    assert not baselines_dir.with_name("baselines.prev").exists()
    assert "previous copy" not in logged[0]


def test_second_call_after_a_fetch_is_a_no_op(paths):
    _commit_pointer(paths, _pointer_for(NEW_SET))
    fetch = FakeFetch(NEW_SET)

    first = _ensure(paths, fetch)
    second = _ensure(paths, fetch)

    assert (first.status, second.status) == (Status.FETCHED, Status.CURRENT)
    assert fetch.urls == [URL]


def test_leftover_staging_directory_from_a_killed_run_is_discarded(paths):
    _, baselines_dir = paths
    staging = baselines_dir.with_name("baselines.tmp")
    (staging / "chromium").mkdir(parents=True)
    (staging / "chromium" / "half-written.png").write_bytes(b"x")
    _commit_pointer(paths, _pointer_for(NEW_SET))

    _ensure(paths, FakeFetch(NEW_SET))

    assert not staging.exists()
    assert not (baselines_dir / "chromium" / "half-written.png").exists()


def test_hash_mismatch_raises_and_leaves_the_working_copy_and_stamp_alone(paths):
    pointer_path, baselines_dir = paths
    page = _old_copy(baselines_dir)
    _commit_pointer(paths, Pointer(NAME, HASH))

    with pytest.raises(BaselineSetError, match="sha256") as failure:
        _ensure(paths, FakeFetch(NEW_SET))

    message = str(failure.value)
    assert hashlib.sha256(NEW_SET).hexdigest() in message and HASH in message and str(pointer_path) in message
    assert page.read_bytes() == b"old"
    assert read_stamp(baselines_dir).name == OLD_NAME
    assert not baselines_dir.with_name("baselines.prev").exists()
    assert not baselines_dir.with_name("baselines.tmp").exists()


def test_missing_set_names_the_set_the_url_and_the_likely_causes(paths):
    pointer_path, _ = paths
    _commit_pointer(paths, _pointer_for(NEW_SET))
    # Built the way fetch_bytes builds it, so the fake raises exactly what a real 404 would.
    not_found = urllib.error.HTTPError(URL, 404, "Not Found", email.message.Message(), None)
    fetch = FakeFetch(baseline_sets._http_failure(URL, not_found))

    with pytest.raises(SetNotFoundError) as failure:
        _ensure(paths, fetch)

    message = str(failure.value)
    assert NAME in message and URL in message and str(pointer_path) in message
    assert f"no release was published on tag baselines-{NAME}" in message
    assert "still a draft" in message and baseline_sets.URL_ENV in message


def test_other_fetch_failures_propagate_unchanged(paths):
    _commit_pointer(paths, _pointer_for(NEW_SET))
    error = BaselineSetError("baselines: could not download it: offline")

    with pytest.raises(BaselineSetError) as failure:
        _ensure(paths, FakeFetch(error))

    assert failure.value is error


# HTTP error translation (the default fetcher's mapping; no request is made)


def _http_error(code, reason="Error"):
    return urllib.error.HTTPError(URL, code, reason, email.message.Message(), None)


def test_http_404_means_no_such_set():
    error = baseline_sets._http_failure(URL, _http_error(404, "Not Found"))

    assert type(error) is SetNotFoundError
    assert URL in str(error)
    assert "baselines.fetch" not in str(error)


@pytest.mark.parametrize("code", [403, 429, 500])
def test_other_http_errors_give_the_status_and_the_way_to_run_offline(code):
    error = baseline_sets._http_failure(URL, _http_error(code, "Bad"))

    assert type(error) is BaselineSetError
    assert f"HTTP {code} Bad" in str(error)
    assert f"{baseline_sets.FETCH_ENV}=0" in str(error)
    assert "`d invoke baselines.fetch`" in str(error)


# Extraction


def test_extract_set_accepts_dot_slash_names_as_gnu_tar_writes_them(tmp_path):
    data = _tar({"chromium/a/b/page.png": b"png"}, dirs=(".", "chromium"), prefix="./")

    assert extract_set(data, tmp_path) == 1
    assert (tmp_path / "chromium/a/b/page.png").read_bytes() == b"png"


@pytest.mark.parametrize("name", ["../escaped.png", "chromium/../../escaped.png", "/tmp/absolute.png"])
def test_unsafe_paths_are_refused_before_anything_is_extracted(tmp_path, name):
    destination = tmp_path / "out"
    destination.mkdir()

    with pytest.raises(BaselineSetError, match="only paths relative"):
        extract_set(_tar_with_member(name, tarfile.REGTYPE), destination)

    assert list(destination.iterdir()) == []
    assert not (tmp_path / "escaped.png").exists()


@pytest.mark.parametrize("kind, linkname", [
    (tarfile.SYMTYPE, "fine.png"),
    (tarfile.LNKTYPE, "chromium/fine.png"),
    (tarfile.FIFOTYPE, ""),
    (tarfile.CHRTYPE, ""),
])
def test_links_and_special_files_are_refused(tmp_path, kind, linkname):
    with pytest.raises(BaselineSetError, match="not a regular file or directory"):
        extract_set(_tar_with_member("chromium/link.png", kind, linkname), tmp_path)

    assert list(tmp_path.iterdir()) == []


def test_unsafe_set_leaves_the_working_copy_and_no_staging(paths):
    _, baselines_dir = paths
    page = _old_copy(baselines_dir)
    data = _tar_with_member("../escaped.png", tarfile.REGTYPE)
    _commit_pointer(paths, _pointer_for(data))

    with pytest.raises(BaselineSetError, match="only paths relative"):
        _ensure(paths, FakeFetch(data))

    assert page.read_bytes() == b"old"
    assert read_stamp(baselines_dir).name == OLD_NAME
    assert not baselines_dir.with_name("baselines.tmp").exists()


@pytest.mark.parametrize("data", [b"", b"not a tarball", gzip.compress(_tar({"chromium/a.png": b"x"}))])
def test_unreadable_or_compressed_tarball_raises(tmp_path, data):
    with pytest.raises(BaselineSetError, match="cannot be extracted"):
        extract_set(data, tmp_path)


# Locking


def test_lock_is_held_around_the_stamp_check_and_the_fetch(paths):
    _, baselines_dir = paths
    _commit_pointer(paths, _pointer_for(NEW_SET))
    lock = FakeLock()
    held_during_fetch = []

    def fetch(url):
        held_during_fetch.append(lock.held)
        return NEW_SET

    _ensure(paths, fetch, lock)

    assert lock.paths == [baselines_dir.with_name("baselines.lock")]
    assert held_during_fetch == [True]
    assert not lock.held


def test_stamp_is_read_after_the_lock_is_acquired(paths):
    """A worker that waited on the lock finds the set another worker installed, and does not fetch."""
    _, baselines_dir = paths
    pointer = _pointer_for(NEW_SET)
    _commit_pointer(paths, pointer)

    def other_worker_installs_the_set():
        baselines_dir.mkdir()
        write_stamp(baselines_dir, pointer)

    fetch = FakeFetch(NEW_SET)
    outcome = _ensure(paths, fetch, FakeLock(on_acquire=other_worker_installs_the_set))

    assert outcome.status is Status.CURRENT
    assert fetch.urls == []


def test_default_lock_takes_a_file_lock_beside_the_working_copy(paths):
    pytest.importorskip("filelock")
    pointer_path, baselines_dir = paths
    _commit_pointer(paths, _pointer_for(NEW_SET))

    ensure_set(pointer_path, baselines_dir, fetch=FakeFetch(NEW_SET), log=lambda line: None)

    assert baselines_dir.with_name("baselines.lock").is_file()


# Shared by the P2 tests below


def _quiet(line):
    pass


def _not_found(url=URL):
    """What the default fetcher raises for HTTP 404, built the way fetch_bytes builds it."""
    return baseline_sets._http_failure(url, urllib.error.HTTPError(url, 404, "Not Found", email.message.Message(), None))


CANDIDATE = "2026-11-02-candidate"
CANDIDATE_URL = _asset_url(CANDIDATE)
CANDIDATE_SET = _tar({"chromium/test_x/test_y/page.png": b"candidate", "webkit/test_x/test_y/page.png": b"wk"})


# ensure_set(force=True)


def test_force_fetches_even_when_the_stamp_matches(paths):
    _, baselines_dir = paths
    pointer = _pointer_for(NEW_SET)
    _commit_pointer(paths, pointer)
    _ensure(paths, FakeFetch(NEW_SET))
    fetch, logged = FakeFetch(NEW_SET), []

    outcome = ensure_set(*paths, fetch=fetch, log=logged.append, lock=FakeLock(), force=True)

    assert outcome.status is Status.FETCHED
    assert fetch.urls == [URL]
    assert read_stamp(baselines_dir) == pointer
    assert read_stamp(baselines_dir.with_name("baselines.prev")) == pointer
    assert logged[0].endswith("; previous copy kept at baselines.prev")


def test_force_still_checks_the_hash(paths):
    _, baselines_dir = paths
    _commit_pointer(paths, Pointer(NAME, HASH))
    baselines_dir.mkdir()
    write_stamp(baselines_dir, Pointer(NAME, HASH))

    with pytest.raises(BaselineSetError, match="sha256"):
        ensure_set(*paths, fetch=FakeFetch(NEW_SET), log=_quiet, lock=FakeLock(), force=True)

    assert read_stamp(baselines_dir) == Pointer(NAME, HASH)


@pytest.mark.parametrize("disabled", [True, False])
def test_force_does_nothing_when_disabled_or_without_a_pointer(monkeypatch, paths, disabled):
    if disabled:
        monkeypatch.setenv(baseline_sets.FETCH_ENV, "0")
        _commit_pointer(paths, _pointer_for(NEW_SET))
    fetch = FakeFetch(NEW_SET)

    outcome = ensure_set(*paths, fetch=fetch, log=_quiet, lock=FakeLock(), force=True)

    assert outcome.status is (Status.DISABLED if disabled else Status.NO_POINTER)
    assert fetch.urls == []


# Messages that name the invoke commands


def test_download_failure_names_the_retry_command_and_the_offline_switch(monkeypatch):
    def offline(*args, **kwargs):
        raise urllib.error.URLError("no route to host")

    monkeypatch.setattr(urllib.request, "urlopen", offline)

    with pytest.raises(BaselineSetError) as failure:
        baseline_sets.fetch_bytes(URL)

    message = str(failure.value)
    assert f"could not download {URL}: no route to host" in message
    assert "`d invoke baselines.fetch`" in message and f"{baseline_sets.FETCH_ENV}=0" in message


def test_hash_mismatch_names_the_adopt_command(paths):
    _commit_pointer(paths, Pointer(NAME, HASH))

    with pytest.raises(BaselineSetError) as failure:
        _ensure(paths, FakeFetch(NEW_SET))

    assert f"`d invoke baselines.adopt {NAME}` rewrites the pointer from a fresh download" in str(failure.value)


def test_missing_set_from_the_pointer_raises_the_public_message(paths):
    pointer_path, _ = paths
    _commit_pointer(paths, _pointer_for(NEW_SET))

    with pytest.raises(SetNotFoundError) as failure:
        _ensure(paths, FakeFetch(_not_found()))

    assert str(failure.value) == set_not_found_message(NAME, URL, pointer_path)


def test_set_not_found_message_for_a_pointer_names_the_pointer(tmp_path):
    message = set_not_found_message(NAME, URL, tmp_path / "BASELINE_SET")

    assert f"set {NAME!r}, named in {tmp_path / 'BASELINE_SET'}, is not at {URL} (HTTP 404)" in message
    assert f"the pointer names a set for which no release was published on tag baselines-{NAME}" in message
    assert "still a draft" in message
    assert f"{baseline_sets.URL_ENV} points at the wrong repository" in message


def test_set_not_found_message_for_a_name_points_to_the_catalog():
    message = set_not_found_message(NAME, URL)

    assert message.startswith(f"baselines: set {NAME!r} is not at {URL} (HTTP 404)")
    assert f"no release was published for tag baselines-{NAME}" in message
    assert "`gh release list` or `git tag -l 'baselines-*'`" in message
    assert "still a draft" in message
    assert f"{baseline_sets.URL_ENV} points at the wrong repository" in message


# install_set


def test_install_set_installs_a_named_set_and_stamps_its_actual_hash(paths):
    _, baselines_dir = paths
    _old_copy(baselines_dir)
    lock, logged = FakeLock(), []
    held_during_fetch = []

    def fetch(url):
        held_during_fetch.append((url, lock.held))
        return NEW_SET

    pointer = install_set(NAME, baselines_dir, fetch=fetch, log=logged.append, lock=lock)

    assert pointer == _pointer_for(NEW_SET)
    assert held_during_fetch == [(URL, True)]
    assert lock.paths == [baselines_dir.with_name("baselines.lock")]
    assert read_stamp(baselines_dir) == pointer
    assert (baselines_dir / "chromium/test_x/test_y/page.png").read_bytes() == b"new"
    assert read_stamp(baselines_dir.with_name("baselines.prev")).name == OLD_NAME
    assert not baselines_dir.with_name("baselines.tmp").exists()
    assert logged == [
        f"baselines: fetched set {NAME} (2 files, {len(NEW_SET) / 1000:.0f} kB) into {baselines_dir.parent.name}/baselines; "
        "previous copy kept at baselines.prev"
    ]


def test_install_set_skips_a_set_the_stamp_already_names(paths):
    _, baselines_dir = paths
    fetch, logged = FakeFetch(NEW_SET), []
    first = install_set(NAME, baselines_dir, fetch=fetch, log=_quiet, lock=FakeLock())
    lock = FakeLock()

    second = install_set(NAME, baselines_dir, fetch=fetch, log=logged.append, lock=lock)

    assert second == first == read_stamp(baselines_dir)
    assert fetch.urls == [URL]
    assert lock.paths == [baselines_dir.with_name("baselines.lock")]
    assert not baselines_dir.with_name("baselines.prev").exists()
    assert logged == [
        f"baselines: set {NAME} is already in {baselines_dir.parent.name}/baselines; "
        "nothing downloaded (pass --force to download it again)"
    ]


def test_install_set_with_force_downloads_a_set_the_stamp_already_names(paths):
    _, baselines_dir = paths
    fetch, logged = FakeFetch(NEW_SET), []
    install_set(NAME, baselines_dir, fetch=fetch, log=_quiet, lock=FakeLock())

    pointer = install_set(NAME, baselines_dir, fetch=fetch, log=logged.append, lock=FakeLock(), force=True)

    assert pointer == _pointer_for(NEW_SET)
    assert fetch.urls == [URL, URL]
    assert read_stamp(baselines_dir.with_name("baselines.prev")) == pointer
    assert logged[0].endswith("; previous copy kept at baselines.prev")


def test_install_set_ignores_the_fetch_switch(monkeypatch, paths):
    monkeypatch.setenv(baseline_sets.FETCH_ENV, "0")
    _, baselines_dir = paths
    fetch = FakeFetch(NEW_SET)

    install_set(NAME, baselines_dir, fetch=fetch, log=_quiet, lock=FakeLock())

    assert fetch.urls == [URL]
    assert read_stamp(baselines_dir) == _pointer_for(NEW_SET)


@pytest.mark.parametrize("adopting", [False, True])
def test_malformed_name_is_refused_before_locking_or_fetching(paths, adopting):
    pointer_path, baselines_dir = paths
    fetch, lock = FakeFetch(NEW_SET), FakeLock()

    with pytest.raises(BaselineSetError, match="is not YYYY-MM-DD-<slug>"):
        if adopting:
            adopt_set("bootstrap3", pointer_path, baselines_dir, fetch=fetch, log=_quiet, lock=lock)
        else:
            install_set("bootstrap3", baselines_dir, fetch=fetch, log=_quiet, lock=lock)

    assert fetch.urls == [] and lock.paths == []
    assert not pointer_path.exists()


def test_install_set_reports_a_missing_set_by_name_and_leaves_the_working_copy(paths):
    _, baselines_dir = paths
    page = _old_copy(baselines_dir)

    with pytest.raises(SetNotFoundError) as failure:
        install_set(NAME, baselines_dir, fetch=FakeFetch(_not_found()), log=_quiet, lock=FakeLock())

    assert str(failure.value) == set_not_found_message(NAME, URL)
    assert page.read_bytes() == b"old"
    assert read_stamp(baselines_dir).name == OLD_NAME


# diff_trees


def _write_tree(root, files):
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def test_diff_trees_counts_changed_added_and_removed_pngs_by_path_and_content(tmp_path):
    before, after = tmp_path / "before", tmp_path / "after"
    _write_tree(before, {
        "chromium/a/same.png": b"same",
        "chromium/a/edited.png": b"old",
        "firefox/b/gone.png": b"x",
        "webkit/c/moved.png": b"m",
    })
    _write_tree(after, {
        "chromium/a/same.png": b"same",
        "chromium/a/edited.png": b"new",
        "firefox/b/new.png": b"x",
        "webkit/d/moved.png": b"m",
    })

    assert diff_trees(before, after) == TreeDiff(changed=1, added=2, removed=2)


def test_diff_trees_ignores_the_stamp_and_files_that_are_not_pngs(tmp_path):
    before, after = tmp_path / "before", tmp_path / "after"
    _write_tree(before, {"chromium/a/page.png": b"same", "chromium/a/notes.txt": b"one"})
    _write_tree(after, {"chromium/a/page.png": b"same", "chromium/a/notes.txt": b"two", "chromium/a/extra.json": b"{}"})
    write_stamp(before, Pointer(OLD_NAME, "b" * 64))
    write_stamp(after, Pointer(NAME, HASH))

    assert diff_trees(before, after) == TreeDiff(changed=0, added=0, removed=0)


def test_diff_trees_treats_a_missing_directory_as_empty(tmp_path):
    _write_tree(tmp_path / "after", {"chromium/a/page.png": b"x"})

    assert diff_trees(tmp_path / "missing", tmp_path / "after") == TreeDiff(changed=0, added=1, removed=0)


# adopt_set


def _adopt(paths, name, fetch, lock=None, log=None):
    pointer_path, baselines_dir = paths
    return adopt_set(name, pointer_path, baselines_dir, fetch=fetch, log=log or _quiet, lock=lock or FakeLock())


def test_adopt_reuses_the_stamp_of_a_previewed_set_without_downloading(paths):
    pointer_path, baselines_dir = paths
    _commit_pointer(paths, _pointer_for(NEW_SET))
    _ensure(paths, FakeFetch(NEW_SET))
    candidate = install_set(CANDIDATE, baselines_dir, fetch=FakeFetch(CANDIDATE_SET), log=_quiet, lock=FakeLock())
    fetch, logged = FakeFetch(CANDIDATE_SET), []

    adoption = _adopt(paths, CANDIDATE, fetch, log=logged.append)

    assert fetch.urls == [] and logged == []
    assert adoption.pointer == candidate == _pointer_for(CANDIDATE_SET, CANDIDATE)
    assert not adoption.already_adopted
    assert pointer_path.read_text() == format_pointer(candidate)
    assert adoption.previous_dir == baselines_dir.with_name("baselines.prev")
    assert adoption.previous_set == _pointer_for(NEW_SET)
    # chromium's page changed, webkit's is new, firefox's is gone.
    assert adoption.changes == TreeDiff(changed=1, added=1, removed=1)


def test_adopt_downloads_a_set_the_working_copy_does_not_hold(paths):
    pointer_path, baselines_dir = paths
    _old_copy(baselines_dir)
    fetch, logged = FakeFetch(CANDIDATE_SET), []

    adoption = _adopt(paths, CANDIDATE, fetch, log=logged.append)

    assert fetch.urls == [CANDIDATE_URL]
    assert adoption.pointer == _pointer_for(CANDIDATE_SET, CANDIDATE)
    assert read_stamp(baselines_dir) == adoption.pointer
    assert pointer_path.read_text() == format_pointer(adoption.pointer)
    assert adoption.previous_set.name == OLD_NAME
    assert adoption.changes == TreeDiff(changed=1, added=1, removed=0)
    assert len(logged) == 1 and logged[0].startswith(f"baselines: fetched set {CANDIDATE} (2 files, ")


def test_adopt_without_a_previous_copy_has_nothing_to_compare(paths):
    pointer_path, baselines_dir = paths

    adoption = _adopt(paths, CANDIDATE, FakeFetch(CANDIDATE_SET))

    assert adoption.previous_dir == baselines_dir.with_name("baselines.prev")
    assert adoption.changes is None and adoption.previous_set is None
    assert read_pointer(pointer_path) == adoption.pointer


def test_adopting_the_committed_and_current_set_is_a_no_op(paths):
    pointer_path, _ = paths
    pointer = _pointer_for(NEW_SET)
    pointer_path.write_text(f"# reviewed in the capture report\n{format_pointer(pointer)}")
    _ensure(paths, FakeFetch(NEW_SET))
    fetch = FakeFetch(NEW_SET)

    adoption = _adopt(paths, NAME, fetch)

    assert adoption == Adoption(pointer, already_adopted=True)
    assert fetch.urls == []
    assert pointer_path.read_text().startswith("# reviewed in the capture report")


def test_adopt_rewrites_a_pointer_whose_hash_is_wrong_from_a_fresh_download(paths):
    """The remedy the hash-mismatch message names."""
    pointer_path, baselines_dir = paths
    _old_copy(baselines_dir)
    _commit_pointer(paths, Pointer(NAME, HASH))
    with pytest.raises(BaselineSetError, match="sha256"):
        _ensure(paths, FakeFetch(NEW_SET))

    adoption = _adopt(paths, NAME, FakeFetch(NEW_SET))

    assert adoption.pointer == _pointer_for(NEW_SET)
    assert read_pointer(pointer_path) == adoption.pointer
    assert _ensure(paths, FakeFetch(NEW_SET)).status is Status.CURRENT


def test_adopt_overwrites_a_pointer_that_does_not_parse(paths):
    pointer_path, _ = paths
    pointer_path.write_text("set=bootstrap3\n")

    adoption = _adopt(paths, NAME, FakeFetch(NEW_SET))

    assert read_pointer(pointer_path) == adoption.pointer


def test_adopt_of_a_missing_set_leaves_the_pointer_and_working_copy_alone(paths):
    pointer_path, baselines_dir = paths
    page = _old_copy(baselines_dir)
    committed = _pointer_for(NEW_SET)
    _commit_pointer(paths, committed)

    with pytest.raises(SetNotFoundError) as failure:
        _adopt(paths, CANDIDATE, FakeFetch(_not_found(CANDIDATE_URL)))

    assert str(failure.value) == set_not_found_message(CANDIDATE, CANDIDATE_URL)
    assert read_pointer(pointer_path) == committed
    assert page.read_bytes() == b"old"


def test_adopt_ignores_the_fetch_switch(monkeypatch, paths):
    monkeypatch.setenv(baseline_sets.FETCH_ENV, "0")

    adoption = _adopt(paths, CANDIDATE, FakeFetch(CANDIDATE_SET))

    assert read_pointer(paths[0]) == adoption.pointer


def test_adopt_writes_the_pointer_before_releasing_the_lock(paths):
    pointer_path, baselines_dir = paths
    written_at_release = []

    class RecordingLock(FakeLock):
        def __exit__(self, *exc):
            written_at_release.append(pointer_path.is_file())
            super().__exit__(*exc)

    lock = RecordingLock()
    _adopt(paths, CANDIDATE, FakeFetch(CANDIDATE_SET), lock=lock)

    assert lock.paths == [baselines_dir.with_name("baselines.lock")]
    assert written_at_release == [True]
