from tastypie.authentication import ApiKeyAuthentication

class DefaultAuthentication(ApiKeyAuthentication):
    """
    Allow all GET requests through
    """

    def is_authenticated(self, request, **kwargs):
        if request.method == 'GET':
            return True
        return super(DefaultAuthentication, self).is_authenticated(request, **kwargs)
