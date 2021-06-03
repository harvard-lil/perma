import logging

from django.apps import AppConfig


logger = logging.getLogger(__name__)


class PermaConfig(AppConfig):
    name = 'perma'

    def ready(self):
        # register our signals
        from . import signals  # noqa
