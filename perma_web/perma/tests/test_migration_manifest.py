"""Tests for the migration_manifest command.

The image build runs it to record the migration graph inside the built image
(see the Dockerfile), and a deploy compares that record against the same command
run elsewhere -- so the document's shape and its hash are the interface, not an
implementation detail.

Nothing here needs a database: the command loads migrations from disk.
"""

import json

from django.core.management import call_command

from perma.management.commands.migration_manifest import (
    FORMAT_VERSION,
    manifest,
    manifest_hash,
    migration_names,
)


def test_migration_names_reach_beyond_this_repository():
    # Loading the graph from disk inside the built environment is what picks up
    # migrations shipped by installed packages, alongside the apps here.
    apps = {name.split(".")[0] for name in migration_names()}
    assert {"perma", "reporting"} <= apps
    assert {"admin", "auth", "contenttypes", "sessions"} <= apps


def test_manifest_describes_its_own_list():
    document = manifest()
    # An empty graph satisfies every other assertion here, and is what a
    # misconfigured loader produces, so say out loud that there is something to
    # check rather than passing on nothing.
    assert document["count"] > 0
    assert document["format"] == FORMAT_VERSION
    assert document["count"] == len(document["migrations"])
    assert document["migrations"] == sorted(document["migrations"])
    assert document["hash"] == manifest_hash(document["migrations"])


def test_hash_distinguishes_different_migration_sets():
    names = migration_names()
    assert manifest_hash(names) != manifest_hash(names[:-1])


def test_command_writes_the_manifest_to_a_file(tmp_path):
    output = tmp_path / "migrations.json"
    call_command("migration_manifest", output=str(output))
    assert json.loads(output.read_text()) == manifest()
