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

# Django Pipeline config
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

# media storage -- default_storage config
DEFAULT_FILE_STORAGE = 'perma.storage_backends.FileSystemStorage'

# We likely want to do something like this:
# PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.jsmin.JSMinCompressor'
PIPELINE_JS_COMPRESSOR = None
PIPELINE_CSS_COMPRESSOR = None

PIPELINE_COMPILERS = (
    'pipeline_compass.compiler.CompassCompiler',
)

# We likely want to remove this disable in the future
PIPELINE_DISABLE_WRAPPER = True

PIPELINE_JS = {
    # scripts included at the foot of all pages
    'global': {
        'source_filenames': (
            'js/jquery.js',
            'js/bootstrap3.js',
            'js/global.js',
        ),
        'output_filename': 'js/global-bundle.js',
    },

    # scripts included in the head of all pages (not counting archive pages)
    'global_head': {
        'source_filenames': (
            'js/modernizr.js',
            'js/holder.js',
            'js/local-datetime.js',
        ),
        'output_filename': 'js/global-head-bundle.js',
    },

    # scripts included in the head of archive pages
    'global_archive_head': {
        'source_filenames': (
            'js/local-datetime.js',
        ),
        'output_filename': 'js/global-archive-head.js',
    },

    # scripts included in all user dashboard pages
    'admin': {
        'source_filenames': (
            'js/handlebars.js',
            'js/handlebars_helpers.js',
            'js/admin.js',
        ),
        'output_filename': 'js/admin-bundle.js',
    },

    ## scripts for individual pages ##

    'create': {
        'source_filenames': (
            'js/lib/spin.js',
            'js/jquery.form.min.js',
            'js/create.js',
        ),
        'output_filename': 'js/create-bundle.js',
    },
    'links_list': {
        'source_filenames': (
            'js/jquery-ui-1.10.3.custom.min.js',
            'js/jquery.dotdotdot-1.5.9.min.js',
            'js/lib/jstree.min.js',
            'js/lib/jquery.splendid.textchange.js',
            'js/links-list.js',
        ),
        'output_filename': 'js/links-list-bundle.js',
    },
    'landing': {
        'source_filenames': (
            'js/raphael.js',
            'js/raphael.scale.js',
            'js/g.raphael.js',
            'js/usmap.js',
            'js/rwdImageMaps.js',
            'js/landing.js',
        ),
        'output_filename': 'js/landing-bundle.js',
    },
    'stats': {
        'source_filenames': (
            'js/d3.v3.js',
            'js/stats.js',
        ),
        'output_filename': 'js/stats-bundle.js',
    },
    'dark-archive-link': {
        'source_filenames': (
            'js/dark-archive-link.js',
        ),
        'output_filename': 'js/dark-archive-link-bundle.js',
    },
    'link-delete-confirm': {
        'source_filenames': (
            'js/link-delete-confirm.js',
        ),
        'output_filename': 'js/link-delete-confirm-bundle.js',
    },
    'link-vest-confirm': {
        'source_filenames': (
            'js/link-vest-confirm.js',
        ),
        'output_filename': 'js/link-vest-confirm-bundle.js',
    },
    'single-link': {
        'source_filenames': (
            'js/single-link.js',

        ),
        'output_filename': 'js/single-link-bundle.js',
    },
    'doc-developer': {
        'source_filenames': (
            'js/pretty-print-json.js',
        ),
        'output_filename': 'js/pretty-print-json.js',
    },
}

PIPELINE_CSS = {
    'base': {
        'source_filenames': (
            'css/bootstrap3.css',
            'css/bootstrap-glyphicons.css',
            'css/style-responsive.scss',
            'css/font-awesome.min.css',
        ),
        'output_filename': 'css/base-bundle.css',
    },
    'base-archive': {
        'source_filenames': (
            'css/bootstrap3.css',
            'css/style-responsive-archive.scss',
            'css/font-awesome.min.css',
        ),
        'output_filename': 'css/base-archive-bundle.css',
    },
}

# override to change .js mimetype from application/javascript for ie8 and below
# see http://django-pipeline.readthedocs.org/en/latest/configuration.html#pipeline-mimetypes
PIPELINE_MIMETYPES = (
  (b'text/coffeescript', '.coffee'),
  (b'text/less', '.less'),
  (b'text/javascript', '.js'),
  (b'text/x-sass', '.sass'),
  (b'text/x-scss', '.scss')
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'perma.middleware.SecurityMiddleware',
    'api.middleware.APISubdomainMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'perma.middleware.AdminAuthMiddleware',
    'ratelimit.middleware.RatelimitMiddleware',
    'perma.middleware.ReadOnlyMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

RATELIMIT_VIEW = 'perma.views.common.rate_limit'

ROOT_URLCONF = 'urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'perma.wsgi.application'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',   # include `request` in templates
    'django.core.context_processors.static',    # include `STATIC_URL` in templates
    'django.core.context_processors.media',     # include `MEDIA_URL` in templates
    'django.contrib.auth.context_processors.auth',  # for Django admin
    'settings_context_processor.context_processors.settings',  # to easily use settings in templates
)

INSTALLED_APPS = (
    # built in apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # our apps
    'perma',
    'api',
    'monitor',

    # third party apps
    'ratelimit',
    'mptt',
    'pipeline',
    'sorl.thumbnail',
    'django_forms_bootstrap',
    'djangosecure',  # force SSL -- this can be removed in Django 1.8
    'settings_context_processor',

    # django admin -- has to come after our apps for our admin template overrides to work
    'django.contrib.admin',
    'tastypie'
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
MAX_ARCHIVE_FILE_SIZE = 1024 * 1024 * 100  # 100 MB
MAX_HTTP_FETCH_SIZE = 1024 * 1024  # 1 MB

# Max image size for screenshots and thumbnails
MAX_IMAGE_SIZE = 1024*1024*50  # 50 megapixels

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

# Cache-Control max-age settings
CACHE_MAX_AGES = {
    'single_linky' : 60 * 60,     # 1hr
    'timegate'     : 60 * 60,     # 1hr
    'timemap'      : 60 * 30,     # 30mins
    'memento'      : 60 * 60 * 4, # 4hrs
}

# Dashboard user lists
MAX_USER_LIST_SIZE = 50

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
            'handlers': ['default', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}

# IP ranges we won't archive.
# Via http://en.wikipedia.org/wiki/Reserved_IP_addresses
BANNED_IP_RANGES = [
    "0.0.0.0/8",
    "10.0.0.0/8",
    "100.64.0.0/10",
    "127.0.0.0/8",
    "169.254.0.0/16",
    "172.16.0.0/12",
    "192.0.0.0/29",
    "192.0.2.0/24",
    "192.88.99.0/24",
    "192.168.0.0/16",
    "198.18.0.0/15",
    "198.51.100.0/24",
    "203.0.113.0/24",
    "224.0.0.0/4",
    "240.0.0.0/4",
    "255.255.255.255/32",
    "::/128",
    "::1/128",
    "::ffff:0:0/96",
    "100::/64",
    "64:ff9b::/96",
    "2001::/32",
    "2001:10::/28",
    "2001:db8::/32",
    "2002::/16",
    "fc00::/7",
    "fe80::/10",
    "ff00::/8",
]

# Celery settings
BROKER_URL = 'amqp://guest:guest@localhost:5672/'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_SEND_TASK_ERROR_EMAILS = True

# Control whether Celery tasks should be run in the background or during a request.
# This should normally be True, but it's handy to not require rabbitmq and celery sometimes.
RUN_TASKS_ASYNC = True

API_SUBDOMAIN = 'api'

CACHE_BYPASS_COOKIE_NAME = 'bypass_cache'

# internet archive stuff
UPLOAD_TO_INTERNET_ARCHIVE = False
INTERNET_ARCHIVE_COLLECTION = 'perma_cc'
INTERNET_ARCHIVE_IDENTIFIER_PREFIX = 'perma_cc_'
# Find these at https://archive.org/account/s3.php :
INTERNET_ARCHIVE_ACCESS_KEY = ''
INTERNET_ARCHIVE_SECRET_KEY = ''

from dateutil.relativedelta import relativedelta
LINK_EXPIRATION_TIME = relativedelta(years=2)


# If set, warc content must be served from this host.
# On production, this is highly recommended to be different from hosts in ALLOWED_HOSTS.
WARC_HOST = None

# Sorl settings. This relates to our thumbnail creation.
# The prod and dev configs are considerably different. See those configs for details.
THUMBNAIL_ENGINE = 'sorl.thumbnail.engines.wand_engine.Engine'
THUMBNAIL_FORMAT = 'PNG'
THUMBNAIL_COLORSPACE = None

# Relative to MEDIA_ROOT
THUMBNAIL_STORAGE_PATH = 'thumbnails'

# feature flags
SINGLE_LINK_HEADER_TEST = False

# security settings -- set these to true if SSL is available
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False

API_VERSION = 1

TEMPLATE_VISIBLE_SETTINGS = (
    'API_VERSION',
    'SECURE_SSL_REDIRECT',
    'HOST',
)


### Tastypie
# http://django-tastypie.readthedocs.org/en/latest/settings.html

TASTYPIE_ALLOW_MISSING_SLASH = True
APPEND_SLASH = False

TASTYPIE_DEFAULT_FORMATS = ['json']

TASTYPIE_FULL_DEBUG = True  # Better Tastypie error handling for debugging. Only has an effect when DEBUG=True.


# Schedule celerybeat jobs.
# These will be added to CELERYBEAT_SCHEDULE in settings.utils.post_processing
CELERYBEAT_JOB_NAMES = []


# Set to true to disable database/file writes for maintenance.
READ_ONLY_MODE = False


# tests
TEST_RUNNER = 'django.test.runner.DiscoverRunner'  # In Django 1.7, including this silences a warning about tests
USE_SAUCE = False  # Default to local functional tests
SAUCE_USERNAME = None
SAUCE_ACCESS_KEY = None

WARC_STORAGE_DIR = 'warcs'  # relative to MEDIA_ROOT