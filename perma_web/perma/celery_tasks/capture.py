import json
import tempfile
import time

import sentry_sdk
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from urllib3.exceptions import ProtocolError, ReadTimeoutError

from django.conf import settings
from django.core.files.storage import storages
from django.db.models.functions import Now

from perma.exceptions import ScoopAPINetworkException, ScoopAPIException
from perma.models import Capture, CaptureAttemptFacts, CaptureJob
from perma.utils import deployment_pending, send_to_scoop, current_scoop_api, temporary_working_directory
from perma.wsgi_utils import retry_on_exception

import logging
logger = logging.getLogger('celery.django')


### CAPTURE HELPERS ###

class HaltCaptureException(Exception):
    """
        An exception we can trigger to halt capture and release
        all involved resources.
    """
    pass

def inc_progress(capture_job, inc, description):
    capture_job.inc_progress(inc, description)
    print(f"{capture_job.link.guid} step {capture_job.step_count}: {capture_job.step_description}")


### CAPTURE COMPLETION ###

def save_scoop_archive(link, capture_job, data, api):
    inc_progress(capture_job, 1, "Downloading web archive file (WACZ)")

    # mode set to 'ab+' as a workaround for https://github.com/python/cpython/issues/69528
    with tempfile.TemporaryFile('ab+') as tmp_file:

        def download_wacz():

            # Send the API request
            response, _ = send_to_scoop(
                method="get",
                path=f"artifact/{data['id_capture']}/archive.wacz",
                valid_if=lambda code, _: code == 200,
                stream=True,
                api=api
            )

            # Write the response, chunk by chunk, into the temp file.
            # Use the raw response, because Python requests standard methods gunzip the file
            tmp_file.seek(0)
            for chunk in response.raw.stream(10 * 1024, decode_content=False):
                if chunk:
                    tmp_file.write(chunk)

            # Record the file size
            tmp_file.flush()
            link.wacz_size = tmp_file.tell()
            link.save(update_fields=['wacz_size'])

        # See Linear issue LIL-2877 for discussion of these exceptions
        retry_on_exception(
            download_wacz,
            exception=(
                ProtocolError,
                ReadTimeoutError,
                ScoopAPINetworkException,
                ScoopAPIException,
                SoftTimeLimitExceeded
            ),
            attempts=settings.SCOOP_WACZ_DOWNLOAD_RETRIES
        )
        inc_progress(capture_job, 1, "Saving web archive file (WACZ)")
        tmp_file.seek(0)
        storages[settings.WACZ_STORAGE].store_file(
            tmp_file, link.wacz_storage_file(), overwrite=True
        )


def save_archive_metadata(link, capture_job, data):

    inc_progress(capture_job, 1, "Saving metadata")

    # Primary capture
    link.primary_capture.status = 'success'
    link.primary_capture.content_type = data['scoop_capture_summary']['targetUrlContentType']
    link.primary_capture.save(update_fields=['status', 'content_type'])

    if 'pageInfo' in data['scoop_capture_summary']:
        title = data['scoop_capture_summary']['pageInfo'].get('title')
        if title and link.submitted_title == link.get_default_title():
            link.submitted_title = title[:2100]
        description = data['scoop_capture_summary']['pageInfo'].get('description')
        if description:
            link.submitted_description=description[:300]
        link.save(update_fields=[
            'submitted_title',
            'submitted_description'
        ])
    else:
        link.tags.add('scoop-missing-pageinfo')
        logger.warning(f"{capture_job.link_id}: Scoop metadata does not contain pageInfo ({data['id_capture']}).")

    # Make this link private by policy, if the captured domain is on the list.
    target_url = data['scoop_capture_summary']['targetUrl']
    content_url = data['scoop_capture_summary']['targetUrlResolved']
    for url in [target_url, content_url]:
        if any(domain in url for domain in settings.PRIVATE_BY_POLICY_DOMAINS):
            link.is_private = True
            link.private_reason = 'domain'
            link.save(update_fields=[
                'is_private',
                'private_reason'
            ])

    # Provenance
    provenance_filename = data['scoop_capture_summary']['attachments'].get("provenanceSummary")
    if provenance_filename:
        Capture(
            link=link,
            role='provenance_summary',
            status='success',
            record_type='response',
            url=f"file:///{provenance_filename}",
            content_type='text/html; charset=utf-8',
        ).save()

        software = data['scoop_capture_summary']['provenanceInfo']['software'].lower()
        version = data['scoop_capture_summary']['provenanceInfo']['version'].lower()
        link.captured_by_software = f"{software}: {version}"
        link.captured_by_browser = data['scoop_capture_summary']['provenanceInfo']['userAgent']
        link.save(update_fields=[
            'captured_by_software',
            'captured_by_browser'
        ])
    else:
        link.tags.add('scoop-missing-provenance')
        logger.warning(f"{capture_job.link_id}: Scoop warc does not contain provenance summary ({data['id_capture']}).")

    # Other attachments
    supported_attachments = {
        "screenshot": {
            'attr': 'screenshot',
            'content_type': 'image/png',
        },
        "pdf_snapshot": {
            'attr': 'pdfSnapshot',
            'content_type': 'application/pdf',
        },
        "dom_snapshot": {
            'attr': 'domSnapshot',
            'content_type': 'text/html; charset=utf-8',
        },
        "video_summary": {
            'attr': 'videoExtractedSummary',
            'content_type': 'text/html; charset=utf-8',
        }
    }
    for attachment_type in supported_attachments:
        if attachment_filename := data['scoop_capture_summary']['attachments'].get(
            supported_attachments[attachment_type]['attr']
        ):
            Capture(
                link=link,
                role=attachment_type,
                status='success',
                record_type='response',
                url=f"file:///{attachment_filename}",
                content_type=supported_attachments[attachment_type]['content_type'],
            ).save()


def clean_up_failed_captures():
    """
        Clean up any existing jobs that are marked in_progress but must have timed out by now, based on our hard timeout
        setting.
    """
    # use database time with a custom where clause to ensure consistent time across workers
    for capture_job in CaptureJob.objects.filter(status='in_progress').select_related('link').extra(
        where=[f"capture_start_time < now() - make_interval(secs => {settings.CELERY_TASK_TIME_LIMIT})"]
    ):
        capture_job.mark_failed("Timed out.")
        capture_job.link.captures.filter(status='pending').update(status='failed')
        capture_job.link.tags.add('hard-timeout-failure')


### TASKS ###

@shared_task(name='perma.celery_tasks.run_next_capture')
@temporary_working_directory()
def run_next_capture():
    """
        Grab and run the next CaptureJob. This will keep calling itself until there are no jobs left.
    """
    clean_up_failed_captures()

    # get job to work on
    capture_job = CaptureJob.get_next_job(reserve=True)
    if not capture_job:
        return  # no jobs waiting

    if settings.CAPTURE_ENGINE == 'scoop-api':
        logger.debug(f"{capture_job.link_id}: capturing with the Scoop API.")
        capture_with_scoop(capture_job)
    else:
        logger.error(f"Invalid settings.CAPTURE_ENGINE: '{settings.CAPTURE_ENGINE}'. Allowed values: 'perma' or 'scoop-api'.")
        capture_job.link.captures.filter(status='pending').update(status='failed')
        capture_job.mark_failed('Failed due to invalid settings.CAPTURE_ENGINE')

    if not deployment_pending():
        run_next_capture.delay()
    else:
        logger.info("Deployment sentinel is present, not running next capture.")


MAX_CAPTURE_FACTS_BYTES = 16 * 1024


def tag_scoop_failure(capture_job, poll_data):
    """
    Tag a failed capture with the kind of failure, recognised by a line of
    Scoop's output, and report failures of any other kind as errors.

    Which log field holds a given line depends on how the Scoop API runs
    Scoop: run directly, Scoop's own stderr is `stderr_logs`; run as an ECS
    task, all of Scoop's output is `stdout_logs` and `stderr_logs` holds the
    controller's account. So both are searched.
    """
    logs = "\n".join(poll_data.get(field) or "" for field in ('stderr_logs', 'stdout_logs'))

    killed = "\nKilled\n"
    didnt_load = "ERROR Navigation to page failed (about:blank)"
    proxy_error = "ERROR An error occurred during capture setup"
    blocklist_error = "TypeError: Cannot read properties of undefined (reading 'match')"
    playwright_error = "${arg.guid} was not bound in the connection"
    warc_header_error = "An error occurred while creating underlying WARC file"
    if killed in logs:
        logger.warning(f"{capture_job.link_id}: Scoop process killed.")
        capture_job.link.tags.add('scoop-load-failure')
    elif didnt_load in logs:
        logger.warning(f"{capture_job.link_id}: Scoop failed to load submitted URL ({capture_job.submitted_url}).")
        capture_job.link.tags.add('scoop-load-failure')
    elif proxy_error in logs:
        logger.warning(f"{capture_job.link_id}: Scoop failed during capture setup.")
        capture_job.link.tags.add('scoop-proxy-failure')
    elif blocklist_error in logs:
        logger.warning(f"{capture_job.link_id}: Scoop failed while checking the blocklist.")
        capture_job.link.tags.add('scoop-blocklist-failure')
    elif playwright_error in logs:
        logger.warning(f"{capture_job.link_id}: Scoop failed with a Playwright error.")
        capture_job.link.tags.add('scoop-playwright-failure')
    elif warc_header_error in logs:
        logger.warning(f"{capture_job.link_id}: Scoop failed while writing the WARC file.")
        capture_job.link.tags.add('scoop-warc-header-failure')
    elif not logs.strip():
        logger.warning(f"{capture_job.link_id}: Scoop failed without logs ({poll_data['id_capture']}).")
        capture_job.link.tags.add('scoop-silent-failure')
    else:
        failed_step = failed_scoop_step(poll_data)
        controller = (poll_data.get('capture_facts') or {}).get('controller') or {}
        with sentry_sdk.new_scope() as scope:
            # One issue per failing step, rather than one per capture
            scope.fingerprint = ['scoop-capture-failed', failed_step or 'no failed step']
            scope.set_tag('scoop.failed_step', failed_step or 'none')
            for tag, value in (('scoop.exit_code', controller.get('capture_exit_code')),
                               ('scoop.stop_code', controller.get('stop_code'))):
                if value is not None:
                    scope.set_tag(tag, value)
            logger.error(
                "Scoop capture of %s failed at step: %s",
                capture_job.link_id, failed_step,
                extra={'id_capture': poll_data.get('id_capture'), 'poll_data': poll_data},
            )


def failed_scoop_step(poll_data):
    """
    The name of the step Scoop was on when the capture failed, or None.

    Scoop's own summary lists its steps with their outcomes; the capture
    controller's `capture_facts` repeats them, and is present when the summary
    is not.
    """
    summary_steps = (poll_data.get('scoop_capture_summary') or {}).get('steps') or []
    for step in summary_steps:
        if step.get('outcome') == 'failed':
            return step.get('name')
    sandbox_steps = ((poll_data.get('capture_facts') or {}).get('sandbox') or {}).get('steps') or []
    for step in sandbox_steps:
        if step[-1] == 'failed':
            return step[0]
    return None


def record_capture_facts(capture_job, poll_data):
    """
    Keep Scoop's account of how this attempt was made (`capture_facts`), so
    captures can be compared by capture configuration: exit IP, Scoop release,
    worker, egress, experiment arm. Stored per attempt.

    Scoop deployments that predate the field report nothing, and nothing is
    recorded. An envelope far larger than Scoop produces is not stored.
    """
    facts = poll_data.get('capture_facts')
    if not isinstance(facts, dict):
        return
    if len(json.dumps(facts)) > MAX_CAPTURE_FACTS_BYTES:
        logger.warning(f"{capture_job.link_id}: capture_facts over {MAX_CAPTURE_FACTS_BYTES} bytes; not stored.")
        return
    CaptureAttemptFacts.objects.update_or_create(
        capture_job=capture_job,
        attempt=capture_job.attempt,
        defaults={'facts': facts, 'scoop_job_id': capture_job.scoop_job_id},
    )


def capture_with_scoop(capture_job):
    capture_job.link.captured_by_software = 'scoop @ harvard library innovation lab'
    capture_job.link.save(update_fields=['captured_by_software'])
    try:

        # Basic setup
        link = capture_job.link
        target_url = link.ascii_safe_url
        success = False

        # Which Scoop runs this capture, decided once. Every request below
        # names an id_capture that only this instance issued, so re-reading the
        # switch per request would send the poll somewhere that has never heard
        # of the job. Deciding here also means the switch can be flipped while
        # captures are in flight: they finish where they started.
        api = current_scoop_api()

        # Get started, unless the user has deleted the capture in the meantime
        inc_progress(capture_job, 0, "Starting capture")
        if link.user_deleted or link.primary_capture.status != "pending":
            capture_job.mark_completed('deleted')
            return
        capture_job.attempt += 1
        capture_job.save()

        # Request a capture
        inc_progress(capture_job, 1, "Capturing with the Scoop REST API")
        scoop_start_time = time.time()
        capture_job.scoop_start_time = Now()
        capture_job.save(update_fields=['scoop_start_time'])
        _, request_data = send_to_scoop(
            method="post",
            path="capture",
            json={"url": target_url},
            api=api,
            valid_if=lambda code, data: code == 200 and all(key in data for key in {"status", "id_capture"}) and data["status"] in ["pending", "started"],
        )

        # Save the Scoop job id for our records
        capture_job.scoop_job_id = request_data['id_capture']
        capture_job.save(update_fields=['scoop_job_id'])

        # Poll until done
        poll_network_errors = 0
        while True:
            if poll_network_errors > settings.SCOOP_POLL_NETWORK_ERROR_LIMIT:
                logger.error(
                    "Gave up polling Scoop for %s after %s network errors.",
                    capture_job.link_id, poll_network_errors,
                )
                raise HaltCaptureException

            time.sleep(settings.SCOOP_POLL_FREQUENCY)
            try:
                _, poll_data = send_to_scoop(
                    method='get',
                    path=f"capture/{capture_job.scoop_job_id}",
                    json={
                        "url": target_url
                    },
                    api=api,
                    valid_if=lambda code, data: code == 200 and all(key in data for key in {'status'})
                )
            except ScoopAPINetworkException:
                poll_network_errors = poll_network_errors + 1
                continue

            if poll_data['status'] not in ['pending', 'started']:
                scoop_end_time = time.time()
                capture_job.scoop_end_time = Now()
                capture_job.save(update_fields=['scoop_end_time'])
                print(f"Scoop finished in {scoop_end_time - scoop_start_time}s.")
                break

            # Show progress to user. Assumes Scoop won't take much longer than ~60s, worst case scenario
            wait_time = time.time() - scoop_start_time
            inc_progress(capture_job, min(wait_time/60, 0.99), f"Waiting for Scoop job {capture_job.scoop_job_id} to finish: {poll_data['status']}")

        record_capture_facts(capture_job, poll_data)

        if poll_data.get('scoop_capture_summary'):
            states = poll_data['scoop_capture_summary']['states']
            state = poll_data['scoop_capture_summary']['state']
            capture_job.scoop_state = states[state]
            capture_job.save(update_fields=['scoop_state'])

        if poll_data['status'] == 'success':
            success = True
        else:
            # Save logs for debugging
            capture_job.scoop_logs = poll_data
            capture_job.save(update_fields=['scoop_logs'])

            tag_scoop_failure(capture_job, poll_data)

    except HaltCaptureException:
        print("HaltCaptureException thrown")
    except SoftTimeLimitExceeded:
        capture_job.link.tags.add('timeout-failure')
    except:  # noqa
        logger.exception(f"Exception while capturing job {capture_job.link_id}:")
    finally:
        try:
            if success:
                save_scoop_archive(link, capture_job, poll_data, api)
                save_archive_metadata(link, capture_job, poll_data)
                capture_job.mark_completed()
                print(f"{capture_job.link_id} capture succeeded.")
            else:
                print(f"{capture_job.link_id} capture failed.")
        except:  # noqa
            logger.exception(f"Exception while finishing job {capture_job.link_id}:")
        finally:
            capture_job.link.captures.filter(status='pending').update(status='failed')
            if capture_job.status == 'in_progress':
                capture_job.mark_failed('Failed during capture.')
