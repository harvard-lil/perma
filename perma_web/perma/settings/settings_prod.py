from settings_common import *
from celery.schedules import crontab

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# The base location, on disk, where we want to store our generated assets
GENERATED_ASSETS_STORAGE = '/perma/assets/generated'

# Schedule our nightly stats generation
CELERYBEAT_SCHEDULE = {
    'get-nightly-stats': {
        'task': 'perma.tasks.get_nigthly_stats',
        'schedule': crontab(minute='05', hour='02', day_of_week='*'),
    },
}

# warc_server uses this to make requests -- it should point back to Django's /cdx view
CDX_SERVER_URL = 'http://127.0.0.1/cdx'