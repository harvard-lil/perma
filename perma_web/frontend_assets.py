"""Keep the compiled frontend bundles in step with their sources.

`static/bundles/` and `webpack-stats.json` are build output. They are not
committed, so they have to be produced locally -- and, more importantly, they
have to be *rebuilt* when the sources move. A stale bundle is worse than a
missing one: the app and the test suite both run happily against it and quietly
exercise last week's frontend.

Staleness is decided by hashing the build's inputs and comparing against the
hash recorded when the bundles were last built. mtimes are not usable here:
git sets them to checkout time, so a fresh clone can look arbitrarily fresh or
stale depending on the order files happened to be written.

Adapted from h2o's web/frontend_assets.py.
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent

# Everything `npm run build` reads. All of static/ is an input except the
# output directory: the entry points are under static/js, static/css and
# static/frontend, and the SCSS pulls fonts, images and vendored CSS from the
# directories beside them.
INPUT_PATHS = [
    "static",
    "package.json",
    "npm-shrinkwrap.json",
    "webpack.config.js",
    "browserslist",
    ".npmrc",
]

# Written by npm run build, via webpack-bundle-tracker in webpack.config.js.
STATS_FILE = WEB_DIR / "webpack-stats.json"
DIST_DIR = WEB_DIR / "static" / "bundles"

# Records the input hash the current bundles were built from.
HASH_FILE = DIST_DIR / ".input-hash"


def _iter_files(path):
    if path.is_file():
        yield path
    elif path.is_dir():
        for child in sorted(path.rglob("*")):
            if child.is_file() and DIST_DIR not in child.parents:
                yield child


def input_hash():
    """Hash of every file the frontend build reads."""
    hasher = hashlib.sha256()
    for entry in INPUT_PATHS:
        root = WEB_DIR / entry
        for file_path in _iter_files(root):
            # Include the name so that moving a file changes the hash even when
            # the bytes do not.
            hasher.update(str(file_path.relative_to(WEB_DIR)).encode("utf-8"))
            hasher.update(file_path.read_bytes())
    return hasher.hexdigest()


def recorded_hash():
    try:
        return HASH_FILE.read_text().strip()
    except FileNotFoundError:
        return None


def is_stale():
    """True when the bundles are missing, or were built from different sources."""
    if not STATS_FILE.exists() or not DIST_DIR.is_dir():
        return True
    return recorded_hash() != input_hash()


def build(quiet=False):
    """Run the frontend build and record what it was built from."""
    if not (WEB_DIR / "node_modules").is_dir():
        if not quiet:
            print("Installing frontend dependencies (npm ci)...", file=sys.stderr)
        subprocess.run(["npm", "ci"], cwd=WEB_DIR, check=True)

    if not quiet:
        print("Building frontend assets (npm run build)...", file=sys.stderr)
    subprocess.run(["npm", "run", "build"], cwd=WEB_DIR, check=True)

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    HASH_FILE.write_text(input_hash())


def ensure_current(quiet=False):
    """Build the bundles if they are missing or stale. Returns True if it built."""
    # An image that baked its bundles in (the prod and test targets do) has no
    # npm sources to rebuild from, and does not need this.
    if os.environ.get("PERMA_SKIP_ASSET_CHECK"):
        return False
    if not is_stale():
        return False
    build(quiet=quiet)
    return True
