from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
import pytest

from django.conf import settings
from django.db import connections
from django.utils import timezone
from rest_framework.settings import api_settings

from perma.models import CaptureJob
from perma.celery_tasks import clean_up_failed_captures


def test_job_queue_order(link_user_factory, pending_capture_job_factory):
    """ Jobs should be processed round-robin, one per user. """

    user_one = link_user_factory()
    user_two = link_user_factory()

    jobs = [
        pending_capture_job_factory(created_by=user_one, human=True),
        pending_capture_job_factory(created_by=user_one, human=True),
        pending_capture_job_factory(created_by=user_one, human=True),
        pending_capture_job_factory(created_by=user_two, human=True),

        pending_capture_job_factory(created_by=user_two),

        pending_capture_job_factory(created_by=user_one, human=True),
        pending_capture_job_factory(created_by=user_one, human=True),
        pending_capture_job_factory(created_by=user_one, human=True),
        pending_capture_job_factory(created_by=user_two, human=True),
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
        assert queue_position == expected_queue_position, f"Job {i} has queue position {queue_position}, should be {expected_queue_position}."

    # test CaptureJob.get_next_job
    expected_next_jobs = [jobs[i] for i in expected_order]
    next_jobs = [CaptureJob.get_next_job(reserve=True) for i in range(len(jobs))]
    assert next_jobs == expected_next_jobs


@pytest.mark.django_db(transaction=True)
def test_race_condition_prevented(pending_capture_job_factory):
    """ Fetch two jobs at the same time in threads and make sure same job isn't returned to both. """
    jobs = [
        pending_capture_job_factory(),
        pending_capture_job_factory()
    ]

    def get_next_job(i):
        job = CaptureJob.get_next_job(reserve=True)
        for connection in connections.all():
            connection.close()
        return job

    CaptureJob.TEST_PAUSE_TIME = .1
    with ThreadPoolExecutor(max_workers=2) as e:
        fetched_jobs = e.map(get_next_job, range(2))
    CaptureJob.TEST_PAUSE_TIME = 0

    assert set(jobs) == set(fetched_jobs)


@pytest.mark.django_db(transaction=True)
def test_race_condition_not_prevented(pending_capture_job_factory):
    """
        Make sure that test_race_condition_prevented is passing for the right reason --
        should fail if race condition protection is disabled.
    """
    CaptureJob.TEST_ALLOW_RACE = True
    with pytest.raises(AssertionError, match="Extra items in the left set"):
        test_race_condition_prevented(pending_capture_job_factory)
    CaptureJob.TEST_ALLOW_RACE = False


def test_hard_timeout(pending_capture_job):

    # simulate a failed run_next_capture()
    job = CaptureJob.get_next_job(reserve=True)

    # capture_start_time should be set accurately on the server side
    assert (job.capture_start_time - timezone.now()).total_seconds() < 60

    # clean_up_failed_captures shouldn't affect job, since timeout hasn't passed
    clean_up_failed_captures()
    job.refresh_from_db()
    assert job.status == "in_progress"

    # once job is sufficiently old, clean_up_failed_captures should mark it as failed
    job.capture_start_time -= timedelta(seconds=settings.CELERY_TASK_TIME_LIMIT+60)
    job.save()
    clean_up_failed_captures()
    job.refresh_from_db()
    assert job.status == "failed"

    # failed jobs will have a message indicating failure reason
    assert json.loads(job.message)[api_settings.NON_FIELD_ERRORS_KEY][0] == "Timed out."


FACTS = {
    "version": 1,
    "controller": {"pool": "ecs-ec2-staging", "api_release": "abc123", "host": "i-0123"},
    "sandbox": {"capture_ip": "3.84.113.108", "scoop_version": "0.7.0"},
}


@pytest.mark.django_db
def test_capture_facts_are_kept_per_attempt(pending_capture_job_factory):
    """ Retries reuse the CaptureJob, so facts are stored per attempt. """
    from perma.celery_tasks import record_capture_facts

    job = pending_capture_job_factory()
    job.scoop_job_id = "job-1"
    job.attempt = 1
    record_capture_facts(job, {"status": "failed", "capture_facts": FACTS})
    job.attempt = 2
    retry = {**FACTS, "controller": {**FACTS["controller"], "host": "i-0456"}}
    record_capture_facts(job, {"status": "success", "capture_facts": retry})

    rows = list(job.attempt_facts.order_by('attempt').values_list('attempt', 'facts'))
    assert [(attempt, facts["controller"]["host"]) for attempt, facts in rows] == [
        (1, "i-0123"),
        (2, "i-0456"),
    ]
    assert job.attempt_facts.get(attempt=2).scoop_job_id == "job-1"


@pytest.mark.django_db
def test_nothing_is_recorded_without_capture_facts(pending_capture_job_factory):
    from perma.celery_tasks import record_capture_facts

    job = pending_capture_job_factory()
    record_capture_facts(job, {"status": "failed"})
    record_capture_facts(job, {"status": "failed", "capture_facts": None})
    record_capture_facts(job, {"status": "failed", "capture_facts": {"sandbox": "x" * 20_000}})
    assert not job.attempt_facts.exists()


ECS_FAILURE = {
    "id_capture": "97567c4a",
    "status": "failed",
    "stdout_logs": "[19:39:59] WARN STEP [2/12]: Wait for initial page load - failed\n"
                   "[19:39:59] ERROR Navigation to page failed (about:blank).\n",
    "stderr_logs": "Missing artifact 'archive.wacz'\nMissing artifact 'archive.wacz'",
}


@pytest.mark.django_db
@pytest.mark.parametrize("poll_data, tag", [
    # Run as an ECS task: Scoop's output is all in stdout_logs.
    (ECS_FAILURE, "scoop-load-failure"),
    # Run directly: Scoop's errors are in stderr_logs.
    ({**ECS_FAILURE, "stdout_logs": "", "stderr_logs": ECS_FAILURE["stdout_logs"]}, "scoop-load-failure"),
    ({**ECS_FAILURE, "stdout_logs": "", "stderr_logs": "ERROR An error occurred during capture setup"}, "scoop-proxy-failure"),
    ({**ECS_FAILURE, "stdout_logs": None, "stderr_logs": None}, "scoop-silent-failure"),
])
def test_scoop_failures_are_tagged_from_either_log(pending_capture_job_factory, poll_data, tag):
    from perma.celery_tasks import tag_scoop_failure

    job = pending_capture_job_factory()
    tag_scoop_failure(job, poll_data)
    assert list(job.link.tags.names()) == [tag]


@pytest.mark.django_db
def test_unrecognised_scoop_failures_are_reported(pending_capture_job_factory, caplog):
    from perma.celery_tasks import tag_scoop_failure

    job = pending_capture_job_factory()
    tag_scoop_failure(job, {**ECS_FAILURE, "stdout_logs": "something else went wrong"})
    assert not job.link.tags.exists()
    assert any(r.levelname == "ERROR" and "failed" in r.getMessage() for r in caplog.records)
