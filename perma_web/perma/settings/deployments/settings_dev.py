from settings_common import *

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SERVICES_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, '../services'))

# logging
LOGGING_DIR = os.path.join(SERVICES_DIR, 'logs')
LOGGING['handlers']['default']['filename'] = os.path.join(LOGGING_DIR, 'django.log')
PHANTOMJS_LOG = os.path.join(LOGGING_DIR, 'phantomjs.log')

# user-generated files
MEDIA_ROOT = os.path.join(SERVICES_DIR, 'django/generated_assets/')

# static files
STATIC_ROOT = os.path.join(SERVICES_DIR, 'django/static_assets/')

# print email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'secret'

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Google Analytics
GOOGLE_ANALYTICS_KEY = 'UA-XXXXX-X'
GOOGLE_ANALYTICS_DOMAIN = 'example.com'

# The host we want to display (used when DEBUG=False)
HOST = 'perma.cc'

CELERY_RESULT_BACKEND = 'amqp'

# Folder migration default
FALLBACK_VESTING_ORG_ID = 1


### optional dev packages ###

# django-debug-toolbar
try:
    import debug_toolbar
    INSTALLED_APPS += (
        # Switch to this when we upgrade to Django 1.7.x:
        #'debug_toolbar.apps.DebugToolbarConfig',
        'debug_toolbar',
    )
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': 'perma.utils.show_debug_toolbar'  # we have to override this check because the default depends on IP address, which doesn't work inside Vagrant
    }
except ImportError:
    pass

# django_extensions
try:
    import django_extensions
    INSTALLED_APPS += (
        # Switch to this when we upgrade to Django 1.7.x:
        #'debug_toolbar.apps.DebugToolbarConfig',
        'django_extensions',
    )
except ImportError:
    pass
    
    
# Our Sorl thumbnail stuff. In prod we use Redis, we'll just use
# the local uncached DB here in dev.
THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.cached_db_kvstore.KVStore'