from settings_common import *

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SERVICES_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, '../services'))

# logging
LOGGING_DIR = os.path.join(SERVICES_DIR, 'logs')
LOGGING['handlers']['default']['filename'] = os.path.join(LOGGING_DIR, 'django.log')
PHANTOMJS_LOG = os.path.join(LOGGING_DIR, 'phantomjs.log')

# user-generated files
MEDIA_ROOT = os.path.join(SERVICES_DIR, 'django/generated_assets/')

# static files
STATIC_ROOT = os.path.join(SERVICES_DIR, 'django/static_assets/')

# print email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'secret'

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Google Analytics
GOOGLE_ANALYTICS_KEY = 'UA-XXXXX-X'
GOOGLE_ANALYTICS_DOMAIN = 'example.com'

# The host we want to display (used when DEBUG=False)
HOST = 'perma.cc'

CELERY_RESULT_BACKEND = 'amqp'

# Folder migration default
FALLBACK_VESTING_ORG_ID = 1

# Dummy GPG keys for mirror communication.
GPG_PUBLIC_KEY = u'-----BEGIN PGP PUBLIC KEY BLOCK-----\nVersion: GnuPG v1\n\nmQENBFRspV4BCACcICCn2CKMHYNIw6F5OBTjKzJAwqkG7d0TJ4IThG2w7AIy4RVg\nAjfbqXcxthfX5Z4274Qeh6b72rcO1I/s437kk1gVQ+ghpU9xUMgJCbPGrA2I332Q\nCrJhc2YIEkh/rXXaGPzLpnpLbCPglyUGjdvqwWV5zB8S3dkfhBqUZ/61Tk4nIx9p\ngJJJytUnLlWnMesJkfNmCeVTdpllikdRe6Rm+Rg5dcWhWNfo5bv5Tw8ouUTHnVCT\n1XUic1LS+o1aPlbFswdM4DRvudrF1BarzuuDLvJU3Ubo508xxpRqiTiAvS1l1hd9\nr/QN42RZ1AdAxt5YawFfIH2tSjUV6qxM2aRvABEBAAG0IUF1dG9nZW5lcmF0ZWQg\nS2V5IDxqY0BKYWNrLmxvY2FsPokBOAQTAQIAIgUCVGylXgIbLwYLCQgHAwIGFQgC\nCQoLBBYCAwECHgECF4AACgkQ/1k3sACLNwzqDQf/XkNzcg+DW6maea3YlZ3rKj/9\nbVIb01yRAcj4rrtxQgMx6q2sdU6BjMkT6bHUZyYZPV4BVwT0PuhZ95ojR0rmEIoO\nRPTPlBQwns+pM6ZRvW9cuF3s+gaM/oXCspt2ffrn26Riy0awcZaGde0FHxfTsrOl\nW5I5LyzmpQMEeHAAJ3DiEez/fnXUY5GPuzXTHTaIkWubCgvbk+3GCRf4Tgo5KUmH\nV/GY4VSzre+QsyOxZKd5HO+8uU1MT2zXBBBzuEb3QYzySZom8oPkaIlwrw41w0dm\nVig6OXUVn6syFO+Tfcv3NqqD3r03TrVnhvXAusboYyhzH/ydCGmWYiu+a/Vi1w==\n=f7O5\n-----END PGP PUBLIC KEY BLOCK-----\n'
GPG_PRIVATE_KEY = u'-----BEGIN PGP PRIVATE KEY BLOCK-----\nVersion: GnuPG v1\n\nlQOXBFRspV4BCACcICCn2CKMHYNIw6F5OBTjKzJAwqkG7d0TJ4IThG2w7AIy4RVg\nAjfbqXcxthfX5Z4274Qeh6b72rcO1I/s437kk1gVQ+ghpU9xUMgJCbPGrA2I332Q\nCrJhc2YIEkh/rXXaGPzLpnpLbCPglyUGjdvqwWV5zB8S3dkfhBqUZ/61Tk4nIx9p\ngJJJytUnLlWnMesJkfNmCeVTdpllikdRe6Rm+Rg5dcWhWNfo5bv5Tw8ouUTHnVCT\n1XUic1LS+o1aPlbFswdM4DRvudrF1BarzuuDLvJU3Ubo508xxpRqiTiAvS1l1hd9\nr/QN42RZ1AdAxt5YawFfIH2tSjUV6qxM2aRvABEBAAEAB/jEFt/F+IeFpAU5zZHP\nvWonzkJ9VUGf5VEI/KVlcZoxF9w19X4D2RwoGOK8oKg3wOJLFLCDLmQiQgUIxKMV\n736Vv0H19bX+YN0SBxOn3jMfzAG2A84FdT6JK4fr4LywPC9R41XbvGFfp5fzBiiF\nrOOQZOqgVvGAkzAja9efqAtDclpecZinyjfdUXl5P6b+IrOvVzCMjNRj+HdJgl+B\nRkLK7KB1mHdVf4oTrNS/K6Wgs0lFFtnoCHd1SXNyww16n3bF/jEk2C5EVGEjci5S\nb5ELAt5w8J6QfGcw6hKUThSbD+iZZqIFU8L+y8qQeYCqDzsKeIGh9rtil/otFKEt\nY2EEAMBqhMvSMpXktyNOt5d6Lklg0jTQRV/HxhENwphA0NR+a7BXVR/avEbudoR4\n6HIpT9LsUgkty5GIFxoecBfogkoWtmVUalzYb/WL8yy76RWKP2EyXTp0Fn9MGkE5\ns/+VzQIngIU07K9/LbBKpuTDUMHffMm3eqfcMz/oMb+iTphhBADPt5kt1Av/HMwv\nxIzeRr3ukrZRLycI3mbusmqNHxqPBteP7UJNQMzX0ATKW8FCqBTay1yQR6O/gUtk\nTt1cwMEbtGRcG5ks/2DHzmQcWwbG+EDM8L/Nlo5dCBTVW7qGL1SCqVYitJb2b8gE\nTu3fXzKL2Ds1B2Ag5JtXez5U+8suzwP/etqnre3d3nwiz6ddMr10q/t5kDukwtHd\nLbwSz5maksiu10LXOcPif9cwyosAm9mfk2NyGxJrRjYW3ojSjle4g19kMVnqUwnh\noNba3dC/prY9PUTlt8W3Qs8Tt/E6MQvEaD4x23vctvl7wW3KVrexWbLy8+ez38vL\nAbPrPOl2KzdHMLQhQXV0b2dlbmVyYXRlZCBLZXkgPGpjQEphY2subG9jYWw+iQE4\nBBMBAgAiBQJUbKVeAhsvBgsJCAcDAgYVCAIJCgsEFgIDAQIeAQIXgAAKCRD/WTew\nAIs3DOoNB/9eQ3NyD4NbqZp5rdiVnesqP/1tUhvTXJEByPiuu3FCAzHqrax1ToGM\nyRPpsdRnJhk9XgFXBPQ+6Fn3miNHSuYQig5E9M+UFDCez6kzplG9b1y4Xez6Boz+\nhcKym3Z9+ufbpGLLRrBxloZ17QUfF9Oys6VbkjkvLOalAwR4cAAncOIR7P9+ddRj\nkY+7NdMdNoiRa5sKC9uT7cYJF/hOCjkpSYdX8ZjhVLOt75CzI7Fkp3kc77y5TUxP\nbNcEEHO4RvdBjPJJmibyg+RoiXCvDjXDR2ZWKDo5dRWfqzIU75N9y/c2qoPevTdO\ntWeG9cC6xuhjKHMf/J0IaZZiK75r9WLX\n=Lgx+\n-----END PGP PRIVATE KEY BLOCK-----\n'

### optional dev packages ###

# django-debug-toolbar
try:
    import debug_toolbar
    INSTALLED_APPS += (
        # Switch to this when we upgrade to Django 1.7.x:
        #'debug_toolbar.apps.DebugToolbarConfig',
        'debug_toolbar',
    )
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': 'perma.utils.show_debug_toolbar'  # we have to override this check because the default depends on IP address, which doesn't work inside Vagrant
    }
except ImportError:
    pass

# django_extensions
try:
    import django_extensions
    INSTALLED_APPS += (
        # Switch to this when we upgrade to Django 1.7.x:
        #'debug_toolbar.apps.DebugToolbarConfig',
        'django_extensions',
    )
except ImportError:
    pass
    
    
# Our Sorl thumbnail stuff. In prod we use Redis, we'll just use
# the local uncached DB here in dev.
THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.cached_db_kvstore.KVStore'