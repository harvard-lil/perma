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

SUBDOMAIN_URLCONFS = {}

DEBUG = False
TESTING = True

ADMINS = (
    ("Admin's Name", 'admin@example.com'),
)

AWS_STORAGE_BUCKET_NAME += '-test'

###############
# Speed Hacks #
###############
# Reference:
# - https://docs.djangoproject.com/en/1.4/topics/testing/#speeding-up-the-tests
# - http://www.daveoncode.com/2013/09/23/effective-tdd-tricks-to-speed-up-django-tests-up-to-10x-faster/

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://localhost/'

# faster collectstatic
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Work around for https://github.com/jamesls/fakeredis/issues/234
DJANGO_REDIS_CONNECTION_FACTORY = 'perma.tests.utils.FakeConnectionFactory'

# Use production cache setup, except with fakeredis backend
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/0",
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

PURCHASE_URL = '/purchase/'
PURCHASE_HISTORY_URL = '/purchase-history/'
ACKNOWLEDGE_PURCHASE_URL = '/acknowledge-purchase/'
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
