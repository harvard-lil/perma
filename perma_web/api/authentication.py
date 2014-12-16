from tastypie.authentication import (MultiAuthentication,
                                     ApiKeyAuthentication,
                                     SessionAuthentication)


class DefaultAuthentication(MultiAuthentication):

    backends = (ApiKeyAuthentication(), SessionAuthentication())

    def __init__(self, *backends, **kwargs):
        pass  # prevent self.backends from being overwritten

    """
    Allow all GET requests through
    """
    def is_authenticated(self, request, **kwargs):
        result = super(DefaultAuthentication, self).is_authenticated(request, **kwargs)
        return request.method == 'GET' or result


class CurrentUserAuthentication(MultiAuthentication):

    backends = (ApiKeyAuthentication(), SessionAuthentication())

    def __init__(self, *backends, **kwargs):
        pass  # prevent self.backends from being overwritten
