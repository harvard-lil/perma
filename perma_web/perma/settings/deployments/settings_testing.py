from settings_common import PROJECT_ROOT

"""
#########
# Setup #
#########
"""

FIXTURE_DIRS = (
    PROJECT_ROOT,
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--nologcapture',
]

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

# Load the api subdomain routes
ROOT_URLCONF = 'api.urls'
SUBDOMAIN_URLCONFS = {}

# Speed up tests with these hacks
# http://www.daveoncode.com/2013/09/23/effective-tdd-tricks-to-speed-up-django-tests-up-to-10x-faster/
PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'api_test_db'
    }
}

DEBUG = False
TEMPLATE_DEBUG = False
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
BROKER_BACKEND = 'memory'
