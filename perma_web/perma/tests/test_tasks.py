from perma.models import Stat
from perma.tasks import get_nightly_stats

from .utils import PermaTestCase

class TasksTestCase(PermaTestCase):
    def test_get_nightly_stats(self):
        old_stat_count = Stat.objects.count()
        get_nightly_stats()
        new_stat_count = Stat.objects.count()
        self.assertEqual(new_stat_count, old_stat_count+1)