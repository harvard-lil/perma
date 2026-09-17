"""
Tests for the PERMA_SETTINGS_MODULE runtime settings selector in
perma/settings/__init__.py.

These run perma.settings in a *subprocess*, not in-process, because this test
process already imported perma.settings.deployments.settings_testing (and, as
a side effect of Python's package-import machinery, already ran
perma/settings/__init__.py once and cached the result in sys.modules). A fresh
interpreter is the only reliable way to exercise the module-selection logic
under different environment variables. None of this touches a database:
importing a settings module only builds Python dicts/lists, it doesn't connect
to anything.
"""

import json
import os
import subprocess
import sys
import textwrap

import pytest

WEB_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# settings_ecs reads all of these out of APP_CONFIG while it imports, so
# importing it at all means supplying them. The values are shaped only as far as
# that module looks: ALLOWED_HOSTS is split on commas, ADMINS is
# ast.literal_eval'd, DATABASE_PORT is int()'d, the Sentry DSN has to parse. A
# KeyError from here means settings_ecs reads a new key and this dict needs it
# too -- and so does the Secrets Manager document.
FAKE_APP_CONFIG = {
    "TIER": "staging",
    "ALLOWED_HOSTS": "perma.test,api.perma.test",
    "SECRET_KEY": "fake",
    "ADMINS": "[('Someone', 'someone@example.test')]",
    "DATABASE_NAME": "perma",
    "DATABASE_USERNAME": "perma",
    "DATABASE_PASSWORD": "fake",
    "DATABASE_HOST": "db",
    "DATABASE_PORT": "5432",
    "DEFAULT_FROM_EMAIL": "info@example.test",
    "SERVER_EMAIL": "server@example.test",
    "EMAIL_HOST": "smtp.example.test",
    "EMAIL_HOST_USER": "fake",
    "EMAIL_HOST_PASSWORD": "fake",
    "HOST": "perma.test",
    "MEDIA_URL": "//user-content.perma.test/media/",
    "PLAYBACK_HOST": "rejouer.perma.test",
    "INTERNET_ARCHIVE_COLLECTION": "perma_cc_test",
    "INTERNET_ARCHIVE_IDENTIFIER_PREFIX": "perma_cc_test_",
    "INTERNET_ARCHIVE_ACCESS_KEY": "fake",
    "INTERNET_ARCHIVE_SECRET_KEY": "fake",
    "STORAGE_BUCKET": "perma-storage",
    "WACZ_BUCKET": "perma-secondary-storage",
    "CELERY_BROKER_URL": "amqp://fake@broker.example.test/perma",
    "CACHE_LOCATION": "redis://cache.example.test:6379/0",
    "STRIPE_PAYMENTS_APP_INTERNAL_URL": "http://payments.internal.test",
    "STRIPE_PAYMENTS_APP_EXTERNAL_URL": "https://payments.example.test",
    "PAYMENTS_KEY_ID": "1",
    "PAYMENTS_PERMA_SECRET_KEY": "fake",
    "PAYMENTS_PERMA_PUBLIC_KEY": "fake",
    "PAYMENTS_PAYMENTS_PUBLIC_KEY": "fake",
    "SCAN_URL": "http://filecheck.example.test/scan/",
    "SENTRY_DSN": "https://0123456789abcdef@o1.ingest.sentry.io/1",
    "SCOOP_API_URL": "https://scoop.example.test/",
    "SCOOP_API_KEY": "fake",
}

# A developer may have their own perma/settings/settings.py (gitignored). When it
# exists, the no-env-var path imports THAT rather than settings_dev, so the fallback
# test below can't assert anything about its contents. CI never has this file.
LOCAL_SETTINGS_PY = os.path.join(WEB_DIR, "perma", "settings", "settings.py")


def _run(code, env_overrides):
    env = os.environ.copy()
    env.pop("PERMA_SETTINGS_MODULE", None)
    env.pop("APP_CONFIG", None)
    env.pop("DJANGO_SETTINGS_MODULE", None)
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        cwd=WEB_DIR,
        env=env,
        capture_output=True,
        text=True,
    )


def _installed_apps(settings_module, env_overrides=None):
    env = {"PERMA_SETTINGS_MODULE": settings_module}
    env.update(env_overrides or {})
    result = _run(
        """
        import json
        import perma.settings as settings
        print(json.dumps(list(settings.INSTALLED_APPS)))
        """,
        env,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.splitlines()[-1])


def test_settings_build_installed_apps_match_the_deployed_ones():
    # The image build runs collectstatic under settings_build, and CI's
    # migration and Celery task inspectors run against the image under it too;
    # all of them derive their output from INSTALLED_APPS. What they record
    # describes the deployed app only for as long as the two lists agree.
    assert _installed_apps("settings_build") == _installed_apps(
        "settings_ecs", {"APP_CONFIG": json.dumps(FAKE_APP_CONFIG)}
    )


def test_settings_ecs_reads_its_configuration():
    result = _run(
        """
        import perma.settings as settings
        assert settings.DEBUG is False
        assert settings.ALLOWED_HOSTS == ["perma.test", "api.perma.test"]
        assert settings.DATABASES["default"]["PORT"] == 5432
        assert settings.DATABASES["default"]["OPTIONS"]["sslmode"] == "verify-full"
        assert settings.ADMINS == [("Someone", "someone@example.test")]
        assert settings.USE_ANALYTICS is False  # staging
        assert "sync_subscriptions_from_perma_payments" not in settings.CELERY_BEAT_JOB_NAMES
        assert "run-next-capture" in settings.CELERY_BEAT_SCHEDULE
        assert "file" not in settings.LOGGING["handlers"]
        assert settings.PAYMENTS_APP_URLS["purchase"] == "https://payments.example.test/purchase/"
        assert settings.JS_WACZ_DIR.endswith("/services/js-wacz")
        assert settings.PERMA_VERSION == "abc1234"
        assert settings.STATIC_URL == "/static/"  # key absent: served from the image
        assert settings.DEPLOYMENT_SENTINEL_CACHE_REQUIRED is True
        print("ok")
        """,
        {
            "PERMA_SETTINGS_MODULE": "settings_ecs",
            "APP_CONFIG": json.dumps(FAKE_APP_CONFIG),
            "PERMA_VERSION": "abc1234",
        },
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_settings_ecs_static_url_from_the_bucket():
    # Once the deploy publishes static files to the bucket, the tier's secret
    # carries the URL; the /static/ path is what keeps WhiteNoise's prefix
    # (urlparse(STATIC_URL).path) answering for the copies in the image.
    result = _run(
        """
        import perma.settings as settings
        assert settings.STATIC_URL == "https://static.perma.test/static/"
        assert "whitenoise.middleware.WhiteNoiseMiddleware" in settings.MIDDLEWARE
        print("ok")
        """,
        {
            "PERMA_SETTINGS_MODULE": "settings_ecs",
            "APP_CONFIG": json.dumps({**FAKE_APP_CONFIG, "STATIC_URL": "https://static.perma.test/static/"}),
        },
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_settings_ecs_rejects_an_unknown_tier():
    result = _run(
        "import perma.settings",
        {
            "PERMA_SETTINGS_MODULE": "settings_ecs",
            "APP_CONFIG": json.dumps({**FAKE_APP_CONFIG, "TIER": "stage"}),
        },
    )
    assert result.returncode != 0
    assert "TIER must be" in result.stderr


def test_perma_settings_module_selects_named_module():
    result = _run(
        """
        import perma.settings as settings
        assert settings.DEBUG is False, settings.DEBUG
        print("ok")
        """,
        {"PERMA_SETTINGS_MODULE": "settings_build"},
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_perma_settings_module_only_merges_uppercase_names():
    # settings_ecs does `from .settings_prod import *`, which pulls in
    # settings_common's own lowercase imports (e.g. `deepcopy`) along with real
    # settings. Only the real (uppercase) settings should end up on perma.settings.
    result = _run(
        """
        import perma.settings as settings
        assert hasattr(settings, "PROJECT_ROOT")
        assert not hasattr(settings, "deepcopy")
        assert not hasattr(settings, "config")
        print("ok")
        """,
        {"PERMA_SETTINGS_MODULE": "settings_ecs", "APP_CONFIG": json.dumps(FAKE_APP_CONFIG)},
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_perma_settings_module_unknown_name_raises_clear_error():
    result = _run(
        "import perma.settings",
        {"PERMA_SETTINGS_MODULE": "settings_does_not_exist"},
    )
    assert result.returncode != 0
    assert "ImportError" in result.stderr
    assert "PERMA_SETTINGS_MODULE" in result.stderr
    assert "settings_does_not_exist" in result.stderr
    # Must fail loudly, not silently boot with dev settings.
    assert "does not name a module" in result.stderr


def test_perma_settings_module_internal_error_is_not_misreported_as_unknown_module():
    # settings_ecs.py exists, but requires an APP_CONFIG env var to import. That
    # failure is a real configuration problem in an existing module, not a typo'd
    # module name, so it must surface as-is rather than as our "unknown module" error.
    result = _run(
        "import perma.settings",
        {"PERMA_SETTINGS_MODULE": "settings_ecs"},
    )
    assert result.returncode != 0
    assert "KeyError" in result.stderr
    assert "APP_CONFIG" in result.stderr
    assert "does not name a module" not in result.stderr


@pytest.mark.skipif(
    os.path.exists(LOCAL_SETTINGS_PY),
    reason="local perma/settings/settings.py shadows the settings_dev fallback",
)
def test_perma_settings_module_unset_falls_back_to_settings_dev():
    result = _run(
        """
        import perma.settings as settings
        assert settings.DEBUG is True
        print("ok")
        """,
        {},
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout
