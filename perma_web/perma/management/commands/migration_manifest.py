"""List the migrations an environment has on disk.

The image build writes this to /perma/perma_web/migrations.json (see the
Dockerfile), so what a candidate image expects of the database can be read
without running it. Running the same command inside a container produces the
same document, and the two are comparable by their `hash` field alone.

The list comes from the migration graph as loaded from disk, so it covers
third-party migrations from site-packages (admin, auth, contenttypes, sessions,
axes, taggit, waffle...) as well as the repository's own. It says nothing about
which migrations any database has applied: MigrationLoader is constructed with
connection=None, which loads files and touches no database.

Copied from h2o's web/main/management/commands/migration_manifest.py; the
format is the interface the shared deploy sequence reads, so keep them equal.
"""

import hashlib
import json

from django.core.management.base import BaseCommand
from django.db.migrations.loader import MigrationLoader

# Bumped when the document's shape changes, so a reader comparing two manifests
# can tell "these disagree about migrations" from "these were written by
# different versions of this command".
FORMAT_VERSION = 1

# Enough hex to make a collision between two real migration sets implausible,
# and short enough to paste into a deploy log.
HASH_LENGTH = 12


def migration_names():
    """Every migration on disk, as sorted "app_label.migration_name" strings."""
    loader = MigrationLoader(None, ignore_no_migrations=True)
    return sorted(".".join(key) for key in loader.disk_migrations)


def manifest_hash(names):
    """Short digest of a migration list: sha256 over the names, one per line."""
    payload = "".join(f"{name}\n" for name in names).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:HASH_LENGTH]


def manifest():
    names = migration_names()
    return {
        "format": FORMAT_VERSION,
        "hash": manifest_hash(names),
        "count": len(names),
        "migrations": names,
    }


class Command(BaseCommand):
    help = "Write the on-disk migration list as JSON, for comparison against another environment."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            metavar="PATH",
            help="File to write the manifest to. Written to stdout when omitted.",
        )

    def handle(self, *args, **options):
        document = json.dumps(manifest(), indent=2) + "\n"
        output = options["output"]
        if output:
            with open(output, "w") as file:
                file.write(document)
        else:
            self.stdout.write(document, ending="")
