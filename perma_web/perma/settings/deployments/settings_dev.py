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

# warc_server uses this to make requests -- it should point back to Django's /cdx view
CDX_SERVER_URL = 'http://127.0.0.1:8000/cdx'

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
