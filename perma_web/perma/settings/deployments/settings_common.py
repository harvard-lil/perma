# Core settings used by all deployments.
import os, sys

# PROJECT_ROOT is the absolute path to the perma_web folder
# We determine this robustly thanks to http://stackoverflow.com/a/2632297
this_module = sys.executable if hasattr(sys, "frozen") else __file__
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(this_module))))
SERVICES_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, '../services'))

# make sure mysql uses innodb and utf8
_mysql_connection_options = {
    "init_command": "SET default_storage_engine=INNODB; SET NAMES 'utf8';",
    # for mysql 5.7+, use:
    # "init_command": "SET default_storage_engine=INNODB; SET NAMES 'utf8';",
    "charset": "utf8",
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'perma',                      # Or path to database file if using sqlite3.
        'USER': 'perma',
        'PASSWORD': 'perma',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '3306',                      # Set to empty string for default.
        'OPTIONS': _mysql_connection_options

    },
    'perma-cdxline': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'perma_cdxline',
        'USER': 'perma',
        'PASSWORD': 'perma',
        'HOST': '',
        'PORT': '3306',
        'OPTIONS': _mysql_connection_options
    },
}
if os.environ.get('DOCKERIZED'):
    DATABASES['default']['USER'] = 'root'
    DATABASES['default']['PASSWORD'] = 'password'
    DATABASES['default']['HOST'] = 'db'
    DATABASES['perma-cdxline']['USER'] = 'root'
    DATABASES['perma-cdxline']['PASSWORD'] = 'password'
    DATABASES['perma-cdxline']['HOST'] = 'db'

# https://docs.djangoproject.com/en/1.9/topics/db/multi-db/#using-routers
DATABASE_ROUTERS = ['perma.cdx_router.CDXRouter']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'

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

# static files
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static-collected')                # where to store collected static files
STATIC_URL = '/static/'         # URL to serve static files

def _pywb_static_dir_location():
    # helper to return absolute path of pywb's static directory
    import pywb
    return os.path.join(os.path.dirname(pywb.__file__), 'static')

# where to look for static files (in addition to app/static/)
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static'),
    ('pywb', _pywb_static_dir_location())  # include pywb's static files at /static/pywb
)

STATICFILES_FINDERS = (         # how to look for static files
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# static files config
STATICFILES_STORAGE = 'perma.storage_backends.StaticStorage'

# media storage -- default_storage config
DEFAULT_FILE_STORAGE = 'perma.storage_backends.FileSystemMediaStorage'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'settings_context_processor.context_processors.settings',  # to easily use settings in templates
            ],
        },
    },
]
# Add a second, identical template engine except with autoescape off,
# for use when rendering non-HTML templates.
# Use by passing 'using='AUTOESCAPE_OFF' to render or render_to_string.
off = TEMPLATES[0].copy()
off['NAME'] = 'AUTOESCAPE_OFF'
off['OPTIONS']['autoescape'] = False
TEMPLATES.append(off)

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'api.middleware.APISubdomainMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'perma.middleware.AdminAuthMiddleware',
    'ratelimit.middleware.RatelimitMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',  # record request.user for model history
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# If the Django redis cache is configured but unavailable,
# the ratelimiting plugin should allow all requests,
# rather than reject them
RATELIMIT_FAIL_OPEN = True

RATELIMIT_VIEW = 'perma.views.common.rate_limit'
CSRF_FAILURE_VIEW = 'perma.views.error_management.csrf_failure'

ROOT_URLCONF = 'urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'perma.wsgi.application'



INSTALLED_APPS = (
    # built in apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',  # override staticfiles
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # our apps
    'perma',
    'lockss',

    # third party apps
    'ratelimit',
    'mptt',
    'sorl.thumbnail',
    'settings_context_processor',
    'simple_history',  # record model changes
    'taggit',  # model tagging
    'webpack_loader',  # track frontend assets

    # api
    'api',
    'rest_framework',
    'django_filters',

    # django admin -- has to come after our apps for our admin template overrides to work
    'django.contrib.admin',
)

AUTH_USER_MODEL = 'perma.LinkUser'

LOGIN_REDIRECT_URL = '/manage/create/'
LOGIN_URL = '/login'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'perma.utils.AlphaNumericValidator',
    },
]

MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

# subscription packages
TIERS = {
    'Individual': [
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
        }, {
            'period': 'annually',
            'link_limit': 500,
            'rate_ratio': 10
        }
    ],
    'Registrar': [
        {
            'period': 'monthly',
            'link_limit': 'unlimited',
            'rate_ratio': 1
        },{
            'period': 'annually',
            'link_limit': 'unlimited',
            'rate_ratio': 12
        }
    ]
}

# Converted to a decimal.Decimal for use; stored as a string
# to avoid complicating environmental_settings.py
DEFAULT_BASE_RATE = '10.00'
DEFAULT_BASE_RATE_REGISTRAR = '100.00'

# Monthly limit for regular users
DEFAULT_CREATE_LIMIT = 10
DEFAULT_CREATE_LIMIT_PERIOD = 'once'

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
    'single_permalink' : 60 * 60,     # 1hr
    'timegate'     : 0,     # 1hr
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
            'class': 'perma.reporter.CustomAdminEmailHandler'
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'warcprox': {
            'level': 'CRITICAL'
        },
        'requests' : {
            'level': 'WARNING'
        }
    }
}
LOG_PLAYBACK_404 = False

# URLS we should not allow to play back
REFUSE_PLAYBACK = []

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

# Proxy whitelisting:
# If TRUSTED_PROXIES is set, wsgi.py will validate that requests come through these proxies,
# and then set request.META['REMOTE_ADDR'] to match the client IP that comes before the trusted proxy chain in the
# X-Forwarded-For header.
# TRUSTED_PROXIES should be a list of reverse proxies in the chain, where each proxy is a whitelist of IP ranges
# for that proxy. Proxies should be in order from client to server. For example, given:

#    from .utils.helpers import get_cloudflare_ips
#    TRUSTED_PROXIES = [get_cloudflare_ips(CLOUDFLARE_DIR), ['<nginx server ip>']]

# if we see a request like:

#    request.META['REMOTE_ADDR'] = '<nginx server ip>'
#    request.META['HTTP_X_FORWARDED_FOR'] = '<user-supplied junk>, <client ip>, <cloudflare ip>'

# then wsgi.py will make sure that request.META['REMOTE_ADDR'] = '<client ip>'. But if <nginx server ip> or <cloudflare ip>
# fail to match, wsgi.py will return a 400 Bad Request.

TRUSTED_PROXIES = []
CLOUDFLARE_DIR = os.path.join(SERVICES_DIR, 'cloudflare')

# Http header we will use to determine/test/validate a client's IP address.
CLIENT_IP_HEADER = 'REMOTE_ADDR'

# Celery settings
if os.environ.get('DOCKERIZED'):
    BROKER_URL = 'amqp://guest:guest@rabbitmq:5672/'
else:
    BROKER_URL = 'amqp://guest:guest@localhost:5672/'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_SEND_TASK_ERROR_EMAILS = True
# If a task is running longer than five minutes, ask it to shut down
CELERYD_TASK_SOFT_TIME_LIMIT=300
# If a task is running longer than seven minutes, kill it
CELERYD_TASK_TIME_LIMIT = 420
# Estimate of active celery workers
# https://github.com/harvard-lil/perma/issues/2438
# this value will be reset in settings.utils.post_processing
WORKER_COUNT = 2

# Control whether Celery tasks should be run in the background or during a request.
# This should normally be True, but it's handy to not require rabbitmq and celery sometimes.
RUN_TASKS_ASYNC = True

API_SUBDOMAIN = 'api'

# internet archive stuff
UPLOAD_TO_INTERNET_ARCHIVE = False
INTERNET_ARCHIVE_COLLECTION = 'perma_cc'
INTERNET_ARCHIVE_IDENTIFIER_PREFIX = 'perma_cc_'
# Find these at https://archive.org/account/s3.php :
INTERNET_ARCHIVE_ACCESS_KEY = ''
INTERNET_ARCHIVE_SECRET_KEY = ''

from dateutil.relativedelta import relativedelta
LINK_EXPIRATION_TIME = relativedelta(years=2)

# Feature Flag: whether to use Webrecorder or Pywb for playback
ENABLE_WR_PLAYBACK = False

#
# Playback
#
# If set, playbacks must be served from PLAYBACK_HOST.
# On production, this is highly recommended to be different from HOST
HOST = 'localhost'

# The host and port loaded by Perma's iframe during playback
# Must be publicly available
PLAYBACK_HOST = HOST

# The Webrecorder API, used internally by Perma to create WR sessions and upload
# warcs for playback. Not in use if ENABLE_WR_PLAYBACK = False
#
# Use 'http://nginx' and port 80 if running on same docker instance
#
# Or, if WR is on remote machine and/or not running Perma in Docker,
# use the remote host and the port that is being publicly exposed
# and mapped to port 80 on the nginx container by docker-compose. E.g.
# http://remote-webrecorder-host:8089
WR_API = 'http://nginx/api/v1'

# WR Credentials for the public user that stores all public collections
WR_PERMA_USER = 'perma'
WR_PERMA_PASSWORD = os.environ.get('WR_PERMA_PASSWORD', 'TestTest123')


# Time (in seconds) to wait for upload to finalize
# after data fully uploaded to Webreccorder
# Or, assume error if upload not done after this many seconds
WR_REPLAY_UPLOAD_TIMEOUT = 20

# circumventing cloudflare's caching policy
# using different route for timegate
TIMEGATE_WARC_ROUTE = '/warc/timegate'
WARC_ROUTE = '/warc'

# Sorl settings. This relates to our thumbnail creation.
# The prod and dev configs are considerably different. See those configs for details.
THUMBNAIL_ENGINE = 'sorl.thumbnail.engines.wand_engine.Engine'
THUMBNAIL_FORMAT = 'PNG'
THUMBNAIL_COLORSPACE = None
# Temporarily work around for https://github.com/jazzband/sorl-thumbnail/issues/476
TEMPLATE_DEBUG = False

# Relative to MEDIA_ROOT
THUMBNAIL_STORAGE_PATH = 'thumbnails'

# feature flags
SINGLE_LINK_HEADER_TEST = False
ENABLE_BATCH_LINKS = False
# N.B. If True, requires RUN_TASKS_ASYNC = True

# security settings -- set these to true if SSL is available
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False

API_VERSION = 1

TEMPLATE_VISIBLE_SETTINGS = (
    'API_VERSION',
    'SECURE_SSL_REDIRECT',
    'DEBUG',
    'ENABLE_BATCH_LINKS',
    'PLAYBACK_HOST',
    'HOST',
    'ENABLE_WR_PLAYBACK'
)


CAPTURE_BROWSER = 'PhantomJS'  # or 'Chrome' or 'Firefox'
# Default user agent is the Chrome on Linux that's most like PhantomJS 2.1.1.
CAPTURE_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.37 Safari/537.36"

APPEND_SLASH = False

# Schedule celerybeat jobs.
# These will be added to CELERYBEAT_SCHEDULE in settings.utils.post_processing
CELERYBEAT_JOB_NAMES = []


# tests
TEST_RUNNER = 'django.test.runner.DiscoverRunner'  # In Django 1.7, including this silences a warning about tests
USE_SAUCE = False  # Default to local functional tests
SAUCE_USERNAME = None
SAUCE_ACCESS_KEY = None
TESTING = False
REMOTE_SELENIUM = False
REMOTE_SELENIUM_HOST = None

WARC_STORAGE_DIR = 'warcs'  # relative to MEDIA_ROOT


### LOCKSS ###

from datetime import timedelta
ARCHIVE_DELAY = timedelta(hours=24)

USE_LOCKSS_REPLAY = False  # whether to replay captures from LOCKSS, if servers are available
LOCKSS_CONTENT_IPS = ""  # IPs of Perma servers allowed to play back LOCKSS content -- e.g. "10.1.146.0/24;140.247.209.64"
LOCKSS_CRAWL_INTERVAL = "12h"
LOCKSS_QUORUM = 3
LOCKSS_DEBUG_IPS = False

CELERY_ROUTES = {
    'perma.tasks.upload_to_internet_archive': {'queue': 'background'},
    'perma.tasks.delete_from_internet_archive': {'queue': 'background'},
    'perma.tasks.upload_all_to_internet_archive': {'queue': 'background'},
}


ENABLE_AV_CAPTURE = False
RESOURCE_LOAD_TIMEOUT = 45 # seconds to wait for at least one resource to load before giving up on capture
SHUTDOWN_GRACE_PERIOD = 10 # seconds to allow slow threads to finish before we complete the capture job
MAX_PROXY_THREADS = 100

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'bundles/',
        'STATS_FILE': os.path.join(PROJECT_ROOT, 'webpack-stats.json'),
    }
}

# set a default reply-to email address, the same as Django's DEFAULT_FROM_EMAIL
# in production, must be different than the production DEFAULT_FROM_EMAIL
DEFAULT_REPLYTO_EMAIL = 'webmaster@localhost'

# Campaign Monitor (override if you want to actually interact with to
# campaign monitor)
CAMPAIGN_MONITOR_AUTH = {'api_key':'fake'}
CAMPAIGN_MONITOR_REGISTRAR_LIST = 'fake'

# Directs contact form to registrar users under certain circumstances
CONTACT_REGISTRARS = False

TAGGIT_CASE_INSENSITIVE = True

# If technical problems prevent proper analysis of a capture,
# should we default to private?
PRIVATE_LINKS_ON_FAILURE = False
PRIVATE_LINKS_IF_GENERIC_NOARCHIVE = True


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'api.authentication.TokenAuthentication',  # authenticate with ApiKey token
        'rest_framework.authentication.SessionAuthentication',  # authenticate with Django login
    ),
    'NON_FIELD_ERRORS_KEY': 'error',  # default key for {'fieldname': 'error message'} error responses
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination', # enable pagination by default
    'PAGE_SIZE': 300,  # max results per page
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'SEARCH_PARAM': 'q',  # query string key for plain text searches
    'ORDERING_PARAM': 'order_by',  # query string key to specify ordering of results
}

# If using geocoding
# Via https://console.developers.google.com/apis/api/geocoding_backend/overview
GEOCODING_KEY = None

# override django-storages default
AWS_DEFAULT_ACL = 'private'

PERMA_PAYMENTS_TIMESTAMP_MAX_AGE_SECONDS = 120
