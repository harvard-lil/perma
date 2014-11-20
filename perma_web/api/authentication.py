from tastypie.authentication import ApiKeyAuthentication

class DefaultAuthentication(ApiKeyAuthentication):
    """
    Allow all GET requests through
    """
    def is_authenticated(self, request, **kwargs):
        result = super(DefaultAuthentication, self).is_authenticated(request, **kwargs)
        return request.method == 'GET' or result
