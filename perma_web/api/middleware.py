from django.conf import settings
from django.utils.cache import patch_vary_headers

from mirroring.middleware import get_subdomain


class APISubdomainMiddleware(object):
    def process_request(self, request):
        if get_subdomain(request) == settings.API_SUBDOMAIN:
            request.urlconf = 'api.urls'
            request.no_mirror_forwarding = True

    def process_response(self, request, response):
        """
        Forces the HTTP ``Vary`` header onto requests to avoid having responses
        cached across subdomains.

        Copied from django-subdomains package.
        """
        if getattr(settings, 'FORCE_VARY_ON_HOST', True):
            patch_vary_headers(response, ('Host',))

        return response
