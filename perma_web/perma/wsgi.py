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
class PywbRedirectMiddleware:
    def __init__(self, pywb):
        self.pywb = pywb

    def __call__(self, environ, start_response):
        # this makes sure everything is served from the /warc route.
        # /timegate route was created to circumvent cloudflare's caching + header resetting issue

        environ['SCRIPT_NAME'] = environ['SCRIPT_NAME'].replace(perma.settings.TIMEGATE_WARC_ROUTE, perma.settings.WARC_ROUTE)

        return self.pywb(environ, start_response)


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
    class ForwardedForWhitelistMiddleware:

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

            # The request must be a health check coming from the load balancer --
            if len(proxy_ips) == 1 and any(proxy_ips[0] in trusted_ip_range for trusted_ip_range in self.whitelists[0]):
                environ['REMOTE_ADDR'] = proxy_ips[0]
                return self.app(environ, start_response)
            # OR the list must include at least one IP per proxy in our whitelists,
            # plus one for the client IP --
            if len(proxy_ips) < len(self.whitelists) + 1:
                return self.bad_request(environ, start_response)

            # Each of the final IPs in the list must match the relevant whitelist.
            # If a whitelist is empty, any IP is accepted for that proxy.
            for whitelist, proxy_ip in zip(self.whitelists, proxy_ips[-len(self.whitelists):]):
                if whitelist and not any(proxy_ip in trusted_ip_range for trusted_ip_range in whitelist):
                    return self.bad_request(environ, start_response)

            # Set REMOTE_ADDR to client IP reported by proxies.
            environ['REMOTE_ADDR'] = proxy_ips[-len(self.whitelists)-1]

            # Continue processing as normal.
            return self.app(environ, start_response)

    application = ForwardedForWhitelistMiddleware(application, whitelists=perma.settings.TRUSTED_PROXIES)

# add newrelic app wrapper
if use_newrelic:
    application = newrelic.agent.WSGIApplicationWrapper(application)
