# settings used for continuous integration test server

from settings_dev import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

DATABASES['default']['HOST'] = '127.0.0.1'
DATABASES['default']['NAME'] = 'perma'
DATABASES['default']['USER'] = 'root'
DATABASES['default']['PASSWORD'] = ''

# To populate the from field of emails sent from Perma
DEFAULT_FROM_EMAIL = 'email@example.com'

# The host we want to display (used when DEBUG=False)
HOST = 'perma.cc'

# Where we store our generated assets (phantomjs images)
MEDIA_ROOT = '/tmp/perma/assets'