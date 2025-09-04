#
# We ran a study, converting a subset of Perma's WARC files to WACZ.
#

import csv
from datetime import datetime
from invoke import task
import json
import time

from django.conf import settings
from django.core.files.storage import storages
from django.utils import timezone

from perma.celery_tasks import convert_warc_to_wacz, populate_wacz_size
from perma.models import Link


import logging
logger = logging.getLogger(__name__)

def get_conversion_queryset(source_csv, guid,
                            big_warcs, legacy_warcs, old_style_guids, user_uploads,
                            batch_guid_prefix, batch_range, batch_size):

    if source_csv and (
        guid or
        big_warcs or legacy_warcs or old_style_guids or user_uploads or
        batch_guid_prefix or batch_range or batch_size
    ):
        raise ValueError("If source CSV is specified, no other options may be configured.")

    if guid and (
        source_csv or
        big_warcs or legacy_warcs or old_style_guids or user_uploads or
        batch_guid_prefix or batch_range or batch_size
    ):
        raise ValueError("If GUID is specified, no other options may be configured.")

    if sum([big_warcs, legacy_warcs, old_style_guids, user_uploads]) > 1:
        raise ValueError("Only one of big_warcs, legacy_warcs, old_style_guids, or user_uploads may be specified.")

    if batch_range and batch_size:
        raise ValueError("Cannot specify both a batch range and a batch size.")

    links = Link.objects.filter(
        is_private=False,
        is_unlisted=False,
        cached_can_play_back=True
    ).values_list('guid', flat=True)

    #
    # Restrict to desired queryset
    #

    if source_csv:
        guids = []
        with open(source_csv, mode='r') as file:
            csv_file = csv.reader(file)
            for line in csv_file:
                guids.append(line[0])
        links = links.filter(guid__in=guids).order_by('guid')

    elif guid:
        links = links.filter(guid=guid)

    elif big_warcs:
        links = links.order_by('-warc_size')

    elif legacy_warcs:
        # Prior to 5/1/2014 we have a mix of wget, instapaper, and warcprox captures
        # https://github.com/harvard-lil/perma/blob/develop/errata.md
        links = links.filter(creation_timestamp__lt=datetime(2014,5,1, tzinfo=timezone.utc)).order_by('creation_timestamp')

    elif old_style_guids:
        # On 11/22/2013 we switched from 11-character IDs to ABCD-1234 IDs.
        # https://github.com/harvard-lil/perma/blob/develop/errata.md
        links = links.filter(creation_timestamp__lt=datetime(2013,11,22, tzinfo=timezone.utc)).order_by('creation_timestamp')

    elif batch_guid_prefix:
        links = links.filter(guid__startswith=batch_guid_prefix).order_by('guid')

    elif user_uploads:
        links = links.filter(captures__user_upload=True).order_by('guid')

    else:
        links = links.order_by('guid')

    #
    # Restrict to desired range or batch size
    #

    if batch_range:
        batch_range_start, batch_range_end = batch_range.split(':')
        batch_range_start = int(batch_range_start)
        batch_range_end = int(batch_range_end)

        if batch_range_start >= batch_range_end:
            raise ValueError("Starting index must be smaller than ending index.")

        links = links[batch_range_start:batch_range_end]

    elif batch_size:
        links = links[:int(batch_size)]

    return links


@task
def benchmark_wacz_conversion(ctx, source_csv=None, guid=None,
                              big_warcs=False, legacy_warcs=False, old_style_guids=False, user_uploads=False,
                              batch_guid_prefix=None, batch_range=None, batch_size=None,
                              log_to_file=None):
    """
    Invokes convert_warc_to_wacz() for a set of Perma Links.

    Specify "big_warcs" to restrict queryset to Links with large filesize.
    Specify "legacy_warcs" to restrict the queryset to Links that were originally produced with wget.
    Specify "old_style_guids" to restrict the queryset to Links with 11-character GUIDs.
    Specify "batch_guid_prefix" to restrict queryset to Links whose GUIDs begin with a string.
    Specify "batch_range" or "batch_size" to slice the queryset.
    Or, provide a file with the desired GUIDs, one per line.

    Specify "log_to_file" to write the list of enqueued GUIDs to a given path. Appends.
    """
    start = time.time()
    logger.info("Gathering benchmark conversion queryset.")
    guids = get_conversion_queryset(
        source_csv, guid,
        big_warcs, legacy_warcs, old_style_guids, user_uploads,
        batch_guid_prefix, batch_range, batch_size
    )

    logger.info("Start launching benchmark conversions.")
    queued = []
    for guid in guids.iterator():
        queued.append(guid)
        convert_warc_to_wacz.delay(guid, save_wacz_on_error=True)

    logger.info(f"Done launching benchmark conversions ({len(queued)} in {time.time() - start}s).")
    if log_to_file:
        with open(log_to_file, mode='a') as file:
            for guid in queued:
                file.write(f"{guid}\n")


@task
def collect_conversion_logs(ctx, log_to_file,
                            source_csv=None, guid=None,
                            big_warcs=False, legacy_warcs=False, old_style_guids=False, user_uploads=False,
                            batch_guid_prefix=None, batch_range=None, batch_size=None):
    """
    Gathers the logged results of convert_warc_to_wacz() for a set of Perma Links.
    Specify the desired file path and name in "log_to_file". Overwrites.

    Specify "big_warcs" to restrict queryset to Links with large filesize.
    Specify "legacy_warcs" to restrict the queryset to Links that were originally produced with wget.
    Specify "old_style_guids" to restrict the queryset to Links with 11-character GUIDs.
    Specify "batch_guid_prefix" to restrict queryset to Links whose GUIDs begin with a string.
    Specify "batch_range" or "batch_size" to slice the queryset.
    Or, provide a file with the desired GUIDs, one per line.
    """
    start = time.time()
    logger.info("Gathering benchmark conversion queryset.")
    guids = get_conversion_queryset(
        source_csv, guid,
        big_warcs, legacy_warcs, old_style_guids, user_uploads,
        batch_guid_prefix, batch_range, batch_size
    )

    logger.info("Start gathering benchmark conversion logs.")
    gathered = []
    with open(log_to_file, mode='w') as csv_file:
        fieldnames = [
            'guid',
            'conversion_status',
            'warc_size',
            'warc_size_formatted',
            'wacz_size',
            'wacz_size_formatted',
            'warc_checksums_match',
            'total_duration_formatted',
            'total_duration',
            'warc_save_duration',
            'pages_write_duration',
            'conversion_duration',
            'hash_check_duration',
            'error'
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for guid in guids.iterator():
            gathered.append(guid)
            try:
                with (
                    storages[settings.WACZ_STORAGE].open(Link.objects.get(guid=guid).warc_to_wacz_conversion_log_file())
                ) as file:
                    writer.writerow(json.loads(file.read()))
            except FileNotFoundError:
                writer.writerow({"guid": guid, "conversion_status": "Unknown"})

    logger.info(f"Done gathering benchmark conversion logs ({len(gathered)} in {time.time() - start}s).")


@task
def populate_benchmarked_wacz_sizes(ctx, source_csv):
    """
    One-time task, to populate the wacz_size field for links converted before that field was added.
    """
    guids = []
    with open(source_csv, mode='r') as file:
        csv_file = csv.reader(file)
        for line in csv_file:
            guids.append(line[0])
    links = Link.objects.filter(guid__in=guids).values_list('guid', flat=True)
    for link in links.iterator():
        populate_wacz_size.delay(link)
