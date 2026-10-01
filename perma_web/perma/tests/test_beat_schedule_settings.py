"""
Each deployment's beat schedule must name only jobs that post_processing defines:
an unknown name raises KeyError when settings load, in every process of that tier.
"""
import json
import os
import subprocess
import sys

import pytest

# APP_CONFIG keys settings_ecs requires, with placeholder values
ECS_APP_CONFIG = {
    key: "x" for key in [
        "ALLOWED_HOSTS", "SECRET_KEY", "DATABASE_NAME", "DATABASE_USERNAME", "DATABASE_PASSWORD",
        "DATABASE_HOST", "DEFAULT_FROM_EMAIL", "SERVER_EMAIL", "EMAIL_HOST", "EMAIL_HOST_USER",
        "EMAIL_HOST_PASSWORD", "HOST", "MEDIA_URL", "PLAYBACK_HOST", "INTERNET_ARCHIVE_COLLECTION",
        "INTERNET_ARCHIVE_IDENTIFIER_PREFIX", "INTERNET_ARCHIVE_ACCESS_KEY", "INTERNET_ARCHIVE_SECRET_KEY",
        "STORAGE_BUCKET", "WACZ_BUCKET", "STRIPE_PAYMENTS_APP_INTERNAL_URL", "STRIPE_PAYMENTS_APP_EXTERNAL_URL",
        "PAYMENTS_KEY_ID", "PAYMENTS_PERMA_SECRET_KEY", "PAYMENTS_PERMA_PUBLIC_KEY",
        "PAYMENTS_PAYMENTS_PUBLIC_KEY", "SCAN_URL", "SENTRY_DSN", "SCOOP_API_URL", "SCOOP_API_KEY",
    ]
} | {
    "ADMINS": "[]",
    "DATABASE_PORT": "5432",
    "CELERY_BROKER_URL": "redis://localhost:6379/1",
    "CACHE_LOCATION": "redis://localhost:6379/0",
}

LOAD_SCHEDULE = (
    "import django; django.setup(); from django.conf import settings; "
    "import json; print(json.dumps(sorted(settings.CELERY_BEAT_SCHEDULE)))"
)


def _beat_schedule(env):
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"} | env | {"DJANGO_SETTINGS_MODULE": "perma.settings"}
    result = subprocess.run([sys.executable, "-c", LOAD_SCHEDULE], env=env, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    assert result.returncode == 0, result.stderr[-2000:]
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("tier", ["staging", "prod"])
def test_ecs_settings_load_with_their_beat_schedule(tier):
    schedule = _beat_schedule({
        "PERMA_SETTINGS_MODULE": "settings_ecs",
        "APP_CONFIG": json.dumps(ECS_APP_CONFIG | {"TIER": tier}),
        "DJANGO__USE_SENTRY": "False",
    })
    if tier == "prod":
        assert "reconcile_internet_archive_files" in schedule
        assert "conditionally_queue_internet_archive_uploads_for_date_range" in schedule
        assert "confirm_files_deleted_from_internet_archive" in schedule
    else:
        assert not [job for job in schedule if "internet_archive" in job]


def test_salt_prod_settings_name_known_beat_jobs():
    schedule = _beat_schedule({
        "PERMA_SETTINGS_MODULE": "settings_prod",
        "DJANGO__SECRET_KEY": "x",
        "DJANGO__STRIPE_PAYMENTS_APP_EXTERNAL_URL": "x",
        "DJANGO__STRIPE_PAYMENTS_APP_INTERNAL_URL": "x",
        "DJANGO__LOGGING__handlers__file__filename": "/tmp/perma-settings-test.log",
    })
    assert "reconcile_internet_archive_files" in schedule
