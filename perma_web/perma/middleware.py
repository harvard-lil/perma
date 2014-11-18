from django.conf import settings
from django.http import HttpResponseRedirect


class ForceSSLMiddleware(object):
    """
        Force dashboard connections to use SSL, unless DEBUG=True or SSL_AVAILABLE=False.
    """
    secure_path_prefixes = set(['manage', 'login', 'logout', 'register', 'password', 'admin'])

    def process_request(self, request):
        if settings.DEBUG or not settings.SSL_AVAILABLE or request.is_secure():
            return None
        path_prefix = request.path.split('/',2)[1]
        if path_prefix in self.secure_path_prefixes:
            return HttpResponseRedirect(request.build_absolute_uri().replace('http://', 'https://'))