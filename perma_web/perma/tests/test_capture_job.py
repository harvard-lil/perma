import time
from multiprocessing.pool import ThreadPool

from perma.models import *

from .utils import PermaTestCase

# TODO:
# - check retry behavior

def create_capture_job(user, human=True):
    link = Link(created_by=user, submitted_url="http://example.com")
    link.save()
    capture_job = CaptureJob(link=link, human=human)
    capture_job.save()
    return capture_job

class CaptureJobTestCase(PermaTestCase):

    fixtures = [
        'fixtures/users.json',
        'fixtures/folders.json',
    ]

    def setUp(self):
        super(CaptureJobTestCase, self).setUp()

        self.user_one = LinkUser.objects.get(pk=1)
        self.user_two = LinkUser.objects.get(pk=2)

        self.maxDiff = None  # let assertListEqual compare large lists

        CaptureJob.clear_cache()  # reset cache (test cases don't reset cache keys automatically)

    ### HELPERS ###

    def assertNextJobsMatch(self, expected_next_jobs, expected_order):
        expected_next_jobs = [expected_next_jobs[i] for i in expected_order]
        def get_next_job(i):
            time.sleep(i*.1)  # make sure tasks go into queue in order, so we can check results
            return CaptureJob.get_next_job(reserve=True)
        next_jobs = ThreadPool(len(expected_next_jobs)).map(get_next_job, range(len(expected_next_jobs)))
        self.assertListEqual(next_jobs, expected_next_jobs)

    ### TESTS ###

    def test_job_queue_order(self):
        """ Jobs should be processed round-robin, one per user. """

        jobs = [
            create_capture_job(self.user_one),
            create_capture_job(self.user_one),
            create_capture_job(self.user_one),
            create_capture_job(self.user_two),

            create_capture_job(self.user_two, human=False),

            create_capture_job(self.user_one),
            create_capture_job(self.user_one),
            create_capture_job(self.user_one),
            create_capture_job(self.user_two),
        ]

        expected_order = [
            0, 3,  # u1, u2
            1, 8,  # u1, u2
            2, 5, 6, 7,  # remaining u1 jobs
            4  # robots queue
        ]

        for i, job in enumerate(jobs):
            queue_position = job.queue_position()
            expected_queue_position = expected_order.index(i)+1
            self.assertEqual(queue_position, expected_queue_position, "Job %s has queue position %s, should be %s." % (i, queue_position, expected_queue_position))

        CaptureJob.CACHE_DELAY = .2  # add delay to smoke out concurrency issues
        self.assertNextJobsMatch(jobs, expected_order)

    def test_job_queue_order_fails_without_lock(self):
        """
            If locking is disabled, our job_queue_order test should fail -- this makes sure our concurrency protection
            is actually working.
        """
        temp = CaptureJob.USE_LOCK
        CaptureJob.USE_LOCK = False
        self.assertRaisesRegexp(AssertionError, r'^Lists differ', self.test_job_queue_order)
        CaptureJob.USE_LOCK = temp

