"""Characterization of the js-wacz worker's local conversion contract.

`celery_tasks.upload_link_to_internet_archive`'s WACZ conversion shells out to
the `js-wacz` CLI installed from `services/js-wacz/package-lock.json`, so the
only thing standing between an upgrade of that package and a silently different
archive format is what this module pins: the WACZ entry layout, the
`datapackage.json` fields Perma and its playback stack rely on, the integrity
hashes, and the CLI's exit-code behavior on bad input.

These tests invoke the real CLI rather than mocking it. Mocking a subprocess
proves only that Perma calls it; the contract at risk during an upgrade lives on
the other side of that call.
"""

import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from django.conf import settings
import pytest


WARC_FIXTURE = Path(settings.PROJECT_ROOT) / 'perma' / 'tests' / 'assets' / 'new_style_archive' / 'archive.warc.gz'

# The first row of what `Link.get_pages_jsonl()` emits, plus one capture row, so
# the fixture exercises the same shape production writes.
PAGES_JSONL = (
    '{"format": "json-pages-1.0", "id": "pages", "title": "All Pages"}\n'
    '{"url": "https://example.com/", '
    '"title": "High-Fidelity Web Capture of https://example.com/", '
    '"ts": "2024-01-01 00:00:00+00:00"}\n'
)


def _js_wacz_available():
    if not shutil.which('npx') or not Path(settings.JS_WACZ_DIR).is_dir():
        return False
    result = subprocess.run(
        ['npx', 'js-wacz', '--version'],
        capture_output=True, text=True, cwd=settings.JS_WACZ_DIR,
    )
    return result.returncode == 0


pytestmark = pytest.mark.skipif(
    not _js_wacz_available(),
    reason="js-wacz is not installed; run inside the Compose web container",
)


def _run_js_wacz(warc_path, wacz_path, pages_dir):
    """Invoke the CLI exactly as `celery_tasks` does, including the cwd it relies on."""
    return subprocess.run(
        [
            "npx", "js-wacz", "create",
            "-f", str(warc_path),
            "-o", str(wacz_path),
            "-p", str(pages_dir),
        ],
        capture_output=True, text=True, cwd=settings.JS_WACZ_DIR,
    )


@pytest.fixture(scope="module")
def converted_wacz(tmp_path_factory):
    """One conversion of the fixture WARC, laid out the way the celery task lays it out."""
    # The task points -f, -o and -p at a single working directory, so the output
    # WACZ and the source WARC sit alongside the pages file. Reproduce that.
    working_directory = tmp_path_factory.mktemp("js-wacz")
    warc_path = working_directory / "archive.warc.gz"
    shutil.copy(WARC_FIXTURE, warc_path)
    (working_directory / "pages.jsonl").write_text(PAGES_JSONL)
    wacz_path = working_directory / "archive.wacz"

    result = _run_js_wacz(warc_path, wacz_path, working_directory)

    assert result.returncode == 0, f"js-wacz failed: {result.stderr}"
    assert wacz_path.exists()
    return wacz_path


@pytest.fixture(scope="module")
def wacz_zip(converted_wacz):
    with zipfile.ZipFile(converted_wacz) as archive:
        yield archive


@pytest.fixture(scope="module")
def datapackage(wacz_zip):
    return json.loads(wacz_zip.read("datapackage.json"))


def _installed_version():
    """The version actually on disk.

    `services/` is not bind-mounted into the container and the Dockerfile deletes
    both service manifests after `npm ci`, so the installed package is the only
    version record available at test time -- and upgrading js-wacz therefore
    requires rebuilding the web image, not just editing the manifest.
    """
    manifest = Path(settings.JS_WACZ_DIR) / 'node_modules' / '@harvard-lil' / 'js-wacz' / 'package.json'
    return json.loads(manifest.read_text())['version']


def test_cli_version_matches_the_installed_package():
    result = subprocess.run(
        ['npx', 'js-wacz', '--version'],
        capture_output=True, text=True, check=True, cwd=settings.JS_WACZ_DIR,
    )

    assert result.stdout.strip() == _installed_version()


def test_wacz_contains_exactly_the_expected_entries(wacz_zip):
    assert sorted(wacz_zip.namelist()) == [
        "archive/archive.warc.gz",
        "datapackage-digest.json",
        "datapackage.json",
        "indexes/index.cdx",
        "pages/pages.jsonl",
    ]


def test_datapackage_declares_the_wacz_format_perma_playback_expects(datapackage):
    assert datapackage["wacz_version"] == "1.1.1"
    assert datapackage["profile"] == "data-package"
    assert datapackage["software"].startswith("@harvard-lil/js-wacz ")


def test_datapackage_software_string_reports_the_installed_version(datapackage):
    assert datapackage["software"] == f"@harvard-lil/js-wacz {_installed_version()}"


def test_datapackage_lists_every_resource_with_size_and_hash(datapackage):
    resources = {resource["name"]: resource for resource in datapackage["resources"]}

    assert set(resources) == {"index.cdx", "pages.jsonl", "archive.warc.gz"}
    assert resources["index.cdx"]["path"] == "indexes/index.cdx"
    assert resources["pages.jsonl"]["path"] == "pages/pages.jsonl"
    assert resources["archive.warc.gz"]["path"] == "archive/archive.warc.gz"

    for resource in resources.values():
        assert resource["hash"].startswith("sha256:")
        assert resource["bytes"] > 0


def test_in_memory_resource_hash_matches_its_stored_bytes(wacz_zip, datapackage):
    """index.cdx is hashed from a buffer, which takes js-wacz's correct code path."""
    resource = next(r for r in datapackage["resources"] if r["name"] == "index.cdx")
    stored = wacz_zip.read(resource["path"])

    assert resource["hash"] == f"sha256:{hashlib.sha256(stored).hexdigest()}"
    assert resource["bytes"] == len(stored)


def test_file_backed_resource_hashes_are_upstream_double_counted(wacz_zip, datapackage):
    """KNOWN UPSTREAM DEFECT, characterized rather than fixed.

    js-wacz's `sha256()` feeds a file-backed resource into the digest twice: the
    stream's 'data' listener calls `hash.update(chunk)` and the same stream is
    then `pipe()`d into the same hash. Resources read from a path therefore carry
    `sha256(content + content)`, while `bytes` reports the true single length, so
    any consumer validating a WACZ's declared hashes against its payload will
    reject every archive Perma produces. Present in 0.1.5 and unchanged in 0.1.6.

    Asserting the doubled digest -- rather than skipping the check -- means an
    upstream fix breaks this test loudly instead of passing unnoticed.
    """
    for name in ("pages.jsonl", "archive.warc.gz"):
        resource = next(r for r in datapackage["resources"] if r["name"] == name)
        stored = wacz_zip.read(resource["path"])

        assert resource["bytes"] == len(stored)
        assert resource["hash"] != f"sha256:{hashlib.sha256(stored).hexdigest()}"
        assert resource["hash"] == f"sha256:{hashlib.sha256(stored + stored).hexdigest()}"


def test_datapackage_digest_hashes_the_datapackage(wacz_zip):
    digest = json.loads(wacz_zip.read("datapackage-digest.json"))
    datapackage_bytes = wacz_zip.read("datapackage.json")

    assert digest["path"] == "datapackage.json"
    assert digest["hash"] == f"sha256:{hashlib.sha256(datapackage_bytes).hexdigest()}"


def test_datapackage_carries_creation_timestamps(datapackage):
    # Values are per-run, so pin only that they are present and ISO-8601 UTC.
    assert datapackage["created"].endswith("Z")
    assert datapackage["mainPageDate"].endswith("Z")


def test_pages_jsonl_is_copied_through_unmodified(wacz_zip):
    """Perma builds pages.jsonl itself; js-wacz must not rewrite it."""
    assert wacz_zip.read("pages/pages.jsonl").decode() == PAGES_JSONL


def test_cdx_index_covers_the_warc_records(wacz_zip):
    lines = wacz_zip.read("indexes/index.cdx").decode().strip().split("\n")

    assert len(lines) == 2
    surts = [line.split(" ")[0] for line in lines]
    assert surts == ["com,example)/", "com,example)/robots.txt"]
    assert surts == sorted(surts), "CDXJ must stay sorted for playback lookup"

    for line in lines:
        entry = json.loads(line.split(" ", 2)[2])
        assert entry["filename"] == "archive.warc.gz"
        assert entry["status"] == 200
        assert entry["mime"] == "text/html"
        assert entry["length"] > 0
        assert "digest" in entry


def test_missing_input_warc_fails_with_a_nonzero_exit_and_message(tmp_path):
    """The failure celery_tasks catches as CalledProcessError and logs."""
    result = _run_js_wacz(tmp_path / "absent.warc.gz", tmp_path / "out.wacz", tmp_path)

    assert result.returncode != 0
    assert "must be a valid path leading to at least 1 .warc" in result.stderr
    assert not (tmp_path / "out.wacz").exists()


def test_non_jsonl_files_in_the_pages_directory_are_skipped_not_fatal(converted_wacz):
    """Production points -p at a directory holding the WARC and the output WACZ too."""
    # converted_wacz was built from exactly that layout; reaching here means the
    # resulting "Skipping file" warnings do not fail the conversion.
    assert converted_wacz.exists()


def test_garbage_warc_content_still_exits_zero(tmp_path):
    """Characterizes upstream behavior: js-wacz validates the extension, not the bytes.

    A corrupt capture therefore reaches Perma as a successful conversion producing
    an empty index, not as a CalledProcessError. Reported, not fixed -- this is
    upstream behavior, outside the dependency-upgrade scope.
    """
    warc_path = tmp_path / "corrupt.warc.gz"
    warc_path.write_text("this is not a warc")
    (tmp_path / "pages.jsonl").write_text(PAGES_JSONL)
    wacz_path = tmp_path / "out.wacz"

    result = _run_js_wacz(warc_path, wacz_path, tmp_path)

    assert result.returncode == 0
    with zipfile.ZipFile(wacz_path) as archive:
        index = archive.read("indexes/index.cdx").decode()

    # The unparseable bytes yield a single record with no SURT and no URL.
    assert index.startswith("undefined ")
    assert '"filename":"corrupt.warc.gz"' in index
