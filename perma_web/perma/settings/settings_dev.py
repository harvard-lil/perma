from settings_common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# The base location, on disk, where we want to store our generated assets
GENERATED_ASSETS_STORAGE = '/tmp/perma/assets'

# print email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'