# Travis is our continuous integration test server.
# This file gets copied by .travis.yml to perma_web/perma/settings/

from .deployments.settings_testing import *

DATABASES['default']['HOST'] = '127.0.0.1'
DATABASES['default']['USER'] = 'root'
DATABASES['default']['PASSWORD'] = ''

DATABASES['perma-cdxline']['HOST'] = '127.0.0.1'
DATABASES['perma-cdxline']['USER'] = 'root'
DATABASES['perma-cdxline']['PASSWORD'] = ''
