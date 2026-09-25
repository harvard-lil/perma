"""
Behavior that exists to keep LinkUser.links_remaining_in_period fast on
production's data.
"""
from unittest.mock import patch

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from perma.models import LinkUser


@pytest.mark.django_db
def test_links_remaining_filters_on_organization_once(link_user):
    # A repeated organization_id IS NULL makes Postgres underestimate the rows
    # it matches and skip perma_link_personal_idx.
    for period in ['once', 'monthly', 'annually']:
        with CaptureQueriesContext(connection) as queries:
            link_user.links_remaining_in_period(period, 10, unlimited=False)
        [count_query] = queries.captured_queries
        assert count_query['sql'].count('"organization_id" IS NULL') == 1, period


@pytest.mark.django_db
def test_create_page_counts_links_once(perma_client, link_user):
    with patch.object(LinkUser, 'links_remaining_in_period', autospec=True, return_value=5) as remaining:
        response = perma_client.get(reverse('create_link'), as_user=link_user)
    assert response.status_code == 200
    assert remaining.call_count == 1
