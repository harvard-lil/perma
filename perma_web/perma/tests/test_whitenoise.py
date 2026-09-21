import gzip

from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from whitenoise.middleware import WhiteNoiseMiddleware

from perma.storage_backends import StaticStorage


def _response_body(response):
    if response.streaming:
        return b"".join(response.streaming_content)
    return response.content


def _static_application():
    return WhiteNoiseMiddleware(
        lambda request: HttpResponse("missing static asset", status=404)
    )


def test_whitenoise_serves_collected_static_files_with_gzip_and_cache_headers(tmp_path):
    static_root = tmp_path / "static"
    static_root.mkdir()
    css = ("body { color: #123456; }\n" * 1_000).encode()
    storage = StaticStorage(location=static_root, base_url="/static/")
    storage.save("phase4.css", ContentFile(css))
    list(storage.post_process({"phase4.css": (storage, "phase4.css")}))
    assert (static_root / "phase4.css.gz").is_file()

    request_factory = RequestFactory()
    with override_settings(STATIC_ROOT=str(static_root), STATIC_URL="/static/", DEBUG=False):
        application = _static_application()
        response = application(request_factory.get("/static/phase4.css"))
        gzip_response = application(
            request_factory.get("/static/phase4.css", HTTP_ACCEPT_ENCODING="gzip")
        )
        missing_response = application(request_factory.get("/static/missing.css"))

    assert response.status_code == 200
    assert _response_body(response) == css
    assert response["Content-Type"] == 'text/css; charset="utf-8"'
    assert response["Cache-Control"] == "max-age=60, public"
    assert response["Vary"] == "Accept-Encoding"
    assert response["Access-Control-Allow-Origin"] == "*"
    assert "Content-Encoding" not in response

    assert gzip_response.status_code == 200
    assert gzip_response["Content-Encoding"] == "gzip"
    assert gzip.decompress(_response_body(gzip_response)) == css

    assert missing_response.status_code == 404
    assert _response_body(missing_response) == b"missing static asset"
