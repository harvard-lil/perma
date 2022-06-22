from django.middleware.common import CommonMiddleware as DjangoCommonMiddleware

class CORSMiddleware(DjangoCommonMiddleware):
    """
       Set `Access-Control-Allow-Origin: *` for API responses, including redirects.
       Only applies if requests come from api.domain.ext.
    """
    def process_response(self, request, response):
        response = super().process_response(request, response)
        host = request.get_host()

        if host.startswith("api."):
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Headers"] = "Authorization"
        return response
