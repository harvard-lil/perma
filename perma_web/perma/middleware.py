from django.http import Http404
from django.utils.deprecation import MiddlewareMixin


class AdminAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
            Don't make Django admin visible unless user is already logged into dashboard and is an admin.
        """
        if request.path.startswith('/admin/') and not getattr(request.user, 'is_staff', False):
            raise Http404

