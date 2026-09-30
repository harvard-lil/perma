"""Find, and with --apply delete, files IA derived from WARCs Perma deleted.

    manage.py remove_ia_derivative_leftovers [--apply] [--after-item ID]
                                             [--limit-items N] [--pause SECONDS]

Until deletions passed cascade_delete=True, deleting a link's WARC from a daily
IA item left the files IA had derived from it, such as <guid>.warc.os.cdx.gz,
which lists the capture's URLs. For each daily item with InternetArchiveFiles
marked 'confirmed_absent', this reads the item's metadata once and finds the
files named after those links' WARCs (<guid>.warc…) that are still there.

Without --apply it only reads, and logs what it would delete. With --apply it
deletes those files one request at a time, pausing --pause seconds after each,
and waits while IA reports itself near its task limits. Items are processed in
identifier order and each is logged when done, so a run can be resumed with
--after-item.
"""

import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from perma.celery_tasks import ia_files_for_link
from perma.models import InternetArchiveFile
from perma.utils import (
    get_ia_session,
    ia_global_task_limit_approaching,
    ia_perma_task_limit_approaching,
)

# daily items Perma cannot edit (see conditionally_queue_internet_archive_uploads_for_date_range)
UNEDITABLE_ITEMS = [
    'daily_perma_cc_2022-07-19',
    'daily_perma_cc_2022-07-20',
    'daily_perma_cc_2022-07-21',
    'daily_perma_cc_2022-07-25',
]
LOAD_WAIT_SECONDS = 60
LOAD_WAITS = 30


class Command(BaseCommand):
    help = "Find (and with --apply delete) IA files derived from WARCs Perma deleted from daily items."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Delete the files found. Without it, only report them.")
        parser.add_argument("--after-item", default="", help="Resume after this item identifier.")
        parser.add_argument("--limit-items", type=int, default=None, help="Stop after this many items.")
        parser.add_argument("--pause", type=float, default=5.0, help="Seconds to wait after each deletion.")

    def handle(self, *args, apply, after_item, limit_items, pause, **options):
        items = InternetArchiveFile.objects.filter(
            status='confirmed_absent',
            item__span__isempty=False,
            item_id__gt=after_item,
        ).exclude(
            item_id__in=UNEDITABLE_ITEMS
        ).order_by('item_id').values_list('item_id', flat=True).distinct()
        if limit_items:
            items = items[:limit_items]

        ia_session = get_ia_session()
        found = deleted = 0
        for identifier in items:
            guids = InternetArchiveFile.objects.filter(
                item_id=identifier, status='confirmed_absent'
            ).values_list('link_id', flat=True)
            ia_item = ia_session.get_item(identifier)
            ia_files = ia_item.item_metadata.get('files', [])
            leftovers = [name for guid in guids for name in ia_files_for_link(ia_files, guid)]
            for name in leftovers:
                found += 1
                if not apply:
                    self.stdout.write(f"Would delete {name} from {identifier}.")
                    continue
                self.wait_for_ia(ia_session, identifier)
                response = ia_item.get_file(name).delete(
                    cascade_delete=False,
                    access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY,
                    secret_key=settings.INTERNET_ARCHIVE_SECRET_KEY,
                    verbose=False,
                    debug=False,
                    retries=0,
                )
                if response.status_code != 204:
                    raise CommandError(f"IA answered {response.status_code} deleting {name} from {identifier}: {response.text}. Resume with --after-item on the item before it.")
                deleted += 1
                self.stdout.write(f"Deleted {name} from {identifier}.")
                time.sleep(pause)
            self.stdout.write(f"Done with {identifier}: {len(leftovers)} leftover file(s). Resume with --after-item {identifier}.")

        verb = "deleted" if apply else "found (dry run; pass --apply to delete)"
        self.stdout.write(f"{deleted if apply else found} leftover file(s) {verb}.")

    def wait_for_ia(self, ia_session, identifier):
        for _ in range(LOAD_WAITS):
            overloaded, details = ia_session.get_s3_load_info(identifier=identifier, access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY)
            if not (overloaded or ia_perma_task_limit_approaching(details) or ia_global_task_limit_approaching(details)):
                return
            self.stdout.write(f"IA is near its task limits; waiting {LOAD_WAIT_SECONDS} s.")
            time.sleep(LOAD_WAIT_SECONDS)
        raise CommandError(f"IA stayed near its task limits; stopped before {identifier}. Resume with --after-item on the item before it.")
