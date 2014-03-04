from settings_common import *

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SERVICES_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, '../services'))

# The base location, on disk, where we want to store our generated assets
GENERATED_ASSETS_STORAGE = os.path.join(SERVICES_DIR, 'django/generated_assets')

# Additional locations of static files
STATICFILES_DIRS = (
    'static',
    GENERATED_ASSETS_STORAGE

    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# print email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# warc_server uses this to make requests -- it should point back to Django's /cdx view
CDX_SERVER_URL = 'http://127.0.0.1:8000/cdx'

STATIC_ROOT = os.path.join(SERVICES_DIR, 'django/static_assets')

PHANTOMJS_BINARY = "/usr/bin/phantomjs"

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'secret'

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Instapaper credentials
INSTAPAPER_KEY = 'key'
INSTAPAPER_SECRET = 'secret'
INSTAPAPER_USER = 'user@example.com'
INSTAPAPER_PASS = 'pass'

# Google Analytics
GOOGLE_ANALYTICS_KEY = 'UA-XXXXX-X'
GOOGLE_ANALYTICS_DOMAIN = 'example.com'
