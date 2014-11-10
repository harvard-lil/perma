from django.contrib.auth import get_user as django_get_user
from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.functional import SimpleLazyObject

from .models import FakeLinkUser
from .utils import read_signed_message

### helpers ###

def get_main_server_host(request):
    """
        Given request, return the host domain with the MIRROR_USERS_SUBDOMAIN included.
    """
    if not hasattr(request, 'main_server_host'):
        host = request.get_host()
        if not host.startswith(settings.MIRROR_USERS_SUBDOMAIN + '.'):
            host = settings.MIRROR_USERS_SUBDOMAIN + '.' + host
        request.main_server_host = host
    return request.main_server_host

def get_mirror_server_host(request):
    """
        Given request, return the host domain with the MIRROR_USERS_SUBDOMAIN excluded.
    """
    if not hasattr(request, 'mirror_server_host'):
        host = request.get_host()
        if host.startswith(settings.MIRROR_USERS_SUBDOMAIN + '.'):
            host = host[len(settings.MIRROR_USERS_SUBDOMAIN + '.'):]
        request.mirror_server_host = host
    return request.mirror_server_host

def get_url_for_host(request, host, url=None):
    """
        Given request, return a version of url with host replaced.

        If url is None, the url for this request will be used.
    """
    return request.build_absolute_uri(location=url).replace(request.get_host(), host, 1)


### fake user auth ###

def get_user(request):
    """ When request.user is viewed on mirror server, try to build it from a fake-user cookie we may have set on the dashboard. """
    if not hasattr(request, '_cached_user'):
        # first try for actual user login cookie
        user = django_get_user(request)

        # else see if we have a fake-user cookie
        if type(user) == AnonymousUser and request.get_host() == get_mirror_server_host(request):
            user_info = request.COOKIES.get(settings.MIRROR_COOKIE_NAME)
            if user_info:
                try:
                    user_info = read_signed_message(user_info)
                    user = FakeLinkUser.init_from_serialized_user(user_info)
                except Exception, e:
                    print "Error loading mirror user:", e

        request._cached_user = user
    return request._cached_user

class MirrorAuthenticationMiddleware(AuthenticationMiddleware):
    def process_request(self, request):
        request.user = SimpleLazyObject(lambda: get_user(request))


### forwarding ###

class MirrorForwardingMiddleware(object):
    def process_request(self, request):
        """
            Determine and cache main_server_host and mirror_server_host.
            If mirroring is disabled, these will be the same.
        """
        if settings.MIRRORING_ENABLED:
            request.main_server_host = get_main_server_host(request)
            request.mirror_server_host = get_mirror_server_host(request)
        else:
            if settings.DEBUG:
                request.mirror_server_host = request.get_host()
            else:
                request.mirror_server_host = settings.HOST
            request.main_server_host = request.mirror_server_host

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
            If we're doing mirroring, make sure that the user is directed to the main domain
            or the generic domain depending on whether the view they requested @must_be_mirrored.
        """
        if settings.MIRRORING_ENABLED:
            if getattr(view_func, 'may_be_mirrored', False):
                return

            host = request.get_host()
            must_be_mirrored = getattr(view_func, 'must_be_mirrored', False)

            if must_be_mirrored and host == request.main_server_host:
                return HttpResponsePermanentRedirect(get_url_for_host(request, request.mirror_server_host))

            elif not must_be_mirrored and (settings.MIRROR_SERVER or host != request.main_server_host):
                return HttpResponsePermanentRedirect(get_url_for_host(request, request.main_server_host))
