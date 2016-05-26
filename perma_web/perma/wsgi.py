"""
WSGI config for Perma project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

"""
import os

# Newrelic setup
use_newrelic = os.environ.get("USE_NEW_RELIC", False)
if use_newrelic:
    import newrelic.agent
    newrelic.agent.initialize(os.path.join(os.path.dirname(__file__), '../../services/newrelic/newrelic.ini'))

# env setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "perma.settings")
os.environ.setdefault("CELERY_LOADER", "django")

# these imports may depend on env setup and/or newrelic setup that came earlier
from werkzeug.wsgi import DispatcherMiddleware
from django.core.wsgi import get_wsgi_application
from warc_server.app import application as warc_application
from whitenoise.django import DjangoWhiteNoise

# subclass WhiteNoise to add missing mime types
class PermaWhiteNoise(DjangoWhiteNoise):
    def __init__(self, *args, **kwargs):
        self.EXTRA_MIMETYPES += (('image/svg+xml', '.svg'),)
        super(PermaWhiteNoise, self).__init__(*args, **kwargs)

# set up application
application = DispatcherMiddleware(
    PermaWhiteNoise(get_wsgi_application()),  # Django app wrapped with whitenoise to serve static assets
    {
        '/warc': warc_application,  # pywb for record playback
    }
)

# add newrelic app wrapper
if use_newrelic:
    application = newrelic.agent.WSGIApplicationWrapper(application)
