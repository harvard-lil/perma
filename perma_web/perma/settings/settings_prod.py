from settings_common import *
from celery.schedules import crontab

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# The base location, on disk, where we want to store our generated assets
GENERATED_ASSETS_STORAGE = '/perma/assets/generated'

# Additional locations of static files
STATICFILES_DIRS = (
    'static',
    GENERATED_ASSETS_STORAGE

    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# Schedule our nightly stats generation
CELERYBEAT_SCHEDULE = {
    'get-nightly-stats': {
        'task': 'perma.tasks.get_nigthly_stats',
        'schedule': crontab(minute='05', hour='02', day_of_week='*'),
    },
}