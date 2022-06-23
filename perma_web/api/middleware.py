from django.middleware.common import CommonMiddleware as DjangoCommonMiddleware

class CORSMiddleware(DjangoCommonMiddleware):
    """
       Add CORS headers to requests made to `api.domain.ext`, so the API can be used in the browser.
    """
    def process_response(self, request, response):
        response = super().process_response(request, response)

        host = request.get_host()

        origin = request.headers.get("Origin")
        if not origin: # Set origin to `*` if none was provided.
            origin = "*"

        if host.startswith("api."):
            # Force HTTP 200 for preflight requests (?).
            # This is a temporary workaround to account for the fact that the browser will not pass a `Authorization` header during preflight, which will trigger a 401.
            if request.method == "OPTIONS" and response.status_code == 401:
                response.status_code = 200

            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Headers"] = "Authorization"
            response["Access-Control-Allow-Methods"] = "*"
            #response["Access-Control-Allow-Credentials"] = "true"
            # ^ Uncomment if we want to allow `fetch()` / `XMLHttpRequest`` to implicitly pass credentials (i.e: HTTP auth stored in session).  

        return response
