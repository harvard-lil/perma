from io import StringIO
import json
import math
import os
import subprocess
import time
from zipfile import ZipFile

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from django.conf import settings
from django.core.files.storage import storages
from django.template.defaultfilters import filesizeformat

from perma.models import Folder, Link
from perma.utils import copy_file_data, calculate_s3_etag, temporary_working_directory

import logging
logger = logging.getLogger('celery.django')


@shared_task(name='perma.celery_tasks.cache_playback_status_for_new_links', acks_late=True)  # use acks_late for tasks that can be safely re-run if they fail
def cache_playback_status_for_new_links():
    links = Link.objects.permanent().filter(cached_can_play_back__isnull=True)
    queued = 0
    for link_guid in links.values_list('guid', flat=True).iterator():
        cache_playback_status.delay(link_guid)
        queued = queued + 1
    logger.info(f"Queued {queued} links to have their playback status cached.")


@shared_task(name='perma.celery_tasks.cache_playback_status', acks_late=True)  # use acks_late for tasks that can be safely re-run if they fail
def cache_playback_status(link_guid):
    link = Link.objects.get(guid=link_guid)
    link.cached_can_play_back = link.can_play_back()
    if link.tracker.has_changed('cached_can_play_back'):
        link.save(update_fields=['cached_can_play_back'])


@shared_task(name='perma.celery_tasks.fix_cached_folder_paths', acks_late=True)
def fix_cached_folder_paths(folder_ids=None):
    if folder_ids:
        folders = Folder.objects.filter(id__in=folder_ids)
    else:
        folders = Folder.objects.all()
    folders = folders.values_list('id', flat=True)

    queued_ids = set()
    try:
        for folder_id in folders:
            fix_cached_folder_path.delay(folder_id)
            queued_ids.add(folder_id)
    except SoftTimeLimitExceeded:
        not_queued_yet = set(folders) - queued_ids
        logger.info(f"SoftTimeLimitExceeded: {len(not_queued_yet)} folders remaining.")
        fix_cached_folder_paths.delay(list(not_queued_yet))

    logger.info(f"Queued {len(queued_ids)} folders to have their cached path fixed.")


@shared_task(name='perma.celery_tasks.fix_cached_folder_path', acks_late=True)  # use acks_late for tasks that can be safely re-run if they fail
def fix_cached_folder_path(folder_id):
    folder = Folder.objects.get(id=folder_id)
    try:
        folder.cached_path = folder.get_path()
        if folder.tracker.has_changed('cached_path'):
            folder.save(update_fields=['cached_path'])
    except Folder.DoesNotExist:
        # This exception will be thrown if a folder's cached tree_root_id is wrong.
        folder = Folder.objects.with_tree_fields().get(id=folder_id)
        folder.tree_root_id = folder.tree_path[0]
        folder.cached_path = Folder.format_tree_path(folder.tree_path)
        folder.save(update_fields=['cached_path', 'tree_root_id'])


@shared_task(name='perma.celery_tasks.populate_warc_size_fields', acks_late=True)
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


@shared_task(name='perma.celery_tasks.populate_warc_size', acks_late=True)
def populate_warc_size(link_guid):
    """
    One-time task, to populate the warc_size field for links where we missed it, the first time around.
    See https://github.com/harvard-lil/perma/issues/2617 and https://github.com/harvard-lil/perma/issues/2172;
    old links also often lack this metadata.
    """
    link = Link.objects.get(guid=link_guid)
    link.warc_size = storages[settings.WARC_STORAGE].size(link.warc_storage_file())
    link.save(update_fields=['warc_size'])



@shared_task(name='perma.celery_tasks.populate_wacz_size', acks_late=True)
def populate_wacz_size(link_guid):
    """
    One-time task, to populate the wacz_size field for links converted before that field was added.
    """
    link = Link.objects.get(guid=link_guid)
    link.wacz_size = storages[settings.WACZ_STORAGE].size(link.wacz_storage_file())
    link.save(update_fields=['wacz_size'])


@shared_task(name='perma.celery_tasks.convert_warc_to_wacz')
@temporary_working_directory()
def convert_warc_to_wacz(input_guid, save_wacz_on_error=False, warn_on_error=False):
    """
    Downloads WARC file to temp dir
    Converts WARC file to WACZ
    Logs conversion metrics
    If successful, saves file in storage
    """

    #
    # Helper methods
    #

    def seconds_to_minutes(seconds_val):
        """
        Converts seconds to minutes
        """
        if seconds_val >= 60:
            return f"{round(seconds_val / 60, 1)} minutes"
        else:
            return f"{math.ceil(seconds_val)} seconds"

    def format_filesize(i):
        return filesizeformat(i).replace("\xa0", " ")

    #
    # Launch the conversions
    #

    start_time = time.time()
    link = Link.objects.get(guid=input_guid)
    cwd = os.getcwd()
    warc_path = f"{link.guid}.warc.gz"
    wacz_path = f"{link.guid}.wacz"
    pages_path = "pages.jsonl"

    # confirm this Link has a warc that should be converted
    if not link.can_play_back():
        logger.error(f"{link.guid} is ineligible for conversion.")
        return

    # save a local copy of the warc file
    warc_save_start_time = time.time()
    with open(warc_path, "wb") as file:
        copy_file_data(storages[settings.WARC_STORAGE].open(link.warc_storage_file()), file)
    warc_save_duration = time.time() - warc_save_start_time

    # prepare our custom pages.jsonl file
    pages_prep_start_time = time.time()
    with open(pages_path, 'w') as file:
        file.write(link.get_pages_jsonl() + '\n')
    pages_write_duration = time.time() - pages_prep_start_time

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

    try:
        wacz_size = os.path.getsize(wacz_path)
    except OSError:
        wacz_size = 0

    hash_check_start_time = time.time()
    if wacz_size:

        # retrieve S3's md5-hash-like "etag" of file it has
        remote_hash = storages[settings.WARC_STORAGE].connection.Object(
            bucket_name=storages[settings.WARC_STORAGE].bucket_name,
            key=os.path.join(settings.MEDIA_ROOT, link.warc_storage_file())
        ).e_tag.strip('"')

        # set a block size for hashing the warc inside the wacz
        #
        # this can be anything, for warcs uploaded to S3 in one piece.
        #
        # for warcs saved using S3's "multipart" upload, behind the scenes,
        # this must match the block size used during upload
        # https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html
        #
        # we don't know what block size was used, so we are guessing:
        # locally with minio, it's 16 MB;
        # S3 docs say the management console uses 16 MB: https://docs.aws.amazon.com/AmazonS3/latest/API/API_Object.html
        # boto3 docs and source state the default is 8 MB: https://boto3.amazonaws.com/v1/documentation/api/latest/_modules/boto3/s3/transfer.html#TransferConfig
        # stackoverflow suggests 16 MB is common
        #
        # let's see if this covers the reality of our collection,
        # and if it doesn't, come up with a better strategy
        MB = 2 ** 20
        blocksize = 16 * MB
        multipart_format = '-' in remote_hash
        if multipart_format:
            parts = int(remote_hash.split('-')[-1])
            if 8 * MB * parts >= warc_size:
                blocksize = 8 * MB

        # calculate the etag for the warc inside the wacz
        with (
            ZipFile(wacz_path) as zip_file,
            zip_file.open(f"archive/{link.guid}.warc.gz") as embedded_warc
        ):
            wacz_hash = calculate_s3_etag(embedded_warc, blocksize, multipart_format)

        # see if they match
        warc_checksums_match =  wacz_hash == remote_hash

    else:
        warc_checksums_match = None
    hash_check_duration = time.time() - hash_check_start_time

    total_duration = time.time() - start_time

    data = {
        "guid": input_guid,
        "conversion_status": '',
        "warc_size": warc_size,
        "warc_size_formatted": format_filesize(warc_size),
        "wacz_size": wacz_size,
        "wacz_size_formatted": format_filesize(wacz_size),
        "warc_checksums_match": warc_checksums_match,
        "total_duration_formatted": seconds_to_minutes(total_duration),
        "total_duration": total_duration,
        "warc_save_duration": warc_save_duration,
        "pages_write_duration": pages_write_duration,
        "conversion_duration": conversion_duration,
        "hash_check_duration": hash_check_duration,
        "error": '',
    }
    if conversion_error:
        # No WACZ to save; error message from js-wacz
        data["conversion_status"] = "Failure"
        data["error"] = error_output
    elif wacz_size == 0:
        # No WACZ to save; no error message from js-wacz
        data["conversion_status"] = "Failure"
        data["error"] = "No WACZ produced"
    else:
        # A WACZ to save: optionally keep broken ones around for study
        if warc_size > wacz_size:
            data["conversion_status"] = "Failure"
            data["error"] = "WACZ is smaller than WARC"
        elif not warc_checksums_match:
            data["conversion_status"] = "Failure"
            data["error"] = f"The WARC embedded in the WACZ differs from the source WARC. Remote hash: {remote_hash}. WACZ hash: {wacz_hash}"
        else:
            data["conversion_status"] = "Success"

        if data["conversion_status"] == "Success" or save_wacz_on_error:
            link.wacz_size = wacz_size
            link.save(update_fields=['wacz_size'])
            with open(wacz_path, 'rb') as wacz_file:
                storages[settings.WACZ_STORAGE].save(link.wacz_storage_file(), wacz_file)

    storages[settings.WACZ_STORAGE].save(link.warc_to_wacz_conversion_log_file(), StringIO(json.dumps(data)))
    if data["error"] and warn_on_error:
        logger.warning(data["error"])
