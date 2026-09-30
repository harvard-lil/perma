from unittest.mock import Mock, patch

from django.core.cache import cache
from django.urls import reverse

import pytest

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
        assert set(response.json()) == {*rate_limits, "inflight", "total_ia_queue", "total_ia_readonly_queue"}
    cache.delete(IA_RATE_LIMITS_CACHE_KEY)
