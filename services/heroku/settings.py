# This file will be copied to settings/settings.py by `fab heroku_push`

from .deployments.settings_prod import *

# Parse database configuration from $DATABASE_URL
if os.environ.has_key('CLEARDB_DATABASE_URL'):
    import dj_database_url
    DATABASES['default'] =  dj_database_url.config('CLEARDB_DATABASE_URL')

# Allow all host headers
# TODO: this is from Heroku's getting started with Django page -- is there a safer way?
ALLOWED_HOSTS = ['*']

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static'),
)

ADMINS = (
    (os.environ.get('ADMIN_NAME', 'Your Name'), os.environ.get('ADMIN_EMAIL', 'your_email@example.com')),
)

DEFAULT_FILE_STORAGE = 'perma.storage_backends.MediaRootS3BotoStorage'
STATICFILES_STORAGE = 'perma.storage_backends.StaticRootS3BotoStorage'

# message passing
BROKER_POOL_LIMIT=1
BROKER_URL = os.environ.get('CLOUDAMQP_URL')
CELERY_RESULT_BACKEND = os.environ.get('REDISCLOUD_URL')


# these are relative to the S3 bucket
MEDIA_ROOT = '/generated/'
STATIC_ROOT = '/static/'

# AWS storage settings
AWS_QUERYSTRING_AUTH = False

# archive creation
PHANTOMJS_LOG = 'phantomjs.log' # this will just get thrown away

# parse redis url
import redis.connection
_parsed_redis_url = redis.connection.ConnectionPool.from_url(os.environ.get('REDISCLOUD_URL')).connection_kwargs

# caching
#KEY_VALUE_STORE = simplekv.memory.redisstore.RedisStore(redis.StrictRedis.from_url(os.environ.get('REDISCLOUD_URL')))
CACHES['default']['LOCATION'] = "%s:%s:%s" % (_parsed_redis_url['host'], _parsed_redis_url['port'], _parsed_redis_url['db'])
CACHES['default']['OPTIONS']['PASSWORD'] = _parsed_redis_url['password']

# thumbnail redis server
THUMBNAIL_REDIS_DB = _parsed_redis_url['db']
THUMBNAIL_REDIS_PASSWORD = _parsed_redis_url['password']
THUMBNAIL_REDIS_HOST = _parsed_redis_url['host']
THUMBNAIL_REDIS_PORT = _parsed_redis_url['port']


### OVERRIDE THESE WITH ENV VARS ###

# Google Analytics
GOOGLE_ANALYTICS_KEY = 'UA-XXXXX-X'
GOOGLE_ANALYTICS_DOMAIN = 'example.com'

# The host we want to display (used when DEBUG=False)
HOST = 'perma.cc'

# Amazon storage
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_STORAGE_BUCKET_NAME = ''
MEDIA_URL = 'http://BUCKET_NAME.s3.amazonaws.com/media/'
STATIC_URL = 'http://BUCKET_NAME.s3.amazonaws.com/static/'


########## EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/1.3/ref/settings/#email-backend
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# See: https://docs.djangoproject.com/en/1.3/ref/settings/#email-host
# EMAIL_HOST = environ.get('EMAIL_HOST', 'smtp.gmail.com')

# See: https://docs.djangoproject.com/en/1.3/ref/settings/#email-host-password
# EMAIL_HOST_PASSWORD = environ.get('EMAIL_HOST_PASSWORD', '')

# See: https://docs.djangoproject.com/en/1.3/ref/settings/#email-host-user
# EMAIL_HOST_USER = environ.get('EMAIL_HOST_USER', 'your_email@example.com')

# See: https://docs.djangoproject.com/en/1.3/ref/settings/#email-port
# EMAIL_PORT = environ.get('EMAIL_PORT', 587)

# See: https://docs.djangoproject.com/en/1.3/ref/settings/#email-subject-prefix
# EMAIL_SUBJECT_PREFIX = '[%s] ' % SITE_NAME

# See: https://docs.djangoproject.com/en/1.3/ref/settings/#email-use-tls
# EMAIL_USE_TLS = True

# See: https://docs.djangoproject.com/en/1.3/ref/settings/#server-email
# SERVER_EMAIL = EMAIL_HOST_USER
########## END EMAIL CONFIGURATION


