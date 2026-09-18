import pytest
from django.template import engines

from perma.templatetags.absolute_url import absolute_url


@pytest.mark.parametrize("url, expected", [
    ("/static/img/a.png", "https://perma.cc/static/img/a.png"),
    ("https://static.perma.cc/static/img/a.png", "https://static.perma.cc/static/img/a.png"),
    ("http://static.example/img/a.png", "http://static.example/img/a.png"),
    ("//static.perma.cc/static/img/a.png", "https://static.perma.cc/static/img/a.png"),
])
def test_absolute_url(url, expected):
    assert absolute_url(url, "https://perma.cc") == expected


@pytest.mark.parametrize("static_url, expected", [
    # The Salt hosts: output is exactly what "{{ base_url }}{{ STATIC_URL }}..." gave.
    ("/static/", "https://perma.cc/static/img/sharing/blue_logo.png"),
    # A static subdomain: no host prefixed onto an absolute URL.
    ("https://static.perma.cc/static/", "https://static.perma.cc/static/img/sharing/blue_logo.png"),
])
def test_meta_image_url_in_a_template(static_url, expected):
    template = engines["django"].from_string(
        "{% load absolute_url %}{{ STATIC_URL|add:'img/sharing/blue_logo.png'|absolute_url:base_url }}"
    )
    assert template.render({"STATIC_URL": static_url, "base_url": "https://perma.cc"}) == expected
