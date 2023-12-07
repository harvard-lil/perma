from django.test import override_settings
from perma.celery_tasks import update_stats


@override_settings(CELERY_ALWAYS_EAGER=True)
def testUpdateStats(db):
    # this tests only that the task runs,
    # not anything about the task itself
    assert update_stats.delay()
