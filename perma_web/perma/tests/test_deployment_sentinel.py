"""The deployment sentinel: the deploy's "pause capture intake" switch.

The ECS deploy runs `manage.py deployment_sentinel set` in a web task, and the
link-creation view and run_next_capture consult perma.utils.deployment_pending
before enqueueing captures. Two signals count: the flag in the shared cache
(what the command writes) and the settings.DEPLOYMENT_SENTINEL file (what the
Salt deploy touches). The cache under settings_testing is django-redis over
fakeredis, so the cache half runs the code path production runs. No database.
"""

from io import StringIO
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django_redis.cache import RedisCache

from perma.utils import DEPLOYMENT_SENTINEL_CACHE_KEY, deployment_pending, deployment_sentinel_state


@pytest.fixture(autouse=True)
def isolated_sentinel(tmp_path):
    """Point the file signal at a path that does not exist, and start with no flag."""
    cache.delete(DEPLOYMENT_SENTINEL_CACHE_KEY)
    with override_settings(DEPLOYMENT_SENTINEL=str(tmp_path / "perma-deployment-pending")):
        yield tmp_path / "perma-deployment-pending"
    cache.delete(DEPLOYMENT_SENTINEL_CACHE_KEY)


def run(action):
    out = StringIO()
    call_command("deployment_sentinel", action, stdout=out)
    return out.getvalue()


def status_exit_code():
    with pytest.raises(SystemExit) as excinfo:
        call_command("deployment_sentinel", "status", stdout=StringIO())
    return excinfo.value.code


def test_not_pending_by_default():
    assert deployment_pending() is False
    assert deployment_sentinel_state() == (False, False, True)
    assert status_exit_code() == 1


def test_set_then_clear():
    assert "set" in run("set")
    assert deployment_pending() is True
    assert status_exit_code() == 0
    # The flag has no TTL: a deploy clears it explicitly.
    assert cache.ttl(DEPLOYMENT_SENTINEL_CACHE_KEY) is None

    assert "cleared" in run("clear")
    assert deployment_pending() is False
    assert status_exit_code() == 1


def test_sentinel_file_still_counts(isolated_sentinel):
    isolated_sentinel.touch()
    assert deployment_pending() is True
    assert deployment_sentinel_state().file_present is True
    assert status_exit_code() == 0
    # clear only touches the cache; the file keeps this host paused
    assert "file" in run("clear")
    assert deployment_pending() is True


def test_set_fails_loudly_when_the_cache_drops_the_write():
    # Under IGNORE_EXCEPTIONS, a Redis outage makes set() a silent no-op and
    # has_key() return None; the command must not report success in that case.
    with patch.object(RedisCache, "set", return_value=None), patch.object(RedisCache, "has_key", return_value=None):
        with pytest.raises(CommandError):
            run("set")


def test_unreadable_cache_counts_as_pending_only_where_required():
    with patch.object(RedisCache, "has_key", return_value=None):
        assert deployment_sentinel_state().cache_readable is False
        assert status_exit_code() == 2
        with override_settings(DEPLOYMENT_SENTINEL_CACHE_REQUIRED=True):
            assert deployment_pending() is True
        with override_settings(DEPLOYMENT_SENTINEL_CACHE_REQUIRED=False):
            assert deployment_pending() is False


def test_call_sites_use_the_helper():
    # Both places that used to test the file directly now go through the helper,
    # so the cache flag pauses them too.
    from perma import celery_tasks
    from api.views import links
    assert celery_tasks.deployment_pending is deployment_pending
    assert links.deployment_pending is deployment_pending
