from settings_common import *
from celery.schedules import crontab

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# This is handy for debugging problems that *only* happen when Debug = False,
# because exceptions are printed directly to the log/console when they happen.
# Just don't leave it on!
# DEBUG_PROPAGATE_EXCEPTIONS = True

# The base location, on disk, where we want to store our generated assets
MEDIA_ROOT = '/perma/assets/generated'

# Schedule our nightly stats generation
CELERYBEAT_SCHEDULE = {
    'get-nightly-stats': {
        'task': 'perma.tasks.get_nightly_stats',
        'schedule': crontab(minute='05', hour='02', day_of_week='*'),
    },
    'email-weekly-stats': {
        'task': 'perma.tasks.email_weekly_stats',
        'schedule': crontab(minute='05', hour='06', day_of_week='tuesday'),
    },
    'cleanup-screencap-monitoring': {
        'task': 'monitor.tasks.delete_screencaps',
        'schedule': crontab(hour='*/2'), # every other hour
    },
}

# If a task is running longer than five minutes, kill it
CELERYD_TASK_TIME_LIMIT = 300

# warc_server uses this to make requests -- it should point back to Django's /cdx view
CDX_SERVER_URL = 'http://127.0.0.1/cdx'

PHANTOMJS_LOG = '/var/log/perma/phantom.log'

# default vesting org for links vested by registry users
FALLBACK_VESTING_ORG_ID = 15  # HLS Default Vesting Org