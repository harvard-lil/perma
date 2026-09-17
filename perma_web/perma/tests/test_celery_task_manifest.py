"""Tests for the celery_task_manifest command.

CI runs it against the built image and a deploy compares two of its documents to
decide whether workers can be rolled without pausing intake, so the document's
shape and its hashes are the interface. Nothing here needs a database.
"""

import json

from celery.schedules import crontab
from django.core.management import call_command

from perma.management.commands.celery_task_manifest import (
    FORMAT_VERSION,
    HASH_LENGTH,
    _digest,
    argspec_hash,
    beat_entries,
    manifest,
    render,
)


def test_command_output_is_deterministic(tmp_path):
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    call_command("celery_task_manifest", output=str(first))
    call_command("celery_task_manifest", output=str(second))
    assert first.read_bytes() == second.read_bytes()
    assert first.read_text() == render(json.loads(first.read_text()))  # sorted keys, indent 2, newline


def test_manifest_describes_perma_tasks():
    document = manifest()
    assert document["format"] == FORMAT_VERSION
    assert len(document["hash"]) == HASH_LENGTH
    assert document["default_queue"] == "celery"
    tasks = document["tasks"]
    assert not any(name.startswith("celery.") for name in tasks)
    assert tasks["perma.celery_tasks.run_next_capture"]["queue"] == "celery"
    assert tasks["perma.celery_tasks.convert_warc_to_wacz"]["queue"] == "wacz-conversion"
    assert tasks["perma.celery_tasks.upload_link_to_internet_archive"]["queue"] == "ia"
    assert all(len(task["argspec"]) == HASH_LENGTH for task in tasks.values())


def test_argspec_hash_follows_the_signature():
    def original(link_guid, attempt=1):
        pass

    def same_signature(link_guid, attempt=1):
        return "a different body"

    def new_default(link_guid, attempt=2):
        pass

    def renamed(guid, attempt=1):
        pass

    def keyword_only(link_guid, *, attempt=1):
        pass

    def extra_parameter(link_guid, attempt=1, force=False):
        pass

    assert argspec_hash(original) == argspec_hash(same_signature)
    assert len({argspec_hash(f) for f in (original, new_default, renamed, keyword_only, extra_parameter)}) == 5


def test_beat_entries_record_task_schedule_and_queue():
    entries = beat_entries({
        "run-next-capture": {
            "task": "perma.celery_tasks.run_next_capture",
            "schedule": crontab(minute="*"),
        },
        "confirm_files_uploaded_to_internet_archive": {
            "task": "perma.celery_tasks.queue_file_uploaded_confirmation_tasks",
            "schedule": crontab(minute="2-59/5"),
        },
        "explicit-queue": {
            "task": "perma.celery_tasks.run_next_capture",
            "schedule": crontab(minute="*"),
            "options": {"queue": "elsewhere"},
        },
    })
    assert entries["run-next-capture"] == {
        "task": "perma.celery_tasks.run_next_capture",
        "schedule": repr(crontab(minute="*")),
        "queue": "celery",
    }
    assert entries["confirm_files_uploaded_to_internet_archive"]["queue"] == "ia-readonly"
    assert entries["explicit-queue"]["queue"] == "elsewhere"


def test_hash_changes_when_a_task_changes():
    document = manifest()
    altered = json.loads(json.dumps(document))
    altered["tasks"]["perma.celery_tasks.run_next_capture"]["argspec"] = "0" * HASH_LENGTH
    assert _digest({"tasks": altered["tasks"], "beat": altered["beat"]}) != document["hash"]
