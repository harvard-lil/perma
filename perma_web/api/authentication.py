from tastypie.authentication import (MultiAuthentication,
                                     ApiKeyAuthentication,
                                     SessionAuthentication)
from perma.models import LinkUser


class KeyOnlyAuthentication(ApiKeyAuthentication):
    """ Subclass of Tastypie's ApiKeyAuthentication that doesn't require username. """

    def is_authenticated(self, request, **kwargs):
        if request.META.get('HTTP_AUTHORIZATION') and request.META['HTTP_AUTHORIZATION'].lower().startswith('apikey '):
            (auth_type, api_key) = request.META['HTTP_AUTHORIZATION'].split()
        else:
            api_key = request.GET.get('api_key') or request.POST.get('api_key')

        if not api_key:
            return self._unauthorized()

        try:
            request.user = LinkUser.objects.get(is_active=True, api_key__key=api_key)
        except LinkUser.DoesNotExist:
            return self._unauthorized()

        return True

    def get_identifier(self, request):
        return unicode(request.user)


# Order here matters. If ApiKeyAuthentication comes first,
# you'll get "You cannot access body after reading from request's data stream"
# errors when POSTing multipart forms using SessionAuthentication
backends = (SessionAuthentication(), KeyOnlyAuthentication())


class DefaultAuthentication(MultiAuthentication):

    backends = backends

    def __init__(self, *backends, **kwargs):
        pass  # prevent self.backends from being overwritten

    """
    Allow all GET requests through
    """
    def is_authenticated(self, request, **kwargs):
        # If is_authenticated isn't run, request.user will always be anonymous
        result = super(DefaultAuthentication, self).is_authenticated(request, **kwargs)
        return request.method == 'GET' or result


class CurrentUserAuthentication(MultiAuthentication):

    backends = backends

    def __init__(self, *backends, **kwargs):
        pass  # prevent self.backends from being overwritten
