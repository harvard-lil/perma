import os

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

SUBSCRIBE_URL = '/subscribe/'
CANCEL_URL = '/cancel-request/'
SUBSCRIPTION_STATUS_URL = '/subscription/'
UPDATE_URL = '/update/'
CHANGE_URL = '/change/'


# lots of subscription packages, to be thorough
TIERS = {
    'Individual': [
        {
            'period': 'monthly',
            'link_limit': 10,
            'rate_ratio': 1
        },{
            'period': 'monthly',
            'link_limit': 100,
            'rate_ratio': 2.5
        },{
            'period': 'monthly',
            'link_limit': 500,
            'rate_ratio': 10
        }, {
            'period': 'annually',
            'link_limit': 500,
            'rate_ratio': 10
        }
    ],
    'Registrar': [
        {
            'period': 'monthly',
            'link_limit': 10,
            'rate_ratio': 0.1
        },{
            'period': 'monthly',
            'link_limit': 25,
            'rate_ratio': 0.25
        },{
            'period': 'monthly',
            'link_limit': 100,
            'rate_ratio': 1
        },{
            'period': 'monthly',
            'link_limit': 500,
            'rate_ratio': 5
        },{
            'period': 'monthly',
            'link_limit': 'unlimited',
            'rate_ratio': 10
        },{
            'period': 'annually',
            'link_limit': 'unlimited',
            'rate_ratio': 120
        }
    ]
}

REMOTE_SELENIUM = True
if REMOTE_SELENIUM:
    if os.environ.get('DOCKERIZED'):
        HOST = 'web:80'
        PLAYBACK_HOST = 'web:80'
        ALLOWED_HOSTS.append('web')
        REMOTE_SELENIUM_HOST = 'selenium'
    else:
        HOST = 'perma.kresnanusantara.co.id:80'
        PLAYBACK_HOST = 'perma-archives.kresnanusantara.co.id:80'
        REMOTE_SELENIUM_HOST = 'localhost'


ENABLE_WR_PLAYBACK = True
if ENABLE_WR_PLAYBACK:
    assert REMOTE_SELENIUM, "WR Playback must be tested with REMOTE_SELENIUM = True"
    if os.environ.get('DOCKERIZED'):
        WR_API = 'http://nginx/api/v1'
        PLAYBACK_HOST = 'nginx:81'
    else:
        WR_API = 'http://perma-archives.kresnanusantara.co.id:8089/api/v1'
        PLAYBACK_HOST = 'perma-archives.kresnanusantara.co.id:8092'
