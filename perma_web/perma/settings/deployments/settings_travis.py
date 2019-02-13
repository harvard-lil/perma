# Travis is our continuous integration test server.
# This file gets copied by .travis.yml to perma_web/perma/settings/

from .deployments.settings_testing import *

DATABASES['default']['HOST'] = '127.0.0.1'
DATABASES['default']['USER'] = 'root'
DATABASES['default']['PASSWORD'] = ''

DATABASES['perma-cdxline']['HOST'] = '127.0.0.1'
DATABASES['perma-cdxline']['USER'] = 'root'
DATABASES['perma-cdxline']['PASSWORD'] = ''

REMOTE_SELENIUM = True
if REMOTE_SELENIUM:
    HOST = 'perma.test:8000'
    PLAYBACK_HOST = 'perma-archives.test:8000'

ENABLE_WR_PLAYBACK = False
if ENABLE_WR_PLAYBACK:
    assert REMOTE_SELENIUM, "WR Playback must be tested with REMOTE_SELENIUM = True"
    WR_API = 'http://nginx:80/api/v1'
    PLAYBACK_HOST = 'perma-archives:81'
