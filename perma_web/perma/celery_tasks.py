import itertools

import os
import os.path
import tempfile
import time
from datetime import datetime, timedelta
import redis
import tempdir
import socket
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from celery.signals import task_failure
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from django.core.files.storage import default_storage
from django.core.mail import mail_admins
from django.db.models import F
from django.db.models.functions import Greatest, Now
from django.conf import settings
from django.utils import timezone
from django.template.defaultfilters import pluralize, filesizeformat

from perma.models import LinkUser, Link, Capture, \
    CaptureJob, InternetArchiveItem, InternetArchiveFile
from perma.exceptions import PermaPaymentsCommunicationException, ScoopAPINetworkException
from perma.utils import (
    remove_whitespace,
    get_ia_session, ia_global_task_limit_approaching,
    ia_perma_task_limit_approaching, ia_bucket_task_limit_approaching,
    copy_file_data, date_range, send_to_scoop)

import logging
logger = logging.getLogger('celery.django')

import csv
import subprocess
import math
import json

### ERROR REPORTING ###

@task_failure.connect()
def celery_task_failure_email(**kwargs):
    """
    Celery 4.0 onward has no method to send emails on failed tasks
    so this event handler is intended to replace it. It reports truly failed
    tasks, such as those terminated after CELERY_TASK_TIME_LIMIT.
    From https://github.com/celery/celery/issues/3389
    """

    subject = "[Django][{queue_name}@{host}] Error: Task {sender.name} ({task_id}): {exception}".format(
        queue_name='celery',
        host=socket.gethostname(),
        **kwargs
    )

    message = """Task {sender.name} with id {task_id} raised exception:
{exception!r}


Task was called with args: {args} kwargs: {kwargs}.

The contents of the full traceback was:

{einfo}
    """.format(
        **kwargs
    )
    mail_admins(subject, message)


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

def save_scoop_capture(link, capture_job, data):

    inc_progress(capture_job, 1, "Saving metadata")

    #
    # PRIMARY CAPTURE
    #

    link.primary_capture.content_type = data['scoop_capture_summary']['targetUrlContentType']
    link.primary_capture.save(update_fields=['content_type'])

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

    #
    # SCREENSHOT
    #

    screenshot_filename = data['scoop_capture_summary']['attachments'].get("screenshot")
    if screenshot_filename:
        Capture(
            link=link,
            role='screenshot',
            status='success',
            record_type='response',
            url=f"file:///{screenshot_filename}",
            content_type='image/png',
        ).save()
        try:
            assert screenshot_filename.lower().endswith('.png')
        except AssertionError:
            logger.error(f"The screenshot for {link.guid} is not a PNG. Please update its record and our codebase!")

    #
    # OTHER ATTACHMENTS
    #
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

    #
    # WARC
    #
    # mode set to 'ab+' as a workaround for https://bugs.python.org/issue25341
    with tempfile.TemporaryFile('ab+') as tmp_file:

        inc_progress(capture_job, 1, "Downloading web archive file")
        response, _ = send_to_scoop(
            method="get",
            path=f"artifact/{data['id_capture']}/archive.warc.gz",
            valid_if=lambda code, _: code == 200,
            stream=True
        )
        # Use the raw response, because Python requests standard methods gunzip the file
        for chunk in response.raw.stream(10*1024, decode_content=False):
            if chunk:
                tmp_file.write(chunk)
        tmp_file.flush()
        link.warc_size = tmp_file.tell()
        link.save(update_fields=['warc_size'])
        tmp_file.seek(0)

        inc_progress(capture_job, 1, "Saving web archive file")
        default_storage.store_file(tmp_file, link.warc_storage_file(), overwrite=True)

    capture_job.mark_completed()


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

@shared_task
@tempdir.run_in_tempdir()
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
        logger.info(f"{capture_job.link_id}: capturing with the Scoop API.")
        capture_with_scoop(capture_job)
    else:
        logger.error(f"Invalid settings.CAPTURE_ENGINE: '{settings.CAPTURE_ENGINE}'. Allowed values: 'perma' or 'scoop-api'.")
        capture_job.link.captures.filter(status='pending').update(status='failed')
        capture_job.mark_failed('Failed due to invalid settings.CAPTURE_ENGINE')

    if not os.path.exists(settings.DEPLOYMENT_SENTINEL):
        run_next_capture.delay()
    else:
        logger.info("Deployment sentinel is present, not running next capture.")


def capture_with_scoop(capture_job):
    capture_job.link.captured_by_software = 'scoop @ harvard library innovation lab'
    capture_job.link.save(update_fields=['captured_by_software'])
    try:

        # Basic setup
        link = capture_job.link
        target_url = link.ascii_safe_url

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
            valid_if=lambda code, data: code == 200 and all(key in data for key in {"status", "id_capture"}) and data["status"] in ["pending", "started"],
        )

        # Save the Scoop job id for our records
        capture_job.scoop_job_id = request_data['id_capture']
        capture_job.save(update_fields=['scoop_job_id'])

        # Poll until done
        poll_network_errors = 0
        while True:
            if poll_network_errors > settings.SCOOP_POLL_NETWORK_ERROR_LIMIT:
                raise HaltCaptureException

            time.sleep(settings.SCOOP_POLL_FREQUENCY)
            try:
                _, poll_data = send_to_scoop(
                    method='get',
                    path=f"capture/{capture_job.scoop_job_id}",
                    json={
                        "url": target_url
                    },
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

        capture_job.scoop_logs = poll_data
        if poll_data.get('scoop_capture_summary'):
            states = poll_data['scoop_capture_summary']['states']
            state = poll_data['scoop_capture_summary']['state']
            capture_job.scoop_state = states[state]
        capture_job.save(update_fields=['scoop_logs', 'scoop_state'])

        if poll_data['status'] == 'success':
            link.primary_capture.status = 'success'
            link.primary_capture.save(update_fields=['status'])
        else:
            didnt_load = "ERROR Navigation to page failed (about:blank)"
            proxy_error = "ERROR An error occurred during capture setup"
            blocklist_error = "TypeError: Cannot read properties of undefined (reading 'match')"
            playwright_error = "${arg.guid} was not bound in the connection"
            if poll_data['stderr_logs'] and didnt_load in poll_data['stderr_logs']:
                logger.warning(f"{capture_job.link_id}: Scoop failed to load submitted URL ({capture_job.submitted_url}).")
                capture_job.link.tags.add('scoop-load-failure')
            elif poll_data['stderr_logs'] and proxy_error in poll_data['stderr_logs']:
                logger.warning(f"{capture_job.link_id}: Scoop failed during capture setup.")
                capture_job.link.tags.add('scoop-proxy-failure')
            elif poll_data['stderr_logs'] and blocklist_error in poll_data['stderr_logs']:
                logger.warning(f"{capture_job.link_id}: Scoop failed while checking the blocklist.")
                capture_job.link.tags.add('scoop-blocklist-failure')
            elif poll_data['stderr_logs'] and playwright_error in poll_data['stderr_logs']:
                logger.warning(f"{capture_job.link_id}: Scoop failed with a Playwright error.")
                capture_job.link.tags.add('scoop-playwright-failure')
            elif not poll_data['stderr_logs'] and not poll_data['stdout_logs']:
                logger.warning(f"{capture_job.link_id}: Scoop failed without logs ({poll_data['id_capture']}).")
                capture_job.link.tags.add('scoop-silent-failure')
            else:
                logger.error(f"Scoop capture failed: {poll_data}")

    except HaltCaptureException:
        print("HaltCaptureException thrown")
    except SoftTimeLimitExceeded:
        capture_job.link.tags.add('timeout-failure')
    except:  # noqa
        logger.exception(f"Exception while capturing job {capture_job.link_id}:")
    finally:
        try:
            if link.primary_capture.status == 'success':
                save_scoop_capture(link, capture_job, poll_data)
                print(f"{capture_job.link_id} capture succeeded.")
            else:
                print(f"{capture_job.link_id} capture failed.")
        except:  # noqa
            logger.exception(f"Exception while finishing job {capture_job.link_id}:")
        finally:
            capture_job.link.captures.filter(status='pending').update(status='failed')
            if capture_job.status == 'in_progress':
                capture_job.mark_failed('Failed during capture.')


###              ###
### HOUSEKEEPING ###
###              ###

@shared_task(acks_late=True)  # use acks_late for tasks that can be safely re-run if they fail
def cache_playback_status_for_new_links():
    links = Link.objects.permanent().filter(cached_can_play_back__isnull=True)
    queued = 0
    for link_guid in links.values_list('guid', flat=True).iterator():
        cache_playback_status.delay(link_guid)
        queued = queued + 1
    logger.info(f"Queued {queued} links to have their playback status cached.")


@shared_task(acks_late=True)  # use acks_late for tasks that can be safely re-run if they fail
def cache_playback_status(link_guid):
    link = Link.objects.get(guid=link_guid)
    link.cached_can_play_back = link.can_play_back()
    if link.tracker.has_changed('cached_can_play_back'):
        link.save(update_fields=['cached_can_play_back'])


@shared_task()
def sync_subscriptions_from_perma_payments():
    """
    Perma only learns about changes to a customer's record in Perma
    Payments when the user transacts with Perma. For admin convenience,
    refresh Perma's records on demand.
    """
    customers = LinkUser.objects.filter(in_trial=False)
    for customer in customers:
        try:
            customer.get_subscription()
        except PermaPaymentsCommunicationException:
            # This gets logged inside get_subscription; don't duplicate logging here
            pass


@shared_task(acks_late=True)
def populate_warc_size_fields(limit=None):
    """
    One-time task, to populate the warc_size field for links where we missed it, the first time around.
    See https://github.com/harvard-lil/perma/issues/2617 and https://github.com/harvard-lil/perma/issues/2172;
    old links also often lack this metadata.
    """
    links = Link.objects.filter(warc_size__isnull=True, cached_can_play_back=True)
    if limit:
        links = links[:limit]
    queued = 0
    for link_guid in links.values_list('guid', flat=True).iterator():
        populate_warc_size.delay(link_guid)
        queued = queued + 1
    logger.info(f"Queued {queued} links for populating warc_size.")


@shared_task(acks_late=True)
def populate_warc_size(link_guid):
    """
    One-time task, to populate the warc_size field for links where we missed it, the first time around.
    See https://github.com/harvard-lil/perma/issues/2617 and https://github.com/harvard-lil/perma/issues/2172;
    old links also often lack this metadata.
    """
    link = Link.objects.get(guid=link_guid)
    link.warc_size = default_storage.size(link.warc_storage_file())
    link.save(update_fields=['warc_size'])


###                  ###
### INTERNET ARCHIVE ###
###                  ###

CONNECTION_ERRORS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.ConnectTimeout,
    requests.exceptions.HTTPError,
    requests.exceptions.ReadTimeout
)

def queue_batched_tasks(task, query, batch_size=1000, **kwargs):
    """
    A generic queuing task. Chunks the queryset by batch_size,
    and queues up the specified celery task for each chunk, passing in a
    list of the objects' primary keys and any other supplied kwargs.
    """
    query = query.values_list('pk', flat=True)

    first = None
    last = None
    batches_queued = 0
    pks = []
    for pk in query.iterator():

        # track the first pk for logging
        if not first:
            first = pk

        pks.append(pk)
        if len(pks) >= batch_size:
            task.delay(pks, **kwargs)
            batches_queued = batches_queued + 1
            pks = []

        # track the last pk for logging
        last = pk

    remainder = len(pks)
    if remainder:
        task.delay(pks, **kwargs)
        last = pks[-1]

    logger.info(f"Queued {batches_queued} batches of size {batch_size}{' and a single batch of size ' + str(remainder) if remainder else ''}, pks {first}-{last}.")


@shared_task(acks_late=True)
def upload_link_to_internet_archive(link_guid, attempts=0, timeouts=0):
    """
    This task adds a link's WARC and metadata to a "daily" Internet Archive item
    using IA's S3-like API. If it fails, it re-queues itself up to settings.INTERNET_ARCHIVE_RETRY_FOR_RATELIMITING_LIMIT,
    settings.INTERNET_ARCHIVE_UPLOAD_MAX_TIMEOUTS, or settings.INTERNET_ARCHIVE_RETRY_FOR_ERROR_LIMIT times.
    """

    # Get the link and verify that it is eligible for upload
    link = Link.objects.get(guid=link_guid)
    if not link.can_upload_to_internet_archive():
        logger.info(f"Queued Link {link_guid} no longer eligible for upload.")
        return

    # Get or create the appropriate InternetArchiveItem object for this link
    date_string = link.creation_timestamp.strftime('%Y-%m-%d')
    identifier = InternetArchiveItem.DAILY_IDENTIFIER.format(
        prefix=settings.INTERNET_ARCHIVE_DAILY_IDENTIFIER_PREFIX,
        date_string=date_string
    )
    start = InternetArchiveItem.datetime(f"{date_string} 00:00:00")
    end = start + timedelta(days=1)
    perma_item, _created = InternetArchiveItem.objects.get_or_create(
        identifier=identifier,
        span=(start, end),
    )

    # Check the Internet Archive-related status of this link
    perma_file = InternetArchiveFile.objects.filter(
        item_id=identifier,
        link_id=link_guid
    ).first()
    if perma_file:
        if perma_file.status == 'confirmed_present':
            logger.info(f"Not uploading {link_guid} to {identifier}: our records indicate it is already present.")
            return
        elif perma_file.status in ['deletion_attempted', 'deletion_submitted']:
            # If we find ourselves here, something has gotten very mixed up indeed. We probably need a human to have a look.
            # Use the error log, assuming this will happen rarely or never.
            logger.error(f"Please investigate the status of {link_guid}: our records indicate a deletion attempt is in progress, but an upload was attempted in the meantime.")
            return
        elif perma_file.status in ['upload_attempted', 'upload_submitted']:
            logger.info(f"Potentially redundant attempt to upload {link_guid} to {identifier}: if this message recurs, please look into its status.")
        elif perma_file.status == 'confirmed_absent':
            logger.info(f"Uploading {link_guid} (previously deleted) to {identifier}.")
        else:
            logger.warning(f"Not uploading {link_guid} to {identifier}: task not implemented for InternetArchiveFiles with status '{perma_file.status}'.")
            return
    else:
        # A fresh one. Create the InternetArchiveFile here.
        perma_file = InternetArchiveFile(
            item_id=identifier,
            link_id=link_guid,
            status='upload_attempted'
        )
        perma_file.save()
        logger.info(f"Uploading {link_guid} to {identifier}.")


    # Attempt the upload

    def retry_upload(attempt_count, timeout_count):
        perma_item.tasks_in_progress = F('tasks_in_progress') - 1
        perma_item.save(update_fields=['tasks_in_progress'])
        upload_link_to_internet_archive.delay(link_guid, attempt_count, timeout_count)

    # Indicate that this InternetArchiveItem should be tracked until further notice
    perma_item.tasks_in_progress = F('tasks_in_progress') + 1
    perma_item.save(update_fields=['tasks_in_progress'])

    # Record that we are attempting an upload
    perma_file.status = 'upload_attempted'
    perma_file.save(update_fields=['status'])

    # Make sure we aren't exceeding rate limits
    ia_session = get_ia_session()
    s3_is_overloaded, s3_details = ia_session.get_s3_load_info(
        identifier=identifier,
        access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY
    )
    perma_task_limit_approaching = ia_perma_task_limit_approaching(s3_details)
    global_task_limit_approaching = ia_global_task_limit_approaching(s3_details)
    bucket_task_limit_approaching = ia_bucket_task_limit_approaching(s3_details)
    if s3_is_overloaded or perma_task_limit_approaching or global_task_limit_approaching or bucket_task_limit_approaching:
        # This logging is noisy: we're not sure whether we want it or not, going forward.
        logger.warning(f"Skipped IA upload task for {link_guid} (IA Item {identifier}) due to rate limit: {s3_details}.")
        retry = (
            not settings.INTERNET_ARCHIVE_RETRY_FOR_RATELIMITING_LIMIT or
            (settings.INTERNET_ARCHIVE_RETRY_FOR_RATELIMITING_LIMIT > attempts + 1)
        )
        if retry:
            retry_upload(attempts + 1, timeouts)
        else:
            msg = f"Not retrying IA upload task for {link_guid} (IA Item {identifier}): rate limit retry maximum reached."
            if settings.INTERNET_ARCHIVE_EXCEPTION_IF_RETRIES_EXCEEDED:
                logger.exception(msg)
            else:
                logger.warning(msg)
        return

    # Get the IA Item
    try:
        ia_item = ia_session.get_item(identifier)
    except CONNECTION_ERRORS:
        # Sometimes, requests to retrieve the metadata of an IA Item time out.
        # Retry later, without counting this as a failed attempt
        logger.info(f"Re-queued 'upload_link_to_internet_archive' for {link_guid} after a connection error.")
        retry_upload(attempts, timeouts)
        return

    # Attempt the upload
    try:

        # mode set to 'ab+' as a workaround for https://bugs.python.org/issue25341
        with tempfile.TemporaryFile('ab+') as temp_warc_file:

            # copy warc to local disk storage for upload.
            # (potentially not necessary, but we think more robust against network conditions
            # https://github.com/harvard-lil/perma/commit/25eb14ce634675ffe67d0f14f51308f1202b53ea)
            with default_storage.open(link.warc_storage_file()) as warc_file:
                logger.info(f"Downloading {link.warc_storage_file()} from S3.")
                copy_file_data(warc_file, temp_warc_file)
                temp_warc_file.seek(0)

            response = ia_item.upload_file(
                body=temp_warc_file,
                key=InternetArchiveFile.WARC_FILENAME.format(guid=link_guid),
                metadata=InternetArchiveItem.standard_metadata_for_date(date_string),
                file_metadata=InternetArchiveFile.standard_metadata_for_link(link),
                access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY,
                secret_key=settings.INTERNET_ARCHIVE_SECRET_KEY,
                queue_derive=False,
                retries=0,
                retries_sleep=0,
                verbose=False,
                debug=False,
            )
            assert response.status_code == 200, f"IA returned {response.status_code}): {response.text}"
    except SoftTimeLimitExceeded:
        retry = (
            not settings.INTERNET_ARCHIVE_UPLOAD_MAX_TIMEOUTS or
            (settings.INTERNET_ARCHIVE_UPLOAD_MAX_TIMEOUTS > timeouts + 1)
        )
        if retry:
            logger.info(f"Re-queued 'upload_link_to_internet_archive' for {link_guid} after SoftTimeLimitExceeded.")
            retry_upload(attempts, timeouts + 1)
        else:
            msg = f"Not retrying IA upload task for {link_guid} (IA Item {identifier}): timeout retry maximum reached."
            if settings.INTERNET_ARCHIVE_EXCEPTION_IF_RETRIES_EXCEEDED:
                logger.exception(msg)
            else:
                logger.warning(msg)
        return

    except CONNECTION_ERRORS:
        # If Internet Archive is unavailable, retry later, without counting this as a failed attempt.
        logger.info(f"Re-queued 'upload_link_to_internet_archive' for {link_guid} after a connection error.")
        retry_upload(attempts, timeouts)
        return

    except (requests.exceptions.HTTPError, AssertionError) as e:
        # upload_file internally calls response.raise_for_status, catching HTTPError
        # and re-raising with a custom error message.
        # https://github.com/jjjake/internetarchive/blob/a2de155d15aab279de6bb6364998266c21752ca6/internetarchive/item.py#L1048
        # https://github.com/jjjake/internetarchive/blob/a2de155d15aab279de6bb6364998266c21752ca6/internetarchive/item.py#L1073
        # ('InternalError', ('We encountered an internal error. Please try again.', '500 Internal Server Error'))
        # ('ServiceUnavailable', ('Please reduce your request rate.', '503 Service Unavailable'))
        # ('SlowDown', ('Please reduce your request rate.', '503 Slow Down'))
        error_string = str(e)
        if "Please reduce your request rate" in error_string:
            # This logging is noisy: we're not sure whether we want it or not, going forward.
            logger.warning(f"Upload task for {link_guid} (IA Item {identifier}) prevented by rate-limiting. Will retry if allowed.")
            retry = (
                not settings.INTERNET_ARCHIVE_RETRY_FOR_RATELIMITING_LIMIT or
                (settings.INTERNET_ARCHIVE_RETRY_FOR_RATELIMITING_LIMIT > attempts + 1)
            )
            if retry:
                retry_upload(attempts + 1, timeouts)
            else:
                msg = f"Not retrying IA upload task for {link_guid} (IA Item {identifier}): rate limit retry maximum reached."
                if settings.INTERNET_ARCHIVE_EXCEPTION_IF_RETRIES_EXCEEDED:
                    logger.exception(msg)
                else:
                    logger.warning(msg)
            return
        elif ("The bucket namespace is shared" in error_string or
              "Failed to get necessary short term bucket lock" in error_string or
              "auto_make_bucket requested" in error_string or
              ("Checking for identifier availability..." in error_string and "not_available" in error_string)):
            # These errors happen when we concurrently request to upload more than one file to an Item
            # that does not yet exist: each concurrent request attempts to create it, and is thwarted
            # by IA code guarding against inconsistent state. We need to support concurrent uploads
            # because of our volume. Since we cannot create the Item in an advance preparatory step
            # without a lot of engineering work on our end, we simply live with these errors, and
            # re-queue the failed attempts, without considering it a failed attempt.
            retry_upload(attempts, timeouts)
            return
        else:
            logger.warning(f"Upload task for {link_guid} (IA Item {identifier}) encountered an unexpected error ({ str(e).strip() }). Will retry if allowed.")
            retry = (
                not settings.INTERNET_ARCHIVE_RETRY_FOR_ERROR_LIMIT or
                (settings.INTERNET_ARCHIVE_RETRY_FOR_ERROR_LIMIT > attempts + 1)
            )
            if retry:
                retry_upload(attempts + 1, timeouts)
            else:
                msg = f"Not retrying IA upload task for {link_guid} (IA Item {identifier}, File {link.guid}): error retry maximum reached."
                if settings.INTERNET_ARCHIVE_EXCEPTION_IF_RETRIES_EXCEEDED:
                    logger.exception(msg)
                else:
                    logger.warning(msg)
            return

    # Record that the upload has been submitted
    perma_file.status = 'upload_submitted'
    perma_file.save(update_fields=['status'])

    logger.info(f"Uploaded {link_guid} to {identifier}: confirmation pending.")


@shared_task(acks_late=True)
def queue_file_uploaded_confirmation_tasks(limit=None):
    """
    It takes some time for IA to finish processing uploads, even after the S3-like API
    returns a success code. This task schedules a confirmation task for each file we've
    attempted to upload but have not yet verified has succeeded. We do this on a schedule,
    rather than immediately upon uploading a file, in order to introduce a delay: if we
    start checking immediately, an intolerable number of attempts fail... which causes
    too much IA API usage and too much churn.

    This may be too blunt an instrument; we may need to introduce a delay in the confirmation
    task itself, sleeping between each retry, but we want to try this first: if we can, we want
    to avoid having sleeping-but-active celery tasks.
    """
    tasks_in_ia_readonly_queue = redis.from_url(settings.CELERY_BROKER_URL).llen('ia-readonly')

    if not tasks_in_ia_readonly_queue:

        file_ids = InternetArchiveFile.objects.filter(
                    status='upload_submitted'
                ).exclude(
                    item_id__in=[
                        'daily_perma_cc_2022-07-25',
                        'daily_perma_cc_2022-07-21',
                        'daily_perma_cc_2022-07-20',
                        'daily_perma_cc_2022-07-19'
                    ]
                ).values_list(
                    'id', flat=True
                )[:limit]

        queued = 0
        for file_id in file_ids.iterator():
            confirm_file_uploaded_to_internet_archive.delay(file_id)
            queued = queued + 1
        logger.info(f"Queued the file upload confirmation task for {queued} InternetArchiveFiles.")

    else:
        logger.info(f"Skipped the queuing of file upload confirmation tasks: {tasks_in_ia_readonly_queue} task{pluralize(tasks_in_ia_readonly_queue)} in the ia-readonly queue.")

@shared_task(acks_late=True)
def confirm_file_uploaded_to_internet_archive(file_id, attempts=0, connection_errors=0):
    """
    This task checks to see if a WARC uploaded to IA's S3-like API has been processed
    and the new WARC is now visibly a part of the expected IA Item;
    if not, the task re-queues itself up to settings.INTERNET_ARCHIVE_RETRY_FOR_ERROR_LIMIT times.
    Once the file is confirmed to be present, it marks that IA item needs to have its
    "derive.php" task re-triggered.
    """
    perma_file = InternetArchiveFile.objects.select_related('item', 'link').get(id=file_id)
    perma_item = perma_file.item
    link = perma_file.link

    if perma_file.status == 'confirmed_present':
        logger.info(f"InternetArchiveFile {file_id} ({link.guid}) already confirmed to be uploaded to {perma_item.identifier}.")
        return

    ia_session = get_ia_session()
    try:
        ia_item = ia_session.get_item(perma_item.identifier)
        ia_file = ia_item.get_file(InternetArchiveFile.WARC_FILENAME.format(guid=link.guid))
    except CONNECTION_ERRORS:
        # Sometimes, requests to retrieve the metadata of an IA Item time out. Retry later.
        if connection_errors < settings.INTERNET_ARCHIVE_RETRY_FOR_CONFIRMATION_CONNECTION_ERROR:
            confirm_file_uploaded_to_internet_archive.delay(file_id, attempts, connection_errors + 1)
            logger.info(f"Re-queued 'confirm_link_uploaded_to_internet_archive' for InternetArchiveFile {file_id} ({link.guid}) after a connection error.")
        return

    expected_metadata = InternetArchiveFile.standard_metadata_for_link(link)
    try:
        assert ia_file.exists
        for k, v in expected_metadata.items():
            # IA normalizes whitespace idiosyncratically:
            # ignore all whitespace when checking for expected values
            assert remove_whitespace(ia_file.metadata.get(k, '')) == remove_whitespace(v), f"expected {k}: {v}, got {ia_file.metadata.get(k)}."
    except AssertionError:
        # IA's tasks can take some time to complete;
        # the upload-related tasks for this link appear not to have finished yet.
        # We'll need to check again later, the next time celerybeat schedules these tasks.
        logger.info(f"Submitted upload of {link.guid} to IA Item {perma_item.identifier} not yet confirmed.")
        return

    # Update the InternetArchiveFile accordingly
    perma_file.update_from_ia_metadata(ia_file.metadata)
    perma_file.status = 'confirmed_present'
    perma_file.cached_size =  ia_file.size
    perma_file.save(update_fields=[
        'status',
        'cached_size',
        'cached_title',
        'cached_comments',
        'cached_external_identifier',
        'cached_external_identifier_match_date',
        'cached_format',
        'cached_submitted_url',
        'cached_perma_url'
    ])

    # If this is the first confirmed upload to this IA item,
    # cache its basic metadata locally
    if not perma_item.confirmed_exists:
        perma_item.confirmed_exists = True
        perma_item.added_date = InternetArchiveItem.datetime(ia_item.metadata['addeddate'])
        perma_item.cached_title = ia_item.metadata['title']
        perma_item.cached_description = ia_item.metadata.get('description')
        perma_item.save(update_fields=[
            'confirmed_exists',
            'added_date',
            'cached_title',
            'cached_description'
        ])

    # Update InternetArchiveItem accordingly
    perma_item.derive_required = True
    perma_item.cached_file_count = ia_item.files_count
    perma_item.tasks_in_progress = Greatest(F('tasks_in_progress') - 1, 0)
    perma_item.save(update_fields=[
        'derive_required',
        'cached_file_count',
        'tasks_in_progress'
    ])

    logger.info(f"Confirmed upload of {link.guid} to {perma_item.identifier}.")


@shared_task(acks_late=True)
def delete_link_from_daily_item(link_guid, attempts=0):
    perma_file = InternetArchiveFile.objects.select_related('item').get(link_id=link_guid, item__span__isempty=False)
    perma_item = perma_file.item
    identifier = perma_item.identifier

    def retry_deletion(attempt_count):
        perma_item.tasks_in_progress = F('tasks_in_progress') - 1
        perma_item.save(update_fields=['tasks_in_progress'])
        delete_link_from_daily_item.delay(link_guid, attempt_count)

    if perma_file.status == 'confirmed_absent':
        logger.info(f"The daily InternetArchiveFile for {link_guid} is already confirmed absent from {identifier}.")
        return
    elif perma_file.status in ['upload_attempted', 'upload_submitted']:
        # If we find ourselves here, something has gotten very mixed up indeed. We probably need a human to have a look.
        # Use the error log, assuming this will happen rarely or never.
        logger.error(f"Please investigate the status of {link_guid}: our records indicate an upload attempt is in progress, but a deletion was attempted in the meantime.")
        return
    elif perma_file.status in ['deletion_attempted', 'deletion_submitted']:
        logger.info(f"Potentially redundant attempt to delete {link_guid} from {identifier}: if this message recurs, please look into its status.")
    elif perma_file.status == 'confirmed_present':
        logger.info(f"Deleting {link_guid} from {identifier}.")
    else:
        logger.warning(f"Not deleting {link_guid} from {identifier}: task not implemented for InternetArchiveFiles with status '{perma_file.status}'.")
        return

    # Record that we are attempting a deletion
    perma_file.status = 'deletion_attempted'
    perma_file.save(update_fields=['status'])

    # Indicate that this InternetArchiveItem should be tracked until further notice
    perma_item.tasks_in_progress = F('tasks_in_progress') + 1
    perma_item.save(update_fields=['tasks_in_progress'])

    # Make sure we aren't exceeding rate limits
    ia_session = get_ia_session()
    s3_is_overloaded, s3_details = ia_session.get_s3_load_info(
        identifier=identifier,
        access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY
    )
    perma_task_limit_approaching = ia_perma_task_limit_approaching(s3_details)
    global_task_limit_approaching = ia_global_task_limit_approaching(s3_details)
    if s3_is_overloaded or perma_task_limit_approaching or global_task_limit_approaching:
        # This logging is noisy: we're not sure whether we want it or not, going forward.
        logger.warning(f"Skipped IA deletion task for {link_guid} (IA Item {identifier}) due to rate limit: {s3_details}.")
        retry = (
            not settings.INTERNET_ARCHIVE_RETRY_FOR_RATELIMITING_LIMIT or
            (settings.INTERNET_ARCHIVE_RETRY_FOR_RATELIMITING_LIMIT > attempts + 1)
        )
        if retry:
            retry_deletion(attempts + 1)
        else:
            msg = f"Not retrying IA deletion task for {link_guid} (IA Item {identifier}): rate limit retry maximum reached."
            if settings.INTERNET_ARCHIVE_EXCEPTION_IF_RETRIES_EXCEEDED:
                logger.exception(msg)
            else:
                logger.warning(msg)
        return

    # Get the IA Item and File
    try:
        ia_item = ia_session.get_item(identifier)
        ia_file = ia_item.get_file(InternetArchiveFile.WARC_FILENAME.format(guid=link_guid))
    except CONNECTION_ERRORS:
        # Sometimes, requests to retrieve the metadata of an IA Item time out.
        # Retry later, without counting this as a failed attempt
        logger.info(f"Re-queued 'delete_link_from_daily_item' for {link_guid} after a connection error.")
        retry_deletion(attempts)
        return

    # attempt the deletion
    try:
        response = ia_file.delete(
            cascade_delete=False,  # is this correct? not sure: test with "derived" items
            access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY,
            secret_key=settings.INTERNET_ARCHIVE_SECRET_KEY,
            verbose=False,
            debug=False,
            retries=0,
        )
        assert response.status_code == 204, f"IA returned {response.status_code}): {response.text}"
    except (requests.exceptions.RetryError,
            requests.exceptions.HTTPError,
            OSError,
            AssertionError) + CONNECTION_ERRORS as e:
        # `delete` internally calls response.raise_for_status catches and re-raises these exceptions.
        # https://github.com/jjjake/internetarchive/blob/a2de155d15aab279de6bb6364998266c21752ca6/internetarchive/files.py#L354
        # I am not sure why that is a longer list than the `upload` code catches.
        # It could be that we should catch the longer list in both places.
        # I am anticipating that the rate-limiting related error messages will be identical here,
        # but do not know if that is in fact the case.
        # ('InternalError', ('We encountered an internal error. Please try again.', '500 Internal Server Error'))
        # ('ServiceUnavailable', ('Please reduce your request rate.', '503 Service Unavailable'))
        # ('SlowDown', ('Please reduce your request rate.', '503 Slow Down'))
        if "Please reduce your request rate" in str(e):
            # This logging is noisy: we're not sure whether we want it or not, going forward.
            logger.warning(f"Deletion task for {link_guid} (IA Item {identifier}) prevented by rate-limiting. Will retry if allowed.")
            retry = (
                not settings.INTERNET_ARCHIVE_RETRY_FOR_RATELIMITING_LIMIT or
                (settings.INTERNET_ARCHIVE_RETRY_FOR_RATELIMITING_LIMIT > attempts + 1)
            )
            if retry:
                retry_deletion(attempts + 1)
            else:
                msg = f"Not retrying IA deletion task for {link_guid} (IA Item {identifier}): rate limit retry maximum reached."
                if settings.INTERNET_ARCHIVE_EXCEPTION_IF_RETRIES_EXCEEDED:
                    logger.exception(msg)
                else:
                    logger.warning(msg)
            return
        else:
            logger.warning(f"Deletion task for {link_guid} (IA Item {identifier}) encountered an unexpected error ({ str(e).strip() }). Will retry if allowed.")
            retry = (
                not settings.INTERNET_ARCHIVE_RETRY_FOR_ERROR_LIMIT or
                (settings.INTERNET_ARCHIVE_RETRY_FOR_ERROR_LIMIT > attempts + 1)
            )
            if retry:
                retry_deletion(attempts + 1)
            else:
                msg = f"Not retrying IA deletion task for {link_guid} (IA Item {identifier}, File {link_guid}): error retry maximum reached."
                if settings.INTERNET_ARCHIVE_EXCEPTION_IF_RETRIES_EXCEEDED:
                    logger.exception(msg)
                else:
                    logger.warning(msg)
            return

    # Record that the deletion has been submitted
    perma_file.status = 'deletion_submitted'
    perma_file.save(update_fields=['status'])

    logger.info(f"Requested deletion of {link_guid} from {identifier}: confirmation pending.")


@shared_task(acks_late=True)
def confirm_file_deleted_from_daily_item(file_id, attempts=0, connection_errors=0):
    """
    This task checks to see if a file we have requested be deleted from internet archive
    is still visibly a part of the expected IA Item;
    if it is, the task re-queues itself up to settings.INTERNET_ARCHIVE_RETRY_FOR_ERROR_LIMIT times.
    Once the file is confirmed to be absent, it marks that IA item needs to have its
    "derive.php" task re-triggered.
    """
    perma_file = InternetArchiveFile.objects.select_related('item').get(id=file_id)
    perma_item = perma_file.item
    guid = perma_file.link_id

    if perma_file.status == 'confirmed_absent':
        logger.info(f"InternetArchiveFile {file_id} ({guid}) already confirmed absent from {perma_item.identifier}.")
        return

    ia_session = get_ia_session()
    try:
        ia_item = ia_session.get_item(perma_item.identifier)
        ia_file = ia_item.get_file(InternetArchiveFile.WARC_FILENAME.format(guid=guid))
    except CONNECTION_ERRORS:
        # Sometimes, requests to retrieve the metadata of an IA Item time out. Retry later.
        if connection_errors < settings.INTERNET_ARCHIVE_RETRY_FOR_CONFIRMATION_CONNECTION_ERROR:
            confirm_file_deleted_from_daily_item.delay(file_id, attempts, connection_errors + 1)
            logger.info(f"Re-queued 'confirm_file_deleted_from_daily_item' for InternetArchiveFile {file_id} ({guid}) after a connection error.")
        return

    try:
        assert not ia_file.exists
    except AssertionError:
        # IA's tasks can take some time to complete;
        # the deletion-related tasks for this link appear not to have finished yet.
        # We need to check again later.
        retry = (
            not settings.INTERNET_ARCHIVE_RETRY_FOR_ERROR_LIMIT or
            (settings.INTERNET_ARCHIVE_RETRY_FOR_ERROR_LIMIT > attempts + 1)
        )
        if retry:
            confirm_file_deleted_from_daily_item.delay(file_id, attempts + 1)
            logger.info(f"Re-queued 'confirm_file_deleted_from_daily_item' for InternetArchiveFile {file_id} ({guid}).")
        else:
            msg = f"Not retrying 'confirm_file_deleted_from_daily_item' for {file_id} (IA Item {perma_item.identifier}, File {guid}): error retry maximum reached."
            if settings.INTERNET_ARCHIVE_EXCEPTION_IF_RETRIES_EXCEEDED:
                logger.exception(msg)
            else:
                logger.warning(msg)
        return

    # Update the InternetArchiveFile accordingly
    perma_file.status = 'confirmed_absent'
    perma_file.zero_cached_ia_metadata()
    perma_file.save(update_fields=[
        'status',
        'cached_size',
        'cached_title',
        'cached_comments',
        'cached_external_identifier',
        'cached_external_identifier_match_date',
        'cached_format',
        'cached_submitted_url',
        'cached_perma_url'
    ])

    # Update InternetArchiveItem accordingly
    perma_item.derive_required = True
    perma_item.cached_file_count = ia_item.files_count
    perma_item.tasks_in_progress = Greatest(F('tasks_in_progress') - 1, 0)
    perma_item.save(update_fields=[
        'derive_required',
        'cached_file_count',
        'tasks_in_progress'
    ])

    logger.info(f"Confirmed deletion of {guid} from {perma_item.identifier}.")


@shared_task(acks_late=True)
def queue_file_deleted_confirmation_tasks(limit=100):
    """
    It takes some time for IA to finish processing deletions, even after the S3-like API
    returns a success code. This task schedules a confirmation task for each file we've
    attempted to delete but have not yet verified has succeeded. We do this on a schedule,
    rather than immediately upon uploading a file, in order to introduce a delay: if we
    start checking immediately, an intolerable number of attempts fail... which causes
    too much IA API usage and too much churn.

    This may be too blunt an instrument; we may need to introduce a delay in the confirmation
    task itself, sleeping between each retry, but we want to try this first: if we can, we want
    to avoid having sleeping-but-active celery tasks.
    """
    tasks_in_ia_readonly_queue = redis.from_url(settings.CELERY_BROKER_URL).llen('ia-readonly')

    if not tasks_in_ia_readonly_queue:

        file_ids = InternetArchiveFile.objects.filter(
                    status='deletion_submitted'
                ).exclude(
                    item_id__in=[
                        'daily_perma_cc_2022-07-25',
                        'daily_perma_cc_2022-07-21',
                        'daily_perma_cc_2022-07-20',
                        'daily_perma_cc_2022-07-19'
                    ]
                ).values_list(
                    'id', flat=True
                )[:limit]

        queued = 0
        for file_id in file_ids.iterator():
            confirm_file_deleted_from_daily_item.delay(file_id)
            queued = queued + 1
        logger.info(f"Queued the file deleted confirmation task for {queued} InternetArchiveFiles.")

    else:
        logger.info(f"Skipped the queuing of file deleted confirmation tasks: {tasks_in_ia_readonly_queue} task{pluralize(tasks_in_ia_readonly_queue)} in the ia-readonly queue.")


@shared_task
def queue_internet_archive_deletions(limit=None):
    """
    Queue deletion tasks for any currently-ineligible Links that were eligible
    when daily IA items were initially created...and so were uploaded.

    (Don't limit by creation date: this is expected to be a small number.)
    """
    to_delete = Link.objects.ineligible_for_ia().filter(
        internet_archive_items__span__isempty=False,
        internet_archive_files__status__in=['confirmed_present', 'deletion_attempted']
    )[:limit]

    # Queue the tasks
    queued = []
    query_started = time.time()
    query_ended = None
    try:
        for guid in to_delete.values_list('guid', flat=True).iterator():
            if not query_ended:
                # log here: the query won't actually be evaluated until .iterator() is called
                query_ended = time.time()
                logger.info(f"Ready to queue links for deletion in {query_ended - query_started} seconds.")
            delete_link_from_daily_item.delay(guid)
            queued.append(guid)
    except SoftTimeLimitExceeded:
        pass

    logger.info(f"Queued { len(queued) } links for deletion ({queued[0]} through {queued[-1]}).")


def queue_internet_archive_uploads_for_date(date_string, limit=100):
    """
    Queue upload tasks for all currently-eligible Links created on a given day,
    if we have not yet attempted to upload them to a "daily" Item.
    """

    # force the query to evaluate so we can time it, and use a strategy that
    # lets us test whether any links were found and iterate through the queryset,
    # without needing to query the database twice
    query_started = time.time()
    to_upload = Link.objects.ia_upload_pending(date_string, limit).iterator()
    first_link_to_upload = next(to_upload, None)
    query_ended = time.time()

    if first_link_to_upload:
        logger.info(f"Ready to queue links for upload in {query_ended - query_started} seconds.")
        queued = []
        try:
            for link in itertools.chain([first_link_to_upload], to_upload):
                upload_link_to_internet_archive.delay(link.guid)
                queued.append(link.guid)
        except SoftTimeLimitExceeded:
            pass
        logger.info(f"Queued { len(queued) } links for upload ({queued[0]} through {queued[-1]}).")
        return len(queued)
    else:
        logger.info(f"Found no links to upload in {query_ended - query_started} seconds.")
        identifier = InternetArchiveItem.DAILY_IDENTIFIER.format(
            prefix=settings.INTERNET_ARCHIVE_DAILY_IDENTIFIER_PREFIX,
            date_string=date_string
        )
        try:
            item = InternetArchiveItem.objects.get(identifier=identifier)
            # Don't mark an item complete if it's yesterday's
            if timezone.now() - item.span.lower > timedelta(days=3):
                item.complete = True
                item.save(update_fields=['complete'])
                logger.info(f"Found no pending links: marked IA Item {item.identifier} complete.")
            else:
                logger.info(f"Found no pending links for recent IA Item {item.identifier}; not marking complete.")
        except InternetArchiveItem.DoesNotExist:
            logger.info(f"Found no pending links for {date_string}.")
        return 0


@shared_task
def conditionally_queue_internet_archive_uploads_for_date_range(start_date_string, end_date_string, daily_limit=100, limit=None):
    """
    Queues up to settings.INTERNET_ARCHIVE_MAX_SIMULTANEOUS_UPLOADS links for upload to IA, spread over
    a number of days such that no more than `daily_limit` are ever queued for a particular day. May
    queue fewer links, if an explicit `limit` is passed in, or if:
    - there are pending tasks in the Celery queue
    - there are submitted-but-as-of-yet-unfinished upload requests being processed by IA
    - there are not enough qualifying links in the date range
    - there are not enough qualifying links in the date range, while respecting daily_limit
    """
    tasks_in_ia_queue = redis.from_url(settings.CELERY_BROKER_URL).llen('ia')
    if tasks_in_ia_queue:
        logger.info(f"Skipped the queuing of file upload tasks: {tasks_in_ia_queue} task{pluralize(tasks_in_ia_queue)} in the ia queue.")
        return

    if not start_date_string:
        oldest_incomplete_daily_item_in_backlog = InternetArchiveItem.objects.filter(
              span__isempty=False,
              span__gt=('2021-11-10', '2021-11-11'),
              complete=False,
        ).order_by('span').first()
        start = oldest_incomplete_daily_item_in_backlog.span.lower.date()
    else:
        start = datetime.strptime(start_date_string, '%Y-%m-%d').date()
    if not end_date_string:
        end = datetime.now().date()
    else:
        end = datetime.strptime(end_date_string, '%Y-%m-%d').date()
    if start > end:
        logger.error(f"Invalid range: start={start} end={end}.")

    tasks_in_flight = InternetArchiveItem.inflight_task_count()
    max_to_queue = settings.INTERNET_ARCHIVE_MAX_SIMULTANEOUS_UPLOADS - tasks_in_flight
    to_queue = min(max_to_queue, limit) if limit else max_to_queue

    if to_queue < 0:
        logger.error(f"Something is amiss with the IA upload process: InternetArchiveItem.inflight_task_count ({InternetArchiveItem.inflight_task_count()}) is larger than settings.INTERNET_ARCHIVE_MAX_SIMULTANEOUS_UPLOADS.")
        return

    if to_queue:

        total_queued = 0
        queued = []
        for day in date_range(start, end, timedelta(days=1)):
            if total_queued < to_queue:
                date_string = day.strftime('%Y-%m-%d')
                if date_string in ['2022-07-25', '2022-07-21', '2022-07-20', '2022-07-19']:
                    # for now, skip these days: by accident, we don't presently have edit
                    # privileges for the IA Items with these identifiers
                    continue
                identifier = InternetArchiveItem.DAILY_IDENTIFIER.format(
                    prefix=settings.INTERNET_ARCHIVE_DAILY_IDENTIFIER_PREFIX,
                    date_string=date_string
                )
                try:
                    item = InternetArchiveItem.objects.get(identifier=identifier)
                    if item.complete:
                        # if this day is already complete, skip it, and move on to the
                        # next day in the range
                        continue
                    in_flight_for_this_day = item.tasks_in_progress
                except InternetArchiveItem.DoesNotExist:
                    in_flight_for_this_day = 0
                bucket_limit = min(daily_limit, to_queue - total_queued) - in_flight_for_this_day
                if bucket_limit > 0:
                    count_queued = queue_internet_archive_uploads_for_date(date_string, bucket_limit)
                    if count_queued:
                        total_queued += count_queued
                        queued.append(f"{date_string} ({count_queued})")
            else:
                break

        if total_queued:
            logger.info(f"Prepared to upload {total_queued} links to internet archive across {len(queued)} days: {', '.join(queued)}.")
        else:
            logger.info("Prepared to upload 0 links to internet archive: no pending links in range.")

    else:
        logger.info("Skipped the queuing of file upload tasks: max tasks already in progress.")


# WACZ CONVERSION

def seconds_to_minutes(seconds_val):
    """
    Converts seconds to minutes
    """
    if seconds_val >= 60:
        return f"{round(seconds_val / 60, 1)} minutes"
    else:
        return f"{math.ceil(seconds_val)} seconds"


@shared_task
@tempdir.run_in_tempdir()
def convert_warc_to_wacz(input_guid, benchmark_log):
    """
    Downloads WARC file to temp dir
    Converts WARC file to WACZ
    Logs conversion metrics
    If successful, saves file in storage
    """
    start_time = time.time()
    link = Link.objects.get(guid=input_guid)
    cwd = os.getcwd()
    warc_path = f"{link.guid}.warc.gz"
    wacz_path = f"{link.guid}.wacz"
    pages_path = "pages.jsonl"
    warc_not_found_error = False

    # save a local copy of the warc file
    warc_save_start_time = time.time()
    try:
        with open(warc_path, "wb") as file:
            copy_file_data(default_storage.open(link.warc_storage_file()), file)
    except FileNotFoundError:
        warc_not_found_error = True
    warc_save_duration = time.time() - warc_save_start_time

    # prepare our custom pages.jsonl file
    jsonl_prep_start_time = time.time()
    jsonl_rows = [
        {"format": "json-pages-1.0", "id": "pages", "title": "All Pages"}
    ]
    ts = str(link.creation_timestamp)
    if link.primary_capture:
        jsonl_rows.append(
            {"title": "primary capture url", "url": link.primary_capture.url, "ts": ts}
        )
    if link.screenshot_capture:
        jsonl_rows.append(
            {"title": "screenshot url", "url": link.screenshot_capture.url, "ts": ts}
        )
    if link.provenance_summary_capture:
        jsonl_rows.append(
            {"title": "provenance summary url", "url": link.provenance_summary_capture.url, "ts": ts}
        )
    assert len(jsonl_rows) > 1, f"{link.guid} has neither a primary nor a screenshot capture!"
    with open(pages_path, 'w') as file:
        for item in jsonl_rows:
            file.write(json.dumps(item) + '\n')
    jsonl_write_duration = time.time() - jsonl_prep_start_time

    # call js-wacz in a subprocess
    conversion_start_time = time.time()
    conversion_error = False
    error_output = ''
    subprocess_arguments = [
        "npx",
        "js-wacz",
        "create",
        "-f", os.path.join(cwd, warc_path),
        "-o", os.path.join(cwd, wacz_path),
        "-p", cwd  # js-wacz takes the directory in which to find page.jsonl; not the path to the file itself
    ]
    try:
        # set cwd to settings.JS_WACZ_DIR so subprocess can find js-wacz
        subprocess.run(subprocess_arguments, capture_output=True, check=True, text=True, cwd=settings.JS_WACZ_DIR)
    except subprocess.CalledProcessError as e:
        conversion_error = True
        error_output = e.stderr
        logger.error(f"{link.guid}: js-wacz returned {e.returncode} with error {error_output}")
    conversion_duration = time.time() - conversion_start_time

    warc_size = link.warc_size
    formatted_warc_size = filesizeformat(warc_size)
    try:
        wacz_size = os.path.getsize(wacz_path)
    except OSError:
        wacz_size = 0

    formatted_wacz_size = filesizeformat(wacz_size)
    raw_total_duration = time.time() - start_time
    duration = seconds_to_minutes(raw_total_duration)

    with open(benchmark_log, 'a') as log_file:
        row = {
            "file_name": input_guid,
            "conversion_status": '',
            "warc_size": formatted_warc_size,
            "raw_warc_size": warc_size,  # bytes
            "wacz_size": formatted_wacz_size,
            "raw_wacz_size": wacz_size,  # bytes
            "duration": duration,
            "raw_duration": raw_total_duration,  # seconds
            "raw_warc_save_duration": warc_save_duration,
            "raw_jsonl_write_duration": jsonl_write_duration,
            "raw_conversion_duration": conversion_duration,
            "error": ''
        }
        writer = csv.DictWriter(log_file, fieldnames=row.keys())

        if conversion_error:
            row["conversion_status"] = "Failure"
            row["error"] = error_output
            writer.writerow(row)
        elif warc_not_found_error:
            row["conversion_status"] = "Failure"
            row["error"] = "WARC is not found in storage"
            writer.writerow(row)
        elif wacz_size == 0 or warc_size > wacz_size:
            row["conversion_status"] = "Failure"
            row["error"] = "WACZ is smaller than WARC"
            writer.writerow(row)
        else:
            row["conversion_status"] = "Success"
            writer.writerow(row)

            with open(wacz_path, 'rb') as wacz_file:
                default_storage.save(link.wacz_storage_file(), wacz_file)
