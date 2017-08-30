from ..__init__ import *

#########
# Setup #
#########

FIXTURE_DIRS = (
    PROJECT_ROOT,
)

# Uncomment to enable Nose as your test runner
# from settings_dev import INSTALLED_APPS
# import logging
# TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
# INSTALLED_APPS += ("django_nose",)
# logging.getLogger('subdomains.middleware').setLevel(logging.ERROR)

#############
# Overrides #
#############

RUN_TASKS_ASYNC = False  # avoid sending celery tasks to queue -- just run inline

SUBDOMAIN_URLCONFS = {}

TESTING = True


###############
# Speed Hacks #
###############
# Reference:
# - https://docs.djangoproject.com/en/1.4/topics/testing/#speeding-up-the-tests
# - http://www.daveoncode.com/2013/09/23/effective-tdd-tricks-to-speed-up-django-tests-up-to-10x-faster/

CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
BROKER_BACKEND = 'memory'

# faster collectstatic
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

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



# Use production cache setup, except with fakeredis backend
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "REDIS_CLIENT_CLASS": "fakeredis.FakeStrictRedis",
        }
    }
}


# Perma.cc encryption keys for communicating with Perma-Payments
# generated using perma_payments.security.generate_public_private_keys
# SECURITY WARNING: keep the production secret key secret!
PERMA_PAYMENTS_ENCRYPTION_KEYS = {
    'id': 1,
    'perma_secret_key': b'\xa3]m\xee\x81\xac&\x7fSA\xf7j\xa9N\xfbq\x97\x8b\xd7\xe6\xae\x85\x03\x16EO\xa0u\x9a\xecW\x9d',
    'perma_public_key': b'fi\x16S\xa0\x1dBSk\x0c"\xcd#^x\x1d!\x87\xf7\xa8\xe3\xb3mT\x03r\xbeb\x9a\x9e\xcdh',
    'perma_payments_public_key': b'\x0co(\xf5\xc4\xb9.\x07\xae\xbb\xb5\xc0\x17O,\xc3F\x8e_\xb9\x89\x16\xefSTK]\xae\xb0P\x1c6',
}
PERMA_PAYMENTS_TIMESTAMP_MAX_AGE_SECONDS = 120
