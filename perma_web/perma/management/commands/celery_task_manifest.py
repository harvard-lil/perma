"""Write the registered Celery tasks and the beat schedule as JSON.

CI runs this against the built image (under PERMA_SETTINGS_MODULE=settings_build,
with no network and a read-only root) and attaches the result to the published
image. A deploy compares the candidate's manifest with the running tier's: when
they are equal, the workers can be rolled with a warm shutdown and no intake
pause, because every task message the old code left on the broker can be
executed by the new code. The document's shape is therefore an interface.

Format version 1 (keys sorted, two-space indent, trailing newline):

    {
      "beat": {
        "<entry name>": {
          "queue": "<queue the entry's messages go to>",
          "schedule": "<repr of the schedule, e.g. <crontab: * * * * * (m/h/dM/MY/d)>>",
          "task": "<task name>"
        }
      },
      "default_queue": "<app.conf.task_default_queue, 'celery' unless overridden>",
      "format": 1,
      "hash": "<12 hex characters>",
      "tasks": {
        "<task name>": {
          "argspec": "<12 hex characters>",
          "queue": "<queue>"
        }
      }
    }

- "tasks" covers every task registered with the Celery app except Celery's own
  (names beginning "celery."). In this codebase that is perma.celery_tasks.*.
- "argspec" is sha256, truncated to 12 hex characters, over the JSON list of
  [name, kind, default] for each parameter of the task's run function in
  declaration order, where kind is inspect's parameter-kind name and default is
  repr(default) or null when there is none. It changes when a parameter is
  added, removed, renamed, reordered, made keyword-only, or given a different
  default; it does not change with the function body.
- "queue" is the task's own `queue` option when set, else its entry in
  CELERY_TASK_ROUTES, else the default queue.
- "beat" is the CELERY_BEAT_SCHEDULE the selected settings module produces.
  settings_build imports settings_prod, so CI's manifest carries the prod tier's
  beat list; a staging deploy compares that list against the same document
  produced by the same settings, so the comparison is still like for like.
- "hash" is sha256, truncated to 12 hex characters, over the canonical JSON
  (sorted keys, no whitespace) of {"beat": ..., "tasks": ...}. Two manifests are
  interchangeable exactly when their hashes are equal.
"""

import hashlib
import inspect
import json

from django.core.management.base import BaseCommand

from perma.celery import app

FORMAT_VERSION = 1
HASH_LENGTH = 12


def _digest(document):
    payload = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:HASH_LENGTH]


def argspec_hash(function):
    """Short digest of a callable's parameters: names, kinds and defaults."""
    parameters = [
        [
            parameter.name,
            parameter.kind.name,
            None if parameter.default is inspect.Parameter.empty else repr(parameter.default),
        ]
        for parameter in inspect.signature(function).parameters.values()
    ]
    return _digest(parameters)


def task_queue(name, task=None):
    """The queue a task's messages are sent to, by Perma's routing rules."""
    if task is not None and getattr(task, "queue", None):
        return task.queue
    route = (app.conf.task_routes or {}).get(name) or {}
    return route.get("queue") or app.conf.task_default_queue


def registered_tasks():
    """Every registered task other than Celery's own, as {name: {argspec, queue}}."""
    app.loader.import_default_modules()
    return {
        name: {"argspec": argspec_hash(task.run), "queue": task_queue(name, task)}
        for name, task in app.tasks.items()
        if not name.startswith("celery.")
    }


def beat_entries(schedule):
    """CELERY_BEAT_SCHEDULE reduced to what a deploy needs to compare."""
    return {
        name: {
            "task": entry["task"],
            "schedule": repr(entry["schedule"]),
            "queue": entry.get("options", {}).get("queue") or task_queue(entry["task"], app.tasks.get(entry["task"])),
        }
        for name, entry in schedule.items()
    }


def manifest():
    tasks = registered_tasks()
    beat = beat_entries(app.conf.beat_schedule or {})
    return {
        "format": FORMAT_VERSION,
        "hash": _digest({"tasks": tasks, "beat": beat}),
        "default_queue": app.conf.task_default_queue,
        "tasks": tasks,
        "beat": beat,
    }


def render(document):
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


class Command(BaseCommand):
    help = "Write the registered Celery tasks, their argument hashes and queues, and the beat schedule as JSON."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            metavar="PATH",
            help="File to write the manifest to. Written to stdout when omitted.",
        )

    def handle(self, *args, **options):
        document = render(manifest())
        if options["output"]:
            with open(options["output"], "w") as file:
                file.write(document)
        else:
            self.stdout.write(document, ending="")
