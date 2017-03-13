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

# Pywb request rewriting for the /timegate route
class PywbRedirectMiddleware(object):
    def __init__(self, pywb):
        self.pywb = pywb

    def __call__(self, environ, start_response):
        # this makes sure everything is served from the /warc route.
        # /timegate route was created to circumvent cloudflare's caching + header resetting issue

        environ['SCRIPT_NAME'] = environ['SCRIPT_NAME'].replace(perma.settings.TIMEGATE_WARC_ROUTE, perma.settings.WARC_ROUTE)

        return self.pywb(environ, start_response)

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


# Main application setup
application = DispatcherMiddleware(
    get_wsgi_application(),  # Django app
    {
        perma.settings.TIMEGATE_WARC_ROUTE: PywbRedirectMiddleware(warc_application),
        perma.settings.WARC_ROUTE: warc_application,  # pywb for record playback
    }
)

# Middleware to whitelist X-Forwarded-For proxy IP addresses
if perma.settings.TRUSTED_PROXIES:
    from netaddr import IPNetwork
    from werkzeug.wrappers import Response
    class ForwardedForWhitelistMiddleware(object):

        def __init__(self, app, whitelists):
            self.app = app
            self.whitelists = [[IPNetwork(trusted_ip_range) for trusted_ip_range in whitelist] for whitelist in whitelists]

        def bad_request(self, environ, start_response, reason=''):
            response = Response(reason, 400)
            return response(environ, start_response)

        def __call__(self, environ, start_response):
            # Parse X-Forwarded-For header into list of IPs.
            # First IP in list is client IP, then each proxy up to the closest one.
            # Final IP is from the REMOTE_ADDR header -- closest proxy of all.
            forwarded_for = environ.get('HTTP_X_FORWARDED_FOR', '')
            remote_addr = environ.get('REMOTE_ADDR', '').strip()
            proxy_ips = [x for x in [x.strip() for x in forwarded_for.split(',')] if x] + [remote_addr]

            # List must include at least one IP per proxy in our whitelists, plus one for the client IP.
            if len(proxy_ips) < len(self.whitelists) + 1:
                return self.bad_request(environ, start_response)  #, 'Header %s has insufficient entries' % self.header)

            # Each of the final IPs in the list must match the relevant whitelist. If a whitelist is empty, any IP is accepted for that proxy.
            for whitelist, proxy_ip in zip(self.whitelists, proxy_ips[-len(self.whitelists):]):
                if whitelist and not any(proxy_ip in trusted_ip_range for trusted_ip_range in whitelist):
                    return self.bad_request(environ, start_response)  #, 'Header %s has invalid proxy IP. Value: %s' % (self.header, forwarded_for_header))

            # Set REMOTE_ADDR to client IP reported by proxies.
            environ['REMOTE_ADDR'] = proxy_ips[-len(self.whitelists)-1]

            # Continue processing as normal.
            return self.app(environ, start_response)

    application = ForwardedForWhitelistMiddleware(application, whitelists=perma.settings.TRUSTED_PROXIES)

# add newrelic app wrapper
if use_newrelic:
    application = newrelic.agent.WSGIApplicationWrapper(application)
