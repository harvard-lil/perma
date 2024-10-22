# Core settings used by all deployments.
import os, sys
from copy import deepcopy

# PROJECT_ROOT is the absolute path to the perma_web folder
# We determine this robustly thanks to http://stackoverflow.com/a/2632297
this_module = sys.executable if hasattr(sys, "frozen") else __file__
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(this_module))))
SERVICES_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, '../services'))
JS_WACZ_DIR = os.path.abspath(os.path.join(SERVICES_DIR, 'js-wacz'))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'perma',
        'USER': 'perma',
        'PASSWORD': 'password',
        'HOST': 'db',
        'PORT': 5432,
    },
}

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

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

STORAGES = {
    "default": {
        "BACKEND": 'perma.storage_backends.S3MediaStorage',
        "OPTIONS": {
            "signature_version": 's3v4',
            "default_acl": 'private'
        }
    },
    "secondary": {
        "BACKEND": 'perma.storage_backends.S3MediaStorage',
        "OPTIONS": {
            "signature_version": 's3v4',
            "default_acl": 'private'
        }
    },
    "staticfiles": {
        "BACKEND": 'perma.storage_backends.StaticStorage',
    },
}

# static files
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static-collected')                # where to store collected static files
STATIC_URL = '/static/'         # URL to serve static files

# where to look for static files (in addition to app/static/)
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static'),
)

STATICFILES_FINDERS = (         # how to look for static files
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'bundles/',
        'STATS_FILE': os.path.join(PROJECT_ROOT, 'webpack-stats.json'),
    }
}

# user-generated files / default_storage config
MEDIA_URL = '/this-setting-is-not-in-use-in-any-deployments/'
MEDIA_ROOT ='generated/'
WARC_STORAGE = 'default'
WARC_STORAGE_DIR = 'warcs'  # relative to MEDIA_ROOT
WARC_PRESIGNED_URL_EXPIRES = 15 * 60
WACZ_STORAGE = 'secondary'
WACZ_STORAGE_DIR = 'waczs'
WACZ_PRESIGNED_URL_EXPIRES = 15 * 60

ARCHIVE_FORMATS = ['warc']

WARC_TO_WACZ_ON_DEMAND = False
WARC_TO_WACZ_ON_DEMAND_SIZE_LIMIT = 1024 * 1024 * 100 # 100 MB

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

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'perma.middleware.APISubdomainMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'perma.middleware.AdminAuthMiddleware',
    'ratelimit.middleware.RatelimitMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',  # record request.user for model history
    'waffle.middleware.WaffleMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # AxesMiddleware should be the last middleware in the MIDDLEWARE list.
    # It only formats user lockout messages and renders Axes lockout responses
    # on failed user authentication attempts from login views.
    # If you do not want Axes to override the authentication response
    # you can skip installing the middleware and use your own views.
    'axes.middleware.AxesMiddleware',
    'api.middleware.CORSMiddleware'
)

ROOT_URLCONF = 'urls'

APPEND_SLASH = False

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'perma.wsgi.application'

INSTALLED_APPS = (
    # built in apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.postgres',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',  # override staticfiles
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # our apps
    'perma',
    'reporting',

    # third party apps
    'ratelimit',
    'settings_context_processor',
    'simple_history',  # record model changes
    'taggit',  # model tagging
    'webpack_loader',  # track frontend assets
    'axes',  # limit login attempts
    'django_json_widget',
    'waffle',  # feature flags

    # api
    'api',
    'rest_framework',
    'django_filters',

    # django admin -- has to come after our apps for our admin template overrides to work
    'django.contrib.admin',
)

CSRF_FAILURE_VIEW = 'perma.views.error_management.csrf_failure'
MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'
TAGGIT_CASE_INSENSITIVE = True

# Security Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_NAME = '__Host-sessionid'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SAMESITE = 'Lax'
# This defaults to 'SAMEORIGIN' w/ Django 2, but was changed to 'DENY' in Django 3
X_FRAME_OPTIONS = 'DENY'
REQUIRE_JS_FORM_SUBMISSIONS = True

#
# Authentication
#
AUTH_USER_MODEL = 'perma.LinkUser'
LOGIN_REDIRECT_URL = '/manage/create/'
LOGIN_URL = 'user_management_limited_login'

# Axes, fundamental integration
AUTHENTICATION_BACKENDS = [
    # AxesBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    'axes.backends.AxesBackend',

    # Django ModelBackend is the default authentication backend.
    'django.contrib.auth.backends.ModelBackend',
]
AXES_LOCKOUT_TEMPLATE = 'registration/login_attempts_exceeded.html'

# Axes, configure behavior
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 6
AXES_LOCK_OUT_AT_FAILURE = True
AXES_COOLOFF_MINUTES = 30
AXES_COOLOFF_TIME = 'perma.utils.cooloff_time'
AXES_ONLY_USER_FAILURES = True  # If True, only lock based on username, and never lock based on IP if attempts exceed the limit. Otherwise utilize the existing IP and user locking logic. Default: False
AXES_RESET_ON_SUCCESS = True  # If True, a successful login will reset the number of failed logins. Default: False

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

# 3 days, in seconds
PASSWORD_RESET_TIMEOUT = 3 * 24 * 60 * 60

#
# Subscription packages/Payments
#

PERMA_PAYMENTS_TIMEOUT = 2
PERMA_PAYMENTS_TIMESTAMP_MAX_AGE_SECONDS = 120
PERMA_PAYMENTS_IN_MAINTENANCE = False

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

SPECIAL_UNLIMITED_LINKS_FOR_REGISTRAR = []

BONUS_PACKAGES = [
    {
        'link_quantity': 10,
        'price': '15.00'
    },
    {
        'link_quantity': 100,
        'price': '30.00'
    },
        {
        'link_quantity': 500,
        'price': '125.00'
    }
]

# Monthly limit for regular users
DEFAULT_CREATE_LIMIT = 10
DEFAULT_CREATE_LIMIT_PERIOD = 'once'

#
# Rate limits
#
MINUTE_LIMIT = '6000/m'
HOUR_LIMIT = '100000/h'
DAY_LIMIT = '500000/d'
REGISTER_MINUTE_LIMIT = '600/m'
LOGIN_MINUTE_LIMIT = '5000/m'
CONTACT_MINUTE_LIMIT = MINUTE_LIMIT
CONTACT_HOUR_LIMIT = HOUR_LIMIT
CONTACT_DAY_LIMIT = DAY_LIMIT
REPORT_MINUTE_LIMIT = MINUTE_LIMIT
REPORT_HOUR_LIMIT = HOUR_LIMIT
REPORT_DAY_LIMIT = DAY_LIMIT

# If the Django redis cache is configured but unavailable,
# the ratelimiting plugin should allow all requests,
# rather than reject them
RATELIMIT_FAIL_OPEN = True
RATELIMIT_VIEW = 'perma.views.common.rate_limit'

#
# Django cache
#
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
CACHE_MAX_AGES = {
    'single_permalink' : 60 * 60,     # 1hr
    'timegate'     : 0,
    'timemap'      : 60 * 30,         # 30mins
}

# Dashboard user lists
MAX_USER_LIST_SIZE = 50

# Logging
from django.utils.log import DEFAULT_LOGGING
LOGGING = deepcopy(DEFAULT_LOGGING)
LOGGING['handlers'] = {
    **LOGGING['handlers'],
    # log everything to console on both dev and prod
    'console': {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'standard',
    },
    # custom error email template
    'mail_admins': {
        'level': 'ERROR',
        'filters': ['require_debug_false'],
        'class': 'perma.reporter.CustomAdminEmailHandler'
    },
    # log to file
    'file': {
        'level':'INFO',
        'class':'logging.handlers.RotatingFileHandler',
        'filename': '/tmp/perma.log',
        'maxBytes': 1024*1024*5, # 5 MB
        'backupCount': 5,
        'formatter':'standard',
    },
}
LOGGING['loggers'] = {
    **LOGGING['loggers'],
    # only show warnings for third-party apps
    '': {
        'level': 'WARNING',
        'handlers': ['console', 'mail_admins', 'file'],
    },
    # disable django's built-in handlers to avoid double emails
    'django': {
        'level': 'WARNING'
    },
    'django.request': {
        'level': 'ERROR'
    },
    'warcprox': {
        'level': 'CRITICAL'
    },
    # prevent IA's own error emails, in favor of our own handling
    'internetarchive': {
        'level': 'CRITICAL'
    },
    'celery.django': {
        'level': 'INFO',
        'handlers': ['console', 'mail_admins', 'file'],
    },
    # show info for our first-party apps
    **{
        app_name: {'level': 'INFO'}
        for app_name in ('api', 'perma',)
    },
    # show info for our invoke tasks
    'tasks': {
        'level': 'INFO'
    }
}
LOGGING['formatters'] = {
    **LOGGING['formatters'],
    'standard': {
        'format': '%(asctime)s [%(levelname)s] %(filename)s %(lineno)d: %(message)s'
    },
}

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

#
# Celery settings
#
CELERY_BROKER_URL = 'redis://perma-redis:6379/1'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
# If a task is running longer than five minutes, ask it to shut down
CELERY_TASK_SOFT_TIME_LIMIT=300
# If a task is running longer than seven minutes, kill it
CELERY_TASK_TIME_LIMIT = 420

CELERY_TASK_ROUTES = {
    'perma.celery_tasks.sync_subscriptions_from_perma_payments': {'queue': 'background'},
    'perma.celery_tasks.cache_playback_status_for_new_links': {'queue': 'background'},
    'perma.celery_tasks.cache_playback_status': {'queue': 'background'},
    'perma.celery_tasks.populate_warc_size_fields': {'queue': 'background'},
    'perma.celery_tasks.populate_warc_size': {'queue': 'background'},
    'perma.celery_tasks.populate_wacz_size': {'queue': 'background'},
    'perma.celery_tasks.fix_cached_folder_paths': {'queue': 'background'},
    'perma.celery_tasks.fix_cached_folder_path': {'queue': 'background'},
    # the 'ia' queue is for tasks that alter or may alter Internet Archive's records
    'perma.celery_tasks.upload_link_to_internet_archive': {'queue': 'ia'},
    'perma.celery_tasks.delete_link_from_daily_item': {'queue': 'ia'},
    # the 'ia-readonly' queue is for internal tasks that only affect our database
    'perma.celery_tasks.queue_file_uploaded_confirmation_tasks': {'queue': 'ia-readonly'},
    'perma.celery_tasks.confirm_file_uploaded_to_internet_archive': {'queue': 'ia-readonly'},
    'perma.celery_tasks.queue_file_deleted_confirmation_tasks': {'queue': 'ia-readonly'},
    'perma.celery_tasks.confirm_file_deleted_from_daily_item': {'queue': 'ia-readonly'},
    'perma.celery_tasks.conditionally_queue_internet_archive_uploads_for_date_range': {'queue': 'ia-readonly'},
    'perma.celery_tasks.queue_internet_archive_deletions': {'queue': 'ia-readonly'},
    'perma.celery_tasks.convert_warc_to_wacz': {'queue': 'wacz-conversion'},
    'perma.celery_tasks.deactivate_expired_sponsored_users': {'queue': 'background'},
    'perma.celery_tasks.warn_expiring_sponsored_users': {'queue': 'background'},
    'perma.celery_tasks.remove_expired_organization_user_affiliations': {'queue': 'background'},
    'perma.celery_tasks.warn_expiring_organization_users': {'queue': 'background'}
}

# Schedule celerybeat jobs.
# These will be added to CELERY_BEAT_SCHEDULE in settings.utils.post_processing
CELERY_BEAT_JOB_NAMES = []

# Internet Archive stuff
INTERNET_ARCHIVE_MAX_UPLOAD_SIZE = 1024 * 1024 * 100
INTERNET_ARCHIVE_COLLECTION = 'perma_cc'
INTERNET_ARCHIVE_IDENTIFIER_PREFIX = 'perma_cc_'
INTERNET_ARCHIVE_DAILY_IDENTIFIER_PREFIX = 'daily_perma_cc_'
# Find these at https://archive.org/account/s3.php :
INTERNET_ARCHIVE_ACCESS_KEY = ''
INTERNET_ARCHIVE_SECRET_KEY = ''
# Rate limiting
INTERNET_ARCHIVE_MAX_SIMULTANEOUS_UPLOADS = 499  # as of 2023-03-21, this is our "accesskey_ration"
INTERNET_ARCHIVE_PERMITTED_PROXIMITY_TO_GLOBAL_RATE_LIMIT = 500
INTERNET_ARCHIVE_PERMITTED_PROXIMITY_TO_RATE_LIMIT = 50
INTERNET_ARCHIVE_RETRY_FOR_RATELIMITING_LIMIT = None
INTERNET_ARCHIVE_RETRY_FOR_ERROR_LIMIT = 2
INTERNET_ARCHIVE_EXCEPTION_IF_RETRIES_EXCEEDED = False
INTERNET_ARCHIVE_ITEM_LOCK_RETRIES = 4
INTERNET_ARCHIVE_RETRY_FOR_CONFIRMATION_CONNECTION_ERROR = 3
INTERNET_ARCHIVE_UPLOAD_MAX_TIMEOUTS = None
# Other
INTERNET_ARCHIVE_EXCEPTION_IF_NO_ITEM = False
INTERNET_ARCHIVE_UPLOAD_MAX_TMEOUTS = 2

#
# Hosts
#

HOST = 'perma.test:8000'
ALLOWED_HOSTS = ['perma.test', 'api.perma.test']
API_SUBDOMAIN = 'api'

#
# API
#

API_VERSION = 1
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

#
# Playback
#

PLAYBACK_HOST = 'rejouer.perma.test:8080'


#
# Capture
#
CAPTURE_ENGINE = 'scoop-api'  # perma|scoop-api
PRIVATE_BY_POLICY_DOMAINS = []
SCOOP_API_KEY = None
SCOOP_API_URL = None
SCOOP_API_USERAGENT = 'Perma capture worker'
SCOOP_POLL_FREQUENCY = 0.5
SCOOP_POLL_NETWORK_ERROR_LIMIT = 10

# Max file size (for our downloads)
MAX_ARCHIVE_FILE_SIZE = 1024 * 1024 * 100  # 100 MB

# Seconds to wait for website to respond during URL validation:
# set to the Scoop API's own 502 threshold, currently 60s, plus two seconds for network conditions
RESOURCE_LOAD_TIMEOUT = 60 + 2

# We're finding that warcs aren't always available for download from S3
# instantly, immediately after upload. How long do we want to wait for S3
# to catch up, during first playback, before raising an error?
WARC_AVAILABLE_RETRIES = 9
CHECK_WARC_BEFORE_PLAYBACK = False

# tests
TEST_RUNNER = 'django.test.runner.DiscoverRunner'  # In Django 1.7, including this silences a warning about tests
TESTING = False

### MIRRORS ###

from datetime import timedelta
ARCHIVE_DELAY = timedelta(hours=24)

#
# Email
#

# set a default reply-to email address, the same as Django's DEFAULT_FROM_EMAIL
# in production, must be different than the production DEFAULT_FROM_EMAIL
DEFAULT_REPLYTO_EMAIL = 'webmaster@localhost'

# Campaign Monitor (override if you want to actually interact with to
# campaign monitor)
CAMPAIGN_MONITOR_AUTH = {'api_key':'fake'}
CAMPAIGN_MONITOR_REGISTRAR_LIST = 'fake'

# Directs contact form to registrar users under certain circumstances
CONTACT_REGISTRARS = True

# Virus Scanning
SCAN_UPLOADS = False
SCAN_URL = ''

# Analytics
USE_ANALYTICS = False
USE_ANALYTICS_VIEWS = [
    'landing',
    'about',
    'copyright_policy',
    'terms_of_service',
    'privacy_policy',
    'return_policy',
    'contingency_plan',
    'docs',
    'docs_perma_link_creation',
    'docs_libraries',
    'docs_faq',
    'docs_accounts',
    'dev_docs',
    'sign_up',
    'sign_up_courts',
    'sign_up_firms',
    'sign_up_libraries'
]

# If USE_SENTRY is True, SENTRY_DSN must be set
USE_SENTRY = False
SENTRY_DSN = ''
SENTRY_ENVIRONMENT = 'dev'
SENTRY_TRACES_SAMPLE_RATE = 1.0
SENTRY_SEND_DEFAULT_PII = False

# Before deployment, we suppress the addition of new capture jobs when this file is present
DEPLOYMENT_SENTINEL = '/tmp/perma-deployment-pending'

# Which settings should be available in all Django templates,
# without needing to explicitly pass them via the view?
TEMPLATE_VISIBLE_SETTINGS = (
    'API_VERSION',
    'SECURE_SSL_REDIRECT',
    'DEBUG',
    'HOST',
    'USE_ANALYTICS',
    'USE_ANALYTICS_VIEWS',
    'USE_SENTRY',
    'SENTRY_DSN',
    'SENTRY_ENVIRONMENT',
    'SENTRY_TRACES_SAMPLE_RATE',
    'PLAYBACK_HOST'
)
