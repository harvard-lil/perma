# settings used for playwright tests in CI
from .deployments.settings_dev import *


DEBUG = False
RUN_TASKS_ASYNC = False

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
