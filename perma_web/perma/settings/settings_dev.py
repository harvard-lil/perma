from settings_common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# The base location, on disk, where we want to store our generated assets
GENERATED_ASSETS_STORAGE = '/tmp/perma/assets'

# Additional locations of static files
STATICFILES_DIRS = (
    'static',
    GENERATED_ASSETS_STORAGE

    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025