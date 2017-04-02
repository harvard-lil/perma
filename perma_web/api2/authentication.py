from rest_framework.authentication import TokenAuthentication as DRFTokenAuthentication
from tastypie.models import ApiKey


class TokenAuthentication(DRFTokenAuthentication):
    """
        Override default TokenAuth to use our api key table and custom keyword in the Authorization header.
    """
    keyword = 'ApiKey'
    model = ApiKey  # todo when dropping TastyPie -- migrate to new table

    def authenticate(self, request):
        """
            Try getting api_key from get/post param before using Authorization header.
        """
        api_key = request.POST.get('api_key') or request.query_params.get('api_key')
        if api_key:
            return self.authenticate_credentials(api_key)
        return super(TokenAuthentication, self).authenticate(request)