"""
WSGI config for Perma project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

"""
import os
import perma.settings

# Newrelic setup
use_newrelic = os.environ.get("USE_NEW_RELIC", False)
if use_newrelic:
    import newrelic.agent
    newrelic_config_file = os.environ.get('NEW_RELIC_CONFIG_FILE',
                                          os.path.join(os.path.dirname(__file__), '../../services/newrelic/newrelic.ini'))
    newrelic.agent.initialize(newrelic_config_file)

# env setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "perma.settings")
os.environ.setdefault("CELERY_LOADER", "django")

# these imports may depend on env setup and/or newrelic setup that came earlier
from werkzeug.wsgi import DispatcherMiddleware
from django.core.wsgi import get_wsgi_application
from warc_server.app import application as warc_application
from whitenoise.django import DjangoWhiteNoise

class PywbRedirectMiddleware(object):
    def __init__(self, pywb):
        self.pywb = pywb

    def __call__(self, environ, start_response):
        environ['SCRIPT_NAME'] = environ['SCRIPT_NAME'].replace('/timegate', '/warc')

        return self.pywb(environ, start_response)


# subclass WhiteNoise to add missing mime types
class PermaWhiteNoise(DjangoWhiteNoise):
    def __init__(self, *args, **kwargs):
        self.EXTRA_MIMETYPES += (('image/svg+xml', '.svg'),)
        super(PermaWhiteNoise, self).__init__(*args, **kwargs)

# Opbeat setup
if perma.settings.USE_OPBEAT:
    from opbeat import Client
    from warc_server.opbeat_wrapper import PywbOpbeatMiddleware

    warc_application = PywbOpbeatMiddleware(
        warc_application,
        Client(
            organization_id=perma.settings.OPBEAT['ORGANIZATION_ID'],
            app_id=perma.settings.OPBEAT['APP_ID'],
            secret_token=perma.settings.OPBEAT['SECRET_TOKEN'],
        )
    )

# set up application
application = DispatcherMiddleware(
    PermaWhiteNoise(get_wsgi_application()),  # Django app wrapped with whitenoise to serve static assets
    {
        '/warc': warc_application,  # pywb for record playback
        '/timegate': PywbRedirectMiddleware(warc_application),
    }
)

# add newrelic app wrapper
if use_newrelic:
    application = newrelic.agent.WSGIApplicationWrapper(application)
