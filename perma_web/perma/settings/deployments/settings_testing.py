from .settings_dev import *

#########
# Setup #
#########

FIXTURE_DIRS = (
    PROJECT_ROOT,
)


#############
# Overrides #
#############

RUN_TASKS_ASYNC = False  # avoid sending celery tasks to queue -- just run inline

SUBDOMAIN_URLCONFS = {}

DEBUG = False
TESTING = True

ADMINS = (
    ("Admin's Name", 'admin@example.com'),
)


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
    'perma_secret_key': 'o11t7oGsJn9TQfdqqU77cZeL1+auhQMWRU+gdZrsV50=',
    'perma_public_key': 'ZmkWU6AdQlNrDCLNI154HSGH96jjs21UA3K+YpqezWg=',
    'perma_payments_public_key': 'DG8o9cS5Lgeuu7XAF08sw0aOX7mJFu9TVEtdrrBQHDY=',
}
PERMA_PAYMENTS_TIMESTAMP_MAX_AGE_SECONDS = 120

SUBSCRIBE_URL = '/subscribe/'
CANCEL_URL = '/cancel-request/'
SUBSCRIPTION_STATUS_URL = '/subscription/'
UPDATE_URL = '/update/'
