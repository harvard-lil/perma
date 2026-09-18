"""The /healthcheck/ path the ECS container health check asks for.

HealthCheckMiddleware answers it first in MIDDLEWARE, so the request never
reaches SecurityMiddleware's SSL redirect (the check is plain HTTP to
localhost) and never consults ALLOWED_HOSTS. No database is involved.
"""

from django.test import Client, override_settings


@override_settings(SECURE_SSL_REDIRECT=True, ALLOWED_HOSTS=["perma.test"])
def test_healthcheck_answers_plain_http_from_any_host():
    response = Client().get("/healthcheck/", secure=False, HTTP_HOST="localhost:8000")
    assert response.status_code == 200
    assert response.content == b"ok"


@override_settings(SECURE_SSL_REDIRECT=True)
def test_other_paths_still_redirect_to_https():
    response = Client().get("/", secure=False)
    assert response.status_code == 301
