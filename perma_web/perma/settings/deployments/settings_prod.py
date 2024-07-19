from .settings_common import *

DEBUG = False

# This is handy for debugging problems that *only* happen when Debug = False,
# because exceptions are printed directly to the log/console when they happen.
# Just don't leave it on!
# DEBUG_PROPAGATE_EXCEPTIONS = True

# Schedule celerybeat jobs.
# These will be added to CELERYBEAT_SCHEDULE in settings.utils.post_processing
CELERY_BEAT_JOB_NAMES = [
    'run-next-capture',
    'sync_subscriptions_from_perma_payments',
    'cache_playback_status_for_new_links',
    'conditionally_queue_internet_archive_uploads_for_date_range',
    'confirm_files_uploaded_to_internet_archive',
    'confirm_files_deleted_from_internet_archive',
]

# logging
LOGGING['handlers']['file']['filename'] = '/var/log/perma/perma.log'

# caching
CACHES["default"] = {
    "BACKEND": "django_redis.cache.RedisCache",
    "LOCATION": "redis://127.0.0.1:6379/0",
    "OPTIONS": {
        "CLIENT_CLASS": "django_redis.client.DefaultClient",
        "IGNORE_EXCEPTIONS": True,  # since this is just a cache, we don't want to show errors if redis is offline for some reason
    }
}

# subscription packages
TIERS['Individual'] = [
    {
        'period': 'monthly',
        'link_limit': 10,
        'rate_ratio': 1
    },{
        'period': 'monthly',
        'link_limit': 100,
        'rate_ratio': 2.5
    },{
        'period': 'monthly',
        'link_limit': 500,
        'rate_ratio': 10
    }
]

CONTACT_MINUTE_LIMIT = '2/m'
CONTACT_HOUR_LIMIT = '5/h'
CONTACT_DAY_LIMIT = '10/d'
REPORT_MINUTE_LIMIT = '2/m'
REPORT_HOUR_LIMIT = '10/h'
REPORT_DAY_LIMIT = '50/d'
