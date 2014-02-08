"""
WSGI config for Perma project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

"""
import os
from werkzeug.wsgi import DispatcherMiddleware

# We defer to a DJANGO_SETTINGS_MODULE already in the environment. This breaks
# if running multiple sites in the same mod_wsgi process. To fix this, use
# mod_wsgi daemon mode with each site in its own daemon process, or use
# os.environ["DJANGO_SETTINGS_MODULE"] = "perma.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "perma.settings")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application

from warc_server.app import application as warc_application

application = DispatcherMiddleware(
    get_wsgi_application(), # Django
    {
        '/warc': warc_application,
    }
)