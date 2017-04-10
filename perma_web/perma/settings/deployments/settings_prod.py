from settings_common import *

DEBUG = False

# This is handy for debugging problems that *only* happen when Debug = False,
# because exceptions are printed directly to the log/console when they happen.
# Just don't leave it on!
# DEBUG_PROPAGATE_EXCEPTIONS = True

# The base location, on disk, where we want to store our generated assets
MEDIA_ROOT = '/perma/assets/generated'

# Schedule celerybeat jobs.
# These will be added to CELERYBEAT_SCHEDULE in settings.utils.post_processing
CELERYBEAT_JOB_NAMES = [
    'update-stats',
    'send-links-to-internet-archives',
    ]

# logging
LOGGING['handlers']['default']['filename'] = '/var/log/perma/perma.log'
PHANTOMJS_LOG = '/var/log/perma/phantom.log'

# use separate subdomain for user content
MEDIA_URL = '//perma-archives.org/media/'
WARC_HOST = 'perma-archives.org'

# Our sorl thumbnail settings
# We only use this redis config in prod. dev envs use the local db.
THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.redis_kvstore.KVStore'
THUMBNAIL_REDIS_HOST = 'localhost'
THUMBNAIL_REDIS_PORT = '6379'

# caching
# in dev, Django will use the default in-memory cache
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # since this is just a cache, we don't want to show errors if redis is offline for some reason
        }
    }
}

# security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
