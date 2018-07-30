from datetime import timedelta
from multiprocessing.pool import ThreadPool

from perma.models import *
from perma.tasks import clean_up_failed_captures

from .utils import PermaTestCase

# TODO:
# - check retry behavior

# lives outside CaptureJobTestCase so it can be used by other tests
def create_capture_job(user, human=True):
    link = Link(created_by=user, submitted_url="http://example.com")
    link.save()
    capture_job = CaptureJob(created_by=user, link=link, human=human, status='pending')
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

        # test CaptureJob.queue_position
        for i, job in enumerate(jobs):
            queue_position = job.queue_position()
            expected_queue_position = expected_order.index(i)+1
            self.assertEqual(queue_position, expected_queue_position, "Job %s has queue position %s, should be %s." % (i, queue_position, expected_queue_position))

        # test CaptureJob.get_next_job
        expected_next_jobs = [jobs[i] for i in expected_order]
        next_jobs = [CaptureJob.get_next_job(reserve=True) for i in range(len(jobs))]
        self.assertListEqual(next_jobs, expected_next_jobs)

    def test_race_condition_prevented(self):
        """ Fetch two jobs at the same time in threads and make sure same job isn't returned to both. """
        jobs = [
            create_capture_job(self.user_one),
            create_capture_job(self.user_one)
        ]

        def get_next_job(i):
            return CaptureJob.get_next_job(reserve=True)

        CaptureJob.TEST_PAUSE_TIME = .1
        fetched_jobs = ThreadPool(2).map(get_next_job, range(2))
        CaptureJob.TEST_PAUSE_TIME = 0

        self.assertSetEqual(set(jobs), set(fetched_jobs))

    def test_race_condition_not_prevented(self):
        """
            Make sure that test_race_condition_prevented is passing for the right reason --
            should fail if race condition protection is disabled.
        """
        CaptureJob.TEST_ALLOW_RACE = True
        self.assertRaisesRegexp(AssertionError, r'^Items in the', self.test_race_condition_prevented)
        CaptureJob.TEST_ALLOW_RACE = False

    def test_hard_timeout(self):
        create_capture_job(self.user_one)

        # simulate a failed run_next_capture()
        job = CaptureJob.get_next_job(reserve=True)

        # capture_start_time should be set accurately on the server side
        self.assertLess((job.capture_start_time - timezone.now()).total_seconds(), 60)

        # clean_up_failed_captures shouldn't affect job, since timeout hasn't passed
        clean_up_failed_captures()
        job.refresh_from_db()
        self.assertEqual(job.status, "in_progress")

        # once job is sufficiently old, clean_up_failed_captures should mark it as failed
        job.capture_start_time -= timedelta(seconds=settings.CELERYD_TASK_TIME_LIMIT+60)
        job.save()
        clean_up_failed_captures()
        job.refresh_from_db()
        self.assertEqual(job.status, "failed")

        # failed jobs will have a message indicating failure reason
        self.assertEqual(json.loads(job.message)[api_settings.NON_FIELD_ERRORS_KEY][0], "Timed out.")
