from django.urls import reverse

import pytest

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
