"""
WSGI config for Perma project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

"""
import os

import newrelic
from werkzeug.wsgi import DispatcherMiddleware

newrelic.agent.initialize('/srv/www/perma/services/newrelic/newrelic.ini')


# We defer to a DJANGO_SETTINGS_MODULE already in the environment. This breaks
# if running multiple sites in the same mod_wsgi process. To fix this, use
# mod_wsgi daemon mode with each site in its own daemon process, or use
# os.environ["DJANGO_SETTINGS_MODULE"] = "perma.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "perma.settings")
os.environ.setdefault("CELERY_LOADER", "django")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
from warc_server.app import application as warc_application
from whitenoise.django import DjangoWhiteNoise


# subclass WhiteNoise to add missing mime types
class PermaWhiteNoise(DjangoWhiteNoise):
    def __init__(self, *args, **kwargs):
        self.EXTRA_MIMETYPES += (('image/svg+xml', '.svg'),)
        super(PermaWhiteNoise, self).__init__(*args, **kwargs)


application = DispatcherMiddleware(
    PermaWhiteNoise(get_wsgi_application()),  # Django app wrapped with whitenoise to serve static assets
    {
        '/warc': warc_application,  # pywb for record playback
    }
)
