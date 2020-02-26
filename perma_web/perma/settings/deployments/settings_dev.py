from .settings_common import *

import os

DEBUG = True

#
# HOSTS
#
HOST = 'perma.test:8000'
PLAYBACK_HOST = 'perma-archives.test:8092'
# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['perma.test', 'api.perma.test']

# logging
LOGGING_DIR = os.path.join(SERVICES_DIR, 'logs')
LOGGING['handlers']['file']['filename'] = os.path.join(LOGGING_DIR, 'django.log')
PHANTOMJS_LOG = os.path.join(LOGGING_DIR, 'phantomjs.log')

# user-generated files
MEDIA_ROOT = os.path.join(SERVICES_DIR, 'django/generated_assets/')

# static files
STATIC_ROOT = os.path.join(SERVICES_DIR, 'django/static_assets/')

# print email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'secret'

# Google Analytics
GOOGLE_ANALYTICS_KEY = 'UA-XXXXX-X'
GOOGLE_ANALYTICS_DOMAIN = 'example.com'

CELERY_RESULT_BACKEND = None

### optional dev packages ###

# django-debug-toolbar
try:
    import debug_toolbar  # noqa
    INSTALLED_APPS += (
        'debug_toolbar',
    )
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': 'perma.utils.show_debug_toolbar'  # we have to override this check because the default depends on IP address, which doesn't work inside Vagrant
    }
except ImportError:
    pass

# django_extensions
try:
    import django_extensions  # noqa
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


#
# Perma Payments
#
SUBSCRIBE_URL = 'http://localhost/subscribe/'
CANCEL_URL = 'http://localhost/cancel-request/'
SUBSCRIPTION_STATUS_URL = 'http://perma-payments/subscription/'
UPDATE_URL = 'http://localhost/update/'
CHANGE_URL = 'http://localhost/change/'

# Perma.cc encryption keys for communicating with Perma-Payments
# generated using perma_payments.security.generate_public_private_keys
# SECURITY WARNING: keep the production secret key secret!
# These keys are just for local development, and are safe to commit to the repo
PERMA_PAYMENTS_ENCRYPTION_KEYS = {
    'id': 1,
    'perma_secret_key': "hneZHHft4QieiNmyVPfyYFJs3toRgixbiTqSQKJ1r2E=",
    'perma_public_key': "+Y3Kni4Pm+5kWFJgsBL28TyKcgciQdPofRsTwUKaVSE=",
    'perma_payments_public_key': "FhfWRc3QmLzG9SY+QwvTNMT9vcACNzpcMyvNSxKg0jA="
}
