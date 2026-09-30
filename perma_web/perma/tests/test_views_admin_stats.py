import time
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.urls import reverse

import pytest

from perma.celery_tasks import IA_STATE_CACHE_KEY
from perma.views.admin_stats import IA_RATE_LIMITS_CACHE_KEY

@pytest.mark.parametrize(
    "stat_type",
    [
        "days",
        "celery",
        "random",
        "emails",
        "job_queue"
    ]
)
def test_admin_stats(stat_type, client, admin_user):
    client.force_login(admin_user)
    response = client.get(
        reverse('admin_stats', kwargs={"stat_type": stat_type}),
        secure=True
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_stats_reuses_recent_ia_rate_limits(client, admin_user):
    client.force_login(admin_user)
    cache.delete(IA_RATE_LIMITS_CACHE_KEY)
    rate_limits = {"modify_xml": None, "derive": None, "general_s3": {}, "buckets": {}, "over_limit_details": []}

    broker = Mock()
    broker.llen.return_value = 0

    with (
        patch("perma.views.admin_stats.get_complete_ia_rate_limiting_info", return_value=rate_limits) as get_info,
        patch("perma.views.admin_stats.redis.from_url", return_value=broker),
    ):
        responses = [
            client.get(reverse('admin_stats', kwargs={"stat_type": "rate_limits"}), secure=True)
            for _ in range(2)
        ]

    get_info.assert_called_once()
    for response in responses:
        assert response.status_code == 200
        assert set(response.json()) == {
            *rate_limits, "inflight", "total_ia_queue", "total_ia_readonly_queue", "ia_state", "ia_state_age_seconds",
        }
    cache.delete(IA_RATE_LIMITS_CACHE_KEY)


def _rate_limits_pane(client, admin_user, broker):
    client.force_login(admin_user)
    rate_limits = {"modify_xml": None, "derive": None, "general_s3": {}, "buckets": {}, "over_limit_details": []}
    with (
        patch("perma.views.admin_stats.get_complete_ia_rate_limiting_info", return_value=rate_limits),
        patch("perma.views.admin_stats.redis.from_url", return_value=broker),
    ):
        return client.get(reverse('admin_stats', kwargs={"stat_type": "rate_limits"}), secure=True).json()


@pytest.mark.django_db
def test_admin_stats_ia_pane_uses_the_recorded_ia_state(client, admin_user):
    cache.delete(IA_RATE_LIMITS_CACHE_KEY)
    state = {"decision": "queued", "in_flight_stored": 7, "queue_ia": 3, "queue_ia_readonly": 1}
    cache.set(IA_STATE_CACHE_KEY, {"state": state, "recorded_at": time.time() - 120}, 60)
    broker = Mock()

    out = _rate_limits_pane(client, admin_user, broker)

    broker.llen.assert_not_called()
    assert (out["inflight"], out["total_ia_queue"], out["total_ia_readonly_queue"]) == (7, 3, 1)
    assert out["ia_state"] == state
    assert 119 <= out["ia_state_age_seconds"] <= 125
    cache.delete(IA_STATE_CACHE_KEY)
    cache.delete(IA_RATE_LIMITS_CACHE_KEY)


@pytest.mark.django_db
def test_admin_stats_ia_pane_reads_directly_without_a_recorded_state(client, admin_user):
    cache.delete(IA_RATE_LIMITS_CACHE_KEY)
    cache.delete(IA_STATE_CACHE_KEY)
    broker = Mock()
    broker.llen.side_effect = lambda queue: {"ia": 4, "ia-readonly": 2}[queue]

    out = _rate_limits_pane(client, admin_user, broker)

    assert (out["inflight"], out["total_ia_queue"], out["total_ia_readonly_queue"]) == (None, 4, 2)
    assert (out["ia_state"], out["ia_state_age_seconds"]) == (None, None)
    cache.delete(IA_RATE_LIMITS_CACHE_KEY)
