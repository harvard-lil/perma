# settings used for continuous integration test server

from settings_dev import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

DATABASES['default']['NAME'] = ''
DATABASES['default']['USER'] = ''
DATABASES['default']['PASSWORD'] = ''

# To populate the from field of emails sent from Perma
DEFAULT_FROM_EMAIL = 'email@example.com'

# The host we want to display (used when DEBUG=False)
HOST = 'perma.cc'

# Where we store our generated assets (phantomjs images)
GENERATED_ASSETS_STORAGE = '/tmp/perma/assets'

# Additional locations of static files
STATICFILES_DIRS = (
    'static',
    GENERATED_ASSETS_STORAGE

    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)