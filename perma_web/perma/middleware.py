from functools import wraps

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.utils.decorators import available_attrs
import djangosecure.middleware


class AdminAuthMiddleware(object):
    def process_request(self, request):
        """
            Don't make Django admin visible unless user is already logged into dashboard and is an admin.
        """
        if request.path.startswith('/admin/') and not getattr(request.user, 'is_staff', False):
            raise Http404


### SSL forwarding ###

def ssl_optional(view_func):
    """
        Mark view functions with @ssl_optional to exclude them from automatic forwarding to https:.
    """
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.ssl_optional = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)


class SecurityMiddleware(djangosecure.middleware.SecurityMiddleware):
    """
        Apply the same test as djangosecure.middleware.SecurityMiddleware,
        but do it in process_view instead of process_request so we can check
        whether the view has been decorated with ssl_optional.
    """
    def process_request(self, request):
        return

    def process_view(self, request, view_func, view_args, view_kwargs):
        if getattr(view_func, 'ssl_optional', False):
            return
        return super(SecurityMiddleware, self).process_request(request)


### read only mode ###

class ReadOnlyMiddleware(object):
    def process_exception(self, request, exception):
        if settings.READ_ONLY_MODE:
            return render(request, 'read_only_mode.html')
