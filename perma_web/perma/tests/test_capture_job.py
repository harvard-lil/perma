from perma.models import *

from .utils import PermaTestCase

# TODO:
# - check retry behavior

# lives outside CaptureJobTestCase so it can be used by other tests
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

