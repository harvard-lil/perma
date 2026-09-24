import pytest
from rest_framework.exceptions import ValidationError

from api.serializers import AuthenticatedLinkSerializer


@pytest.mark.parametrize("submitted, expected", [
    ("example.com", "https://example.com"),
    ("  example.com/path  ", "https://example.com/path"),
    ("example.com:8080/path", "https://example.com:8080/path"),
    ("localhost:8080", "https://localhost:8080"),
    ("//example.com", "https://example.com"),
    ("httpfoo.com", "https://httpfoo.com"),
    ("https.example.com", "https://https.example.com"),
    ("http://example.com", "http://example.com"),
    ("https://example.com", "https://example.com"),
    ("HTTP://example.com", "HTTP://example.com"),
    ("", ""),
])
def test_validate_url_normalizes_scheme(submitted, expected):
    assert AuthenticatedLinkSerializer().validate_url(submitted) == expected


@pytest.mark.parametrize("submitted", [
    "ftp://example.com",
    "file:///etc/passwd",
    "javascript://example.com",
])
def test_validate_url_rejects_other_schemes(submitted):
    with pytest.raises(ValidationError):
        AuthenticatedLinkSerializer().validate_url(submitted)
