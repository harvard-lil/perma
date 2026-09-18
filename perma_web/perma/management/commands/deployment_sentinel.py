"""Pause and resume capture intake around a deploy.

    manage.py deployment_sentinel set      store the flag in the shared cache
    manage.py deployment_sentinel clear    remove it
    manage.py deployment_sentinel status   report; exit 0 pending, 1 not pending,
                                           2 if the cache could not be read

`set` and `clear` read the flag back and fail (exit 1) if the cache did not
take the write, which is what a Redis outage looks like under
IGNORE_EXCEPTIONS. The ECS deploy runs `set` in a web task before draining the
queues and `clear` after the rollout; on the Salt hosts the file
settings.DEPLOYMENT_SENTINEL does the same job and is still honoured (see
perma.utils.deployment_pending). `status` reports both signals.
"""

import sys

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

from perma.utils import (
    DEPLOYMENT_SENTINEL_CACHE_KEY,
    deployment_pending,
    deployment_sentinel_state,
)


class Command(BaseCommand):
    help = "Set, clear or report the deployment sentinel that pauses capture intake."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["set", "clear", "status"])

    def handle(self, *args, action, **options):
        getattr(self, action)()

    def set(self):
        cache.set(DEPLOYMENT_SENTINEL_CACHE_KEY, True, timeout=None)
        state = deployment_sentinel_state()
        if not state.cache_readable or not state.cache_flag:
            raise CommandError("Deployment sentinel not set: the cache did not take the write.")
        self.stdout.write("Deployment sentinel set.")

    def clear(self):
        cache.delete(DEPLOYMENT_SENTINEL_CACHE_KEY)
        state = deployment_sentinel_state()
        if not state.cache_readable or state.cache_flag:
            raise CommandError("Deployment sentinel not cleared: the cache did not take the delete.")
        self.stdout.write("Deployment sentinel cleared.")
        if state.file_present:
            self.stdout.write(f"Note: sentinel file {self._file_path()} is present on this host; intake stays paused here.")

    def status(self):
        state = deployment_sentinel_state()
        self.stdout.write(
            f"cache flag: {'set' if state.cache_flag else 'not set' if state.cache_readable else 'unreadable'}; "
            f"sentinel file {self._file_path()}: {'present' if state.file_present else 'absent'}; "
            f"deployment pending: {'yes' if deployment_pending() else 'no'}"
        )
        if not state.cache_readable:
            sys.exit(2)
        sys.exit(0 if deployment_pending() else 1)

    @staticmethod
    def _file_path():
        from django.conf import settings
        return settings.DEPLOYMENT_SENTINEL
