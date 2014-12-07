from settings_dev import PROJECT_ROOT, INSTALLED_APPS

"""
#########
# Setup #
#########
"""

FIXTURE_DIRS = (
    PROJECT_ROOT,
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
INSTALLED_APPS += ("django_nose",)

"""
#############
# Overrides #
#############
"""

RUN_TASKS_ASYNC = False  # avoid sending celery tasks to queue -- just run inline

# django-pipeline causes problems if enabled for tests, so disable it.
# That's not great because it's a less accurate test -- when we upgrade to Django 1.7, consider using
# StaticLiveServerCase instead. http://stackoverflow.com/a/22058962/307769
STATICFILES_STORAGE = 'pipeline.storage.NonPackagingPipelineStorage'
PIPELINE_ENABLED = False

SUBDOMAIN_URLCONFS = {}

"""
###############
# Speed Hacks #
###############

Reference:
- https://docs.djangoproject.com/en/1.4/topics/testing/#speeding-up-the-tests
- http://www.daveoncode.com/2013/09/23/effective-tdd-tricks-to-speed-up-django-tests-up-to-10x-faster/
"""

# Note: this is recommended by the Django docs but
# currently conflicts with some of our tests
# PASSWORD_HASHERS = (
#     'django.contrib.auth.hashers.MD5PasswordHasher',
# )

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': None
#     }
# }

CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
BROKER_BACKEND = 'memory'
