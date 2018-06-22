# via https://github.com/celery/celery/blob/3.1/examples/django/proj/__init__.py
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app  # noqa


# tell Django where to find the app config
default_app_config = 'perma.apps.PermaConfig'
