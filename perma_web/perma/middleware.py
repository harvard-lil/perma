from django.conf import settings
from django.http import Http404
from django.urls import reverse
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin


class AdminAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
            Don't make Django admin visible unless user is already logged into dashboard and is an admin.
        """
        if request.path.startswith('/admin/') and not getattr(request.user, 'is_staff', False):
            raise Http404


def bypass_cache_middleware(get_response):
    LOGIN_ROUTE = reverse('user_management_limited_login')
    LOGOUT_ROUTE = reverse('logout')

    def middleware(request):
        response = get_response(request)
        if request.path.startswith(LOGIN_ROUTE) or request.path.startswith(LOGOUT_ROUTE):
            if request.user.is_authenticated:
                response.set_cookie(settings.CACHE_BYPASS_COOKIE_NAME, 'True')
            else:
                response.delete_cookie(settings.CACHE_BYPASS_COOKIE_NAME)
        return response

    return middleware


def get_subdomain(request):
    """
        Given request, get portion before the first .
    """
    if not hasattr(request, 'subdomain'):
        request.subdomain = request.get_host().split('.', 1)[0]
    return request.subdomain


class BaseSubdomainMiddleware(MiddlewareMixin):
    """
    To route requests from a subdomain to a particular Django app, subclass this base class,
    and set 'subdomain' to the subdomain prefix and 'urlconf' to the import path of the app's
    urls.py (relative to the project root, e.g. "myapp.urls").
    """
    subdomain = None
    urlconf = None

    def process_request(self, request):
        if get_subdomain(request) == self.subdomain:
            request.urlconf = self.urlconf

    def process_response(self, request, response):
        """
        Forces the HTTP ``Vary`` header onto requests to avoid having responses
        cached across subdomains.

        Copied from django-subdomains package.
        """
        if getattr(settings, 'FORCE_VARY_ON_HOST', True):
            patch_vary_headers(response, ('Host',))
        return response


class APISubdomainMiddleware(BaseSubdomainMiddleware):
    subdomain = settings.API_SUBDOMAIN
    urlconf = 'api.urls'


class ReplaySubdomainMiddleware(BaseSubdomainMiddleware):
    subdomain = settings.REPLAY_SUBDOMAIN
    urlconf = 'replay.urls'
