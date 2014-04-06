# This file will be copied to settings/__init__.py by `fab heroku_push`

from .settings_prod import *

# Parse database configuration from $DATABASE_URL
if os.environ.has_key('CLEARDB_DATABASE_URL'):
    import dj_database_url
    DATABASES['default'] =  dj_database_url.config('CLEARDB_DATABASE_URL')

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

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

# these are relative to the S3 bucket
MEDIA_ROOT = '/media/'
STATIC_ROOT = '/static/'

### OVERRIDE THESE WITH ENV VARS ###

# Instapaper credentials
INSTAPAPER_KEY = 'key'
INSTAPAPER_SECRET = 'secret'
INSTAPAPER_USER = 'user@example.com'
INSTAPAPER_PASS = 'pass'

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

SECRET_KEY = None

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


### environment settings overrides ###
# this lets us set values from the environment, like
# export DJANGO__SECRET_KEY=foo
# export DJANGO__INT__SITE_ID=1
# export DJANGO__DATABASES__default__NAME=perma
for key, value in os.environ.iteritems():
    if key.startswith("DJANGO__"):
        path = key.split('__')[1:]

        if path[0] == 'INT':
            # convert to int if second piece of path is 'INT'
            value = int(value)
            path = path[1:]
        elif value=='True':
            # convert to boolean
            value=True
        elif value=='False':
            value=False

        # starting with globals(), walk down the tree to find the intended value
        target = globals()
        while len(path) > 1:
            if not path[0] in target:
                target[path[0]] = {}
            target = target[path.pop(0)]

        # set value
        target[path[0]] = value


assert SECRET_KEY is not None, "Set DJANGO__SECRET_KEY env var!"