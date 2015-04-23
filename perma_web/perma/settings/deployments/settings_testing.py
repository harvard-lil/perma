import os
from settings_dev import PROJECT_ROOT

#########
# Setup #
#########

FIXTURE_DIRS = (
    PROJECT_ROOT,
)

RUN_FUNCTIONAL_LOCALLY = os.environ.get('RUN_FUNCTIONAL_LOCALLY', 'True') == 'True'

# Uncomment to enable Nose as your test runner
# from settings_dev import INSTALLED_APPS
# import logging
# TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
# INSTALLED_APPS += ("django_nose",)
# logging.getLogger('south').setLevel(logging.INFO)
# logging.getLogger('subdomains.middleware').setLevel(logging.ERROR)

#############
# Overrides #
#############

# Because LiveServerTestCase runs with DEBUG = False
# and some of the mirroring logic depends on that,
# let's add a reliable flag we can use
TESTING = True

RUN_TASKS_ASYNC = False  # avoid sending celery tasks to queue -- just run inline

# django-pipeline causes problems if enabled for tests, so disable it.
# That's not great because it's a less accurate test -- when we upgrade to Django 1.7, consider using
# StaticLiveServerCase instead. http://stackoverflow.com/a/22058962/307769
STATICFILES_STORAGE = 'pipeline.storage.NonPackagingPipelineStorage'
PIPELINE_ENABLED = False

SUBDOMAIN_URLCONFS = {}

###############
# Speed Hacks #
###############
# Reference:
# - https://docs.djangoproject.com/en/1.4/topics/testing/#speeding-up-the-tests
# - http://www.daveoncode.com/2013/09/23/effective-tdd-tricks-to-speed-up-django-tests-up-to-10x-faster/

CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
BROKER_BACKEND = 'memory'

# Note: this is recommended by the Django docs but
# currently conflicts with some of our tests
# PASSWORD_HASHERS = (
#     'django.contrib.auth.hashers.MD5PasswordHasher',
# )

# Using the Django SQLite in-memory DB for testing is faster,
# but threaded tasks won't have access in Django <=1.7
# - https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEST_NAME
# - https://code.djangoproject.com/ticket/12118
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': None
#     }
# }
