from django.conf import settings
from django.http import Http404
from django.shortcuts import render


class AdminAuthMiddleware(object):
    def process_request(self, request):
        """
            Don't make Django admin visible unless user is already logged into dashboard and is an admin.
        """
        if request.path.startswith('/admin/') and not getattr(request.user, 'is_staff', False):
            raise Http404


### read only mode ###

class ReadOnlyMiddleware(object):
    def process_exception(self, request, exception):
        if settings.READ_ONLY_MODE:
            return render(request, 'read_only_mode.html')
