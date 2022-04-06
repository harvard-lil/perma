# settings used for playwright tests in CI
from .deployments.settings_dev import *


DEBUG = False

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
