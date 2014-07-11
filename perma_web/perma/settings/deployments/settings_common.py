# Core settings used by all deployments.

import os, sys

# PROJECT_ROOT is the absolute path to the perma_web folder
# We determine this robustly thanks to http://stackoverflow.com/a/2632297
this_module = unicode(
    sys.executable if hasattr(sys, "frozen") else __file__,
    sys.getfilesystemencoding())
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(this_module))))


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'perma',                      # Or path to database file if using sqlite3.
        'USER': 'perma',
        'PASSWORD': 'perma',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '3306',                      # Set to empty string for default.
        'OPTIONS': {
            "init_command": "SET storage_engine=INNODB; SET foreign_key_checks = 0; SET NAMES 'utf8';",
            "charset": "utf8",
        },
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# user-generated files
MEDIA_ROOT = ''
MEDIA_URL = '/media/'

# Monitor app generated files
MONITOR_ROOT = '/tmp/perma/monitor'
MONITOR_URL = '/monitor/media/'

# static files
STATIC_ROOT = ''                # where to store collected static files
STATIC_URL = '/static/'         # URL to serve static files
STATICFILES_DIRS = ('static',)  # where to look for static files (in addition to app/static/)
STATICFILES_FINDERS = (         # how to look for static files
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Django Pipline config
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

# media storage -- default_storage config
DEFAULT_FILE_STORAGE = 'perma.storage_backends.FileSystemStorage'

# We likely want to do something like this:
# PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.jsmin.JSMinCompressor'

PIPELINE_JS_COMPRESSOR = None

# We likely want to remove this disable in the future
PIPELINE_DISABLE_WRAPPER = True

PIPELINE_JS = {
    'create': {
        'source_filenames': (
          'js/create.js',
        ),
        'output_filename': 'js/create-bundle.js',
    }
}

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'mirroring.middleware.MirrorCsrfViewMiddleware',
    'mirroring.middleware.MirrorAuthenticationMiddleware',
    'mirroring.middleware.MirrorForwardingMiddleware',
    'ratelimit.middleware.RatelimitMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

RATELIMIT_VIEW = 'perma.views.common.rate_limit'

ROOT_URLCONF = 'urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'perma.wsgi.application'

TEMPLATE_CONTEXT_PROCESSORS = (
    "perma.analytics.analytics",
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',   # include `request` in templates
    'django.core.context_processors.static',    # include `STATIC_URL` in templates
    'django.core.context_processors.media',     # include `MEDIA_URL` in templates
)

INSTALLED_APPS = (
    # built in apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # our apps
    'perma',
    'monitor',
    'mirroring',

    # third party apps
    'south',
    'ratelimit',
    'mptt',
    'pipeline',
)

AUTH_USER_MODEL = 'perma.LinkUser'

LOGIN_REDIRECT_URL = '/manage/create/'
LOGIN_URL = '/login'


MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

# When getting the source with wget, let's set some details
ARCHIVE_QUOTA = '20m' # Maximum filesize
ARCHIVE_LIMIT_RATE = '100m' # Download limit rate; TODO reduce for production
ACCEPT_CONTENT_TYPES = [ # HTTP content-type parameters to accept
    'text/html',
    'text/xml',
    'application/xhtml+xml',
    'application/xml'
]
NUMBER_RETRIES = 3 # if wget fails to get a resource, try to get again this many times
WAIT_BETWEEN_TRIES = .5 # wait between .5 and this many seconds between http requests to our source

# Max file size (for our downloads)
MAX_ARCHIVE_FILE_SIZE = 1024 * 1024 * 100 # 100 MB

# Rate limits
MINUTE_LIMIT = '6000/m'
HOUR_LIMIT = '100000/h'
DAY_LIMIT = '500000/d'
REGISTER_MINUTE_LIMIT = '600/m'
REGISTER_HOUR_LIMIT = '2000/h'
REGISTER_DAY_LIMIT = '5000/d'
LOGIN_MINUTE_LIMIT = '5000/m'
LOGIN_HOUR_LIMIT = '10000/h'
LOGIN_DAY_LIMIT = '50000/d'

# Dashboard user lists
MAX_USER_LIST_SIZE = 100

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(filename)s %(lineno)d: %(message)s'
        },
    },
    'filters': {
         'require_debug_false': {
             '()': 'django.utils.log.RequireDebugFalse'
         }
     },
    'handlers': {
        'default': {
            'level':'INFO',
            'filters': ['require_debug_false'],
            'class':'logging.handlers.RotatingFileHandler',
            'filename': '/tmp/perma.log',
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter':'standard',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


# Celery settings
BROKER_URL = 'amqp://guest:guest@localhost:5672/'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Control whether Celery tasks should be run in the background or during a request.
# This should normally be True, but it might be handy to not use async tasks
# if you're running a mirror on Heroku or something like that.
RUN_TASKS_ASYNC = True


### mirror stuff

MIRRORING_ENABLED = False           # whether to use mirroring features
MIRROR_SERVER = False               # whether we are a mirror
MIRROR_COOKIE_NAME = 'user_info'
MIRROR_USERS_SUBDOMAIN = 'users'

# mirror v1 stuff
ROOT_METADATA_SERVER = 'http://perma.cc'
ROOT_ASSETS_SERVER = 'http://perma.cc'
MIRRORS = []

# where we will store zip archives created for transferring to mirrors
# this is relative to MEDIA_ROOT
MEDIA_ARCHIVES_ROOT = 'zip_archives/'