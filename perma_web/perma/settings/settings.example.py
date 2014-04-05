# Choose one of these:
# from settings_dev import *
# from settings_prod import *

# NOTE: If you are running a local test environment, settings_dev will already have sensible defaults for many of these.
# Only override the ones you need to, so you're less likely to have to make manual settings updates after pulling in changes.

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES['default']['NAME'] = 'perma'
DATABASES['default']['USER'] = 'perma'
DATABASES['default']['PASSWORD'] = 'perma'

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# If the phantomjs binary isn't in your path, you can set the location here
# PHANTOMJS_BINARY = os.path.join(PROJECT_ROOT, 'lib/phantomjs')

# This is where we dump the generated WARCs, PNGs, and so on. If you're running
# in prod, you'll likely want to set this
#MEDIA_ROOT = '/tmp/perma/assets'

# Instapaper credentials
INSTAPAPER_KEY = 'key'
INSTAPAPER_SECRET = 'secret'
INSTAPAPER_USER = 'user@example.com'
INSTAPAPER_PASS = 'pass'

# Google Analytics
GOOGLE_ANALYTICS_KEY = 'UA-XXXXX-X'
GOOGLE_ANALYTICS_DOMAIN = 'example.com'

# To populate the from field of emails sent from Perma
DEFAULT_FROM_EMAIL = 'email@example.com'

# The host we want to display (used when DEBUG=False)
HOST = 'perma.cc'