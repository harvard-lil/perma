# via https://github.com/celery/celery/blob/3.1/examples/django/proj/__init__.py

from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app