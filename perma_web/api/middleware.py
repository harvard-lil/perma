from django.middleware.common import CommonMiddleware as DjangoCommonMiddleware
from django.conf import settings

class CORSMiddleware(DjangoCommonMiddleware):
    """
       Add CORS headers to requests made to `api.domain.ext`, so the API can be used in the browser.
    """
    def process_response(self, request, response):
        response = super().process_response(request, response)

        origin = request.headers.get("Origin")
        if not origin: # Set origin to `*` if none was provided.
            origin = "*"

        if f"/v{settings.API_VERSION}/" in request.get_raw_uri(): # Applies to `/v1/` API urls.
            # Force HTTP 200 for preflight requests (?).
            # The browser doesn't pass a `Authorization` header during preflight (in most cases), our API therefore assumes this resource can't be accessed.
            if request.method == "OPTIONS" and response.status_code == 401:
                response.status_code = 200

            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Headers"] = "Authorization,Content-Type"
            response["Access-Control-Allow-Methods"] = "*"
            #response["Access-Control-Allow-Credentials"] = "true"
            # ^ Uncomment if we want to allow the browser to implicitly pass stored credentials.

        return response
