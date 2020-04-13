from django.conf import settings
from django.http import Http404
from django.urls import reverse
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
