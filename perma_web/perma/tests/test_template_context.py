from django.conf import settings
from django.template.loader import render_to_string
from django.test import RequestFactory

from perma.context_processors import template_visible_settings


def test_js_config_exposes_the_expected_template_settings():
    rendered = render_to_string("js_config.html", request=RequestFactory().get("/"))

    expected_values = {
        "API_VERSION": settings.API_VERSION,
        "STATIC_URL": settings.STATIC_URL,
        "MEDIA_URL": settings.MEDIA_URL,
        "DEBUG": settings.DEBUG,
        "USE_SENTRY": settings.USE_SENTRY,
        "SENTRY_DSN": settings.SENTRY_DSN,
        "SENTRY_ENVIRONMENT": settings.SENTRY_ENVIRONMENT,
        "SENTRY_TRACES_SAMPLE_RATE": settings.SENTRY_TRACES_SAMPLE_RATE,
        "PLAYBACK_HOST": settings.PLAYBACK_HOST,
    }

    for name, value in expected_values.items():
        assert f"{name}:" in rendered
        assert str(value).lower() in rendered.lower()


def test_template_context_processor_exposes_only_allowlisted_settings():
    context = template_visible_settings(RequestFactory().get("/"))

    assert context == {
        setting_name: getattr(settings, setting_name)
        for setting_name in settings.TEMPLATE_VISIBLE_SETTINGS
    }
    assert "PERMA_PAYMENTS_SECRET_KEY" not in context
