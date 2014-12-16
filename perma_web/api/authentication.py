from tastypie.authentication import (MultiAuthentication,
                                     ApiKeyAuthentication,
                                     SessionAuthentication)


# Order here matters. If ApiKeyAuthentication comes first,
# you'll get "You cannot access body after reading from request's data stream"
# errors when POSTing multipart forms using SessionAuthentication
backends = (SessionAuthentication(), ApiKeyAuthentication())


class DefaultAuthentication(MultiAuthentication):

    backends = backends

    def __init__(self, *backends, **kwargs):
        pass  # prevent self.backends from being overwritten

    """
    Allow all GET requests through
    """
    def is_authenticated(self, request, **kwargs):
        result = super(DefaultAuthentication, self).is_authenticated(request, **kwargs)
        return request.method == 'GET' or result


class CurrentUserAuthentication(MultiAuthentication):

    backends = backends

    def __init__(self, *backends, **kwargs):
        pass  # prevent self.backends from being overwritten
