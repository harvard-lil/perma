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

# logging
LOGGING['handlers']['default']['filename'] = '/var/log/perma/perma.log'
PHANTOMJS_LOG = '/var/log/perma/phantom.log'

# default vesting org for links vested by registry users
FALLBACK_VESTING_ORG_ID = 15  # HLS Default Vesting Org

# use separate subdomain for user content
MEDIA_URL = '//user-content.perma.cc/media/'
WARC_HOST = 'user-content.perma.cc'

# Our sorl thumbnail settings
# We only use this redis config in prod. dev envs use the local db.
THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.redis_kvstore.KVStore'
THUMBNAIL_REDIS_HOST = 'localhost'
THUMBNAIL_REDIS_PORT = '6379'

# caching
# in dev, Django will use the default in-memory cache
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.cache.RedisCache',
        'LOCATION': '127.0.0.1:6379:0',
        'OPTIONS': {
            'CLIENT_CLASS': 'redis_cache.client.DefaultClient',
            #'PASSWORD': 'secretpassword',  # Optional
            'IGNORE_EXCEPTIONS': True,  # since this is just a cache, we don't want to show errors if redis is offline for some reason
        }
    }
}