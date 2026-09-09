import itertools
import json
import logging
import os
import random
import re
import time
import zipfile
from contextlib import contextmanager
from urllib.parse import urlparse

import requests
import surt
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex, OpClass
from django.core.files.storage import storages
from django.db import models, transaction
from django.db.models import F, JSONField, Max, Q, QuerySet
from django.db.models.functions import Now, TruncDate, Upper
from django.utils import timezone
from django.utils.functional import cached_property
from model_utils import FieldTracker
from rest_framework.settings import api_settings
from taggit.managers import TaggableManager

from perma.utils import preserve_perma_wacz

from .folder import Folder
from .internet_archive import LAST_INDIVIDUAL_LINK_IA_UPLOAD_DATE
from .organization import Organization
from .user import LinkUser
from .utils import DeletableManager, DeletableModel, GenericStringTaggedItem

logger = logging.getLogger(__name__)


class LinkQuerySet(QuerySet):

    def user_access_filter(self, user):
        """
            User can see/modify a link if they created it or it is in an org folder they belong to.
            Staff can see/modify all links.
        """
        if user.is_staff:
            return Q()  # all

        # personal links
        folder_list = list(Folder.objects.filter(owned_by=user).values_list('id', flat=True))

        # links owned by orgs in which the user a member
        orgs = user.get_orgs()
        if orgs:
            folder_list.extend(Folder.objects.filter(organization__in=list(orgs)).values_list('id', flat=True))

        return Q(folders__id__in=folder_list)

    def accessible_to(self, user):
        return self.filter(self.user_access_filter(user))

    def discoverable(self):
        return self.filter(Link.DISCOVERABLE_FILTER)

    def successful(self):
        """ Limit queryset to those where any non-favicon capture succeeded"""
        return self.filter(
            captures__in=Capture.objects.filter(Capture.CAN_PLAY_BACK_FILTER)
        ).distinct()

    def permanent(self):
        """
            The required wait period has elapsed, and the user did not delete the Link.
            It is a permanent part of the collection.
        """
        return self.filter(
            archive_timestamp__lte=timezone.now(),
            user_deleted=False,
        )

    def visible_to_memento(self):
        return self.discoverable().filter(cached_can_play_back=True)

    def visible_to_ia(self):
        return self.visible_to_memento()

    def ineligible_for_ia(self):
        return self.exclude(Link.DISCOVERABLE_FILTER, cached_can_play_back=True)

    def ia_upload_required_from_privacy_toggle(self, limit=100):
        """
        Links marked upload_or_reupload_required after a privacy toggle.
        """
        query = self.filter(internet_archive_upload_status='upload_or_reupload_required')
        if limit is not None:
            query = query[:limit]
        return query

    def ia_deletion_required_from_privacy_toggle(self, limit=100):
        """
        Links marked deletion_required after a privacy toggle.
        """
        query = self.filter(internet_archive_upload_status='deletion_required')
        if limit is not None:
            query = query[:limit]
        return query

    def ia_upload_pending(self, date_string, limit=100):
        # Get all Links we think should have been uploaded to IA,
        # and then filter out the ones that have already been uploaded
        # to a "daily" item.
        if date_string > LAST_INDIVIDUAL_LINK_IA_UPLOAD_DATE:
            # No links created after this date were uploaded to IA as individual Items:
            # use a simplified query
            logger.debug("Running simple IA eligibility query.")
            query = Link.objects.filter(
                creation_timestamp__date=date_string
            ).visible_to_ia().filter(
                internet_archive_files=None
            )
        else:
            logger.debug("Running full IA eligibility query.")
            query = Link.objects.filter(
                creation_timestamp__date=date_string
            ).visible_to_ia().exclude(
                internet_archive_items__span__isempty=False
            )
        if limit is not None:
            query = query[:limit]
        return query


LinkManager = DeletableManager.from_queryset(LinkQuerySet)

class Link(DeletableModel):
    """
    This is the core of the Perma link.
    """
    guid = models.CharField(max_length=255, null=False, blank=False, primary_key=True, editable=False)
    GUID_CHARACTER_SET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    replacement_link = models.ForeignKey("Link", blank=True, null=True, help_text="New link to which readers should be forwarded when trying to view this link.", on_delete=models.CASCADE)

    submitted_url = models.URLField(max_length=2100, null=False, blank=False)
    submitted_url_surt = models.CharField(max_length=2100, null=True, blank=True)
    creation_timestamp = models.DateTimeField(default=timezone.now, editable=False)
    submitted_title = models.CharField(max_length=2100, null=False, blank=False)
    submitted_description = models.CharField(max_length=300, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='created_links', on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, null=True, blank=True, related_name='links', on_delete=models.CASCADE)
    folders = models.ManyToManyField(Folder, related_name='links', blank=True)
    notes = models.TextField(blank=True)
    default_to_screenshot_view = models.BooleanField(default=False, help_text="User defaults to screenshot view.")
    bonus_link = models.BooleanField(null=True, blank=True)

    captured_by_software = models.CharField(max_length=255, default='perma', db_index=True)
    captured_by_browser = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    warc_size = models.IntegerField(blank=True, null=True)
    wacz_size = models.IntegerField(blank=True, null=True)
    cached_can_play_back = models.BooleanField(
        null=True,
        default=None,
        db_index=True,
        help_text="After archive_timestamp, cache whether this link can be played back, for efficiency."
    )

    is_private = models.BooleanField(default=False)
    private_reason = models.CharField(max_length=10, blank=True, null=True, choices=(
        ('domain', 'At the request of the domain owner'),
        ('meta_perma','Perma-specific robots.txt or meta tag'),
        ('meta','Generic robots.txt or meta tag'),
        ('user','At user direction'),
        ('takedown','At request of content owner'),
        ('failure','Analysis of meta tags failed'),
        ('flagged','Contains flagged content')
    ))
    is_unlisted = models.BooleanField(default=False)

    archive_timestamp = models.DateTimeField(blank=True, null=True, help_text="Date after which this link is eligible to be copied by the mirror network.")
    internet_archive_upload_status = models.CharField(max_length=28,
                                                      choices=(('deletion_required', 'deletion_required'), ('upload_or_reupload_required', 'upload_or_reupload_required')),
                                                      db_index=True,
                                                      null=True)

    internet_archive_items = models.ManyToManyField(
        "InternetArchiveItem", through="InternetArchiveFile", related_name="links"
    )

    objects = LinkManager()
    tracker = FieldTracker()
    tags = TaggableManager(through=GenericStringTaggedItem, blank=True)


    class Meta:
        indexes = [
            models.Index(fields=['user_deleted', 'is_private', 'is_unlisted', 'cached_can_play_back', 'internet_archive_upload_status']),
            models.Index('user_deleted', TruncDate('creation_timestamp'), 'is_private', 'is_unlisted', 'cached_can_play_back', name="ia_eligible_for_date_idx"),
            models.Index(fields=['creation_timestamp', 'guid']),
            models.Index(fields=['-creation_timestamp', 'guid']),
            models.Index(fields=['submitted_url_surt']),
            GinIndex(OpClass(Upper('guid'), name='gin_trgm_ops'), name='guid_case_insensitive_idx'),
        ]

    DISCOVERABLE_FILTER = Q(is_unlisted=False, is_private=False)
    def is_discoverable(self):
        return not self.is_private and not self.is_unlisted

    def is_permanent(self):
        return self.archive_timestamp < timezone.now() and not self.user_deleted

    def has_successful_capture(self):
        return self.captures.filter(Capture.CAN_PLAY_BACK_FILTER).exists()

    def is_visible_to_memento(self):
        return self.cached_can_play_back and self.is_discoverable()

    def can_upload_to_internet_archive(self):
        return self.is_visible_to_memento()

    @cached_property
    def ia_identifier(self):
        return settings.INTERNET_ARCHIVE_IDENTIFIER_PREFIX + self.guid

    @classmethod
    def get_ascii_safe_url(cls, submitted_url):
        """URL as encoded internally by python requests"""
        try:
            # Attempt to quote the URL as well as possible:
            # - percent encoding
            # - unicode domains to punycode
            # - etc.
            return requests.Request('GET', submitted_url).prepare().url
        except requests.exceptions.RequestException:
            # If that fails, just percent encode everything for safety
            return requests.utils.requote_uri(submitted_url)

    @cached_property
    def ascii_safe_url(self):
        """URL as encoded internally by python requests"""
        return self.get_ascii_safe_url(self.submitted_url)

    @cached_property
    def url_details(self):
        return urlparse(self.ascii_safe_url)

    def get_default_title(self):
        return self.url_details.netloc

    def save(self, *args, **kwargs):
        # Set a default title if one is missing
        if not self.submitted_title:
            self.submitted_title = self.get_default_title()

        initial_folder = kwargs.pop('initial_folder', None)

        if not self.pk:
            if not self.archive_timestamp:
                self.archive_timestamp = self.creation_timestamp + settings.ARCHIVE_DELAY
            if not kwargs.pop("pregenerated_guid", False):
                # not self.pk => not created yet
                # only try 100 attempts at finding an unused GUID
                # (100 attempts should never be necessary, since we'll expand the keyspace long before
                # there are frequent collisions)
                r = random.SystemRandom()
                for i in range(100):
                    # Generate an 8-character random string like "1A2B3C4D"
                    guid = ''.join(r.choice(self.GUID_CHARACTER_SET) for _ in range(8))

                    # apply standard formatting (hyphens)
                    guid = Link.get_canonical_guid(guid)

                    # Avoid GUIDs starting with four letters (in case we need those later)
                    match = re.search(r'^[A-Z]{4}', guid)

                    if not match and not Link.objects.filter(guid=guid).exists():
                        break
                else:
                    raise Exception("No valid GUID found in 100 attempts.")
                self.guid = guid

        if not self.submitted_url_surt:
            self.submitted_url_surt = surt.surt(self.submitted_url)

        if self.is_private and not self.private_reason:
            self.private_reason = 'user'

        super(Link, self).save(*args, **kwargs)

        if not self.folders.count():
            if not initial_folder:
                if self.created_by and self.created_by.root_folder:
                    initial_folder = self.created_by.root_folder
            if initial_folder:
                self.folders.add(initial_folder)

    def __str__(self):
        return self.guid

    @classmethod
    def get_canonical_guid(self, guid):
        """
        Given a GUID, return the canonical version, with hyphens every 4 chars and all caps.
        So "a2b3c4d5" becomes "A2B3-C4D5".
        """
        # handle legacy 9/10/11-char GUIDs
        if '-' not in guid and len(guid) >= 9:
            # handle common typo because legacy URLs start with zero
            if guid[0] == 'O':
                guid = guid.replace('O', '0', 1)
            return guid

        # uppercase and remove non-alphanumerics
        canonical_guid = re.sub('[^0-9A-Z]+', '', guid.upper())

        # split guid into 4-char chunks, starting from the end
        guid_parts = [canonical_guid[max(i - 4, 0):i] for i in
                      range(len(canonical_guid), 0, -4)]

        # stick together parts with '-'
        return "-".join(reversed(guid_parts))

    def move_to_folder_for_user(self, folder, user):
        """
            Move this link to the given folder for the given user.
        """
        with transaction.atomic():
            # Don't let anybody move folders around, until this link is
            # safely inside its destination folder, lest denormalized
            # ownership-related fields get out of sync
            for folder in itertools.chain(self.folders.all(), [folder]):
                Folder.objects.select_for_update().get(pk=folder.tree_root_id)

            # remove this link from any folders it's in for this user
            self.folders.remove(*self.folders.accessible_to(user))
            # add it back to the given folder
            self.folders.add(folder)
            if not folder.organization:
                self.organization = None
            else:
                self.organization = folder.organization
            if self.bonus_link and (folder.organization or folder.sponsored_by):
                self.bonus_link = False
                user.bonus_links = F('bonus_links') + 1

            self.save(update_fields=['organization', 'bonus_link'])
            user.save(update_fields=['bonus_links'])

    def guid_as_path(self):
        # For a GUID like ABCD-1234, return a path like AB/CD/12.
        stripped_guid = re.sub('[^0-9A-Za-z]+', '', self.guid)
        guid_parts = [stripped_guid[i:i + 2] for i in range(0, len(stripped_guid), 2)]
        return '/'.join(guid_parts[:-1])

    def warc_storage_file(self):
        return os.path.join(settings.WARC_STORAGE_DIR, self.guid_as_path(), f'{self.guid}.warc.gz')

    def wacz_storage_file(self):
        return os.path.join(settings.WACZ_STORAGE_DIR, self.guid_as_path(), f'{self.guid}.wacz')

    def warc_to_wacz_conversion_log_file(self):
        return os.path.join(settings.WACZ_STORAGE_DIR, self.guid_as_path(), f'{self.guid}-conversion-log.json')

    def warc_presigned_url(self):
        # Specify that warcs should have content-type 'application/gzip' so that archives are fetched correctly by the playback service worker.
        # (All warcs from before summer 2022 were uploaded with content-type 'application/octet-stream' and content-encoding 'gzip')
        return storages[settings.WARC_STORAGE].url(self.warc_storage_file(), expire=settings.WARC_PRESIGNED_URL_EXPIRES, parameters={
                'ResponseContentType': 'application/x-gzip',
                'ResponseContentEncoding': ''
        })

    def wacz_presigned_url(self):
        return storages[settings.WACZ_STORAGE].url(self.wacz_storage_file(), expire=settings.WACZ_PRESIGNED_URL_EXPIRES, parameters={
            'ResponseContentType': 'application/wacz',
            'ResponseContentEncoding': ''
        })

    def warc_presigned_url_relative(self):
        parsed = urlparse(self.warc_presigned_url())
        return f'{parsed.path}?{parsed.query}'.lstrip('/')

    def wacz_presigned_url_relative(self):
        parsed = urlparse(self.wacz_presigned_url())
        return f'{parsed.path}?{parsed.query}'.lstrip('/')

    def has_wacz_version(self):
        return bool(self.wacz_size)

    def delete_related_captures(self):
        Capture.objects.filter(link_id=self.pk).delete()

    def has_capture_job(self):
        try:
            self.capture_job
        except CaptureJob.DoesNotExist:
            return False
        return True

    def mark_capturejob_superseded(self):
        try:
            job = self.capture_job
            job.superseded = True
            job.save()
        except CaptureJob.DoesNotExist:
            pass

    @cached_property
    def is_user_uploaded(self):
        return self.primary_capture.user_upload

    @cached_property
    def screenshot_capture(self):
        return self.captures.filter(role='screenshot').first()

    @cached_property
    def primary_capture(self):
        return self.captures.filter(role='primary').first()

    @cached_property
    def favicon_capture(self):
        return self.captures.filter(role='favicon').first()

    @cached_property
    def provenance_summary_capture(self):
        return self.captures.filter(role='provenance_summary').first()

    @cached_property
    def pdf_snapshot_capture(self):
        return self.captures.filter(role='pdf_snapshot').first()

    @cached_property
    def dom_snapshot_capture(self):
        return self.captures.filter(role='dom_snapshot').first()

    @cached_property
    def video_summary_capture(self):
        return self.captures.filter(role='video_summary').first()

    def get_pages_jsonl(self):
        if self.can_play_back():
            jsonl_rows = [
                {"format": "json-pages-1.0", "id": "pages", "title": "All Pages"}
            ]
            ts = str(self.creation_timestamp)
            if self.provenance_summary_capture:
                jsonl_rows.append(
                    {"url": self.provenance_summary_capture.url, "title": "Provenance Summary", "ts": ts}
                )
            if self.primary_capture:
                jsonl_rows.append(
                    {"url": self.primary_capture.url, "title": f"High-Fidelity Web Capture of {self.ascii_safe_url}", "ts": ts}
                )
            if self.screenshot_capture:
                jsonl_rows.append(
                    {"url": self.screenshot_capture.url, "title": f"Capture Time Screenshot of {self.ascii_safe_url}", "ts": ts}
                )
            if self.dom_snapshot_capture:
                jsonl_rows.append(
                    {"url": self.dom_snapshot_capture.url, "title": f"Capture Time DOM snapshot of {self.ascii_safe_url}", "ts": ts}
                )
            if self.pdf_snapshot_capture:
                jsonl_rows.append(
                    {"url": self.pdf_snapshot_capture.url, "title": f"Capture Time PDF snapshot of {self.ascii_safe_url}", "ts": ts}
                )
            if self.video_summary_capture:
                jsonl_rows.append(
                    {"url": self.video_summary_capture.url, "title": f"Extracted Video data from: {self.ascii_safe_url}", "ts": ts}
                )
            return "\n".join([json.dumps(row) for row in jsonl_rows])

    def write_uploaded_file(self, uploaded_file):
        """
            Given a file uploaded by a user, create a Capture record and WACZ.
        """
        from api.utils import get_mime_type, mime_type_lookup  # local import to avoid circular import

        # normalize file name to upload.jpg, upload.png, upload.gif, or upload.pdf
        mime_type = get_mime_type(uploaded_file.name)
        file_name = f'upload.{mime_type_lookup[mime_type]["new_extension"]}'
        warc_url = f"file:///{self.guid}/{file_name}"

        upload_capture = Capture(
            link=self,
            role='primary',
            status='success',
            record_type='resource',
            user_upload=True,
            content_type=mime_type,
            url=warc_url
        )

        provenance_capture = Capture(
            link=self,
            role='provenance_summary',
            status='success',
            record_type='resource',
            user_upload=False,
            content_type='text/html',
            url='file:///provenance-summary.html'
        )

        # make the WACZ
        self.wacz_size = preserve_perma_wacz(
            uploaded_file,
            warc_url,
            mime_type,
            self.guid,
            self.submitted_url,
            self.submitted_title,
            self.creation_timestamp,
            self.wacz_storage_file()
        )
        self.warc_size = 0  # necessary?

        self.captured_by_software = 'upload'
        self.captured_by_browser = None
        self.save(update_fields=['captured_by_software', 'captured_by_browser', 'warc_size', 'wacz_size'])
        upload_capture.save()
        provenance_capture.save()

    def safe_delete_warc(self):
        old_name = self.warc_storage_file()
        storage = storages[settings.WARC_STORAGE]
        if storage.exists(old_name):
            new_name = old_name.replace('.warc.gz', f'_replaced_{timezone.now().timestamp()}.warc.gz')
            with storage.open(old_name) as old_file:
                storage.store_file(old_file, new_name)
            storage.delete(old_name)

    def safe_delete_wacz(self):
        old_name = self.wacz_storage_file()
        storage = storages[settings.WACZ_STORAGE]
        if storage.exists(old_name):
            new_name = old_name.replace('.wacz', f'_replaced_{timezone.now().timestamp()}.wacz')
            with storage.open(old_name) as old_file:
                storage.store_file(old_file, new_name)
            storage.delete(old_name)
        self.wacz_size = 0
        self.save(update_fields=['wacz_size'])

    @contextmanager
    def get_warc(self, extract_from_wacz_if_present=True, force_from_wacz=False):
        if not self.warc_size and not extract_from_wacz_if_present:
            raise RuntimeError(f'No WARC present for {self.guid}')

        elif self.warc_size and not force_from_wacz:
            yield storages[settings.WARC_STORAGE].open(self.warc_storage_file(), 'rb')

        elif self.wacz_size:
            with storages[settings.WACZ_STORAGE].open(self.wacz_storage_file(), 'rb') as wacz_file:
                yield zipfile.Path(wacz_file, "archive/data.warc.gz").open('rb')

        else:
            raise RuntimeError(f'No archive present for {self.guid}')

    @contextmanager
    def get_wacz(self):
        if not self.wacz_size:
            raise RuntimeError(f'No WACZ present for {self.guid}')
        yield storages[settings.WACZ_STORAGE].open(self.wacz_storage_file(), 'rb')

    def accessible_to(self, user):
        return user.can_edit(self)

    def can_play_back(self):
        """
        Reports whether a Perma Link has been successfully captured (or uploaded)
        and is ready for playback.

        See also /perma/perma_web/static/js/helpers/link.helpers.js
        """
        if self.cached_can_play_back is not None:
            return self.cached_can_play_back

        if self.user_deleted:
            return False

        successful_metadata = self.has_successful_capture()

        # Early Perma Links and direct uploads do not have CaptureJobs;
        # if no CaptureJob, judge based on Capture statuses alone;
        # otherwise, inspect CaptureJob status
        job = None
        try:
            job = self.capture_job
        except CaptureJob.DoesNotExist:
            pass
        if job and not job.superseded and job.status != 'completed':
            successful_metadata = False

        # Trust our records (the metadata) more than has_warc
        return successful_metadata


class Capture(models.Model):
    link = models.ForeignKey(Link, null=False, related_name='captures', on_delete=models.CASCADE)
    role = models.CharField(max_length=18, choices=(
        ('primary','Primary'),
        ('screenshot','Screenshot'),
        ('favicon','Favicon'),
        ('provenance_summary', 'Provenance Summary'),
        ('pdf_snapshot', 'PDF Snapshot'),
        ('dom_snapshot', 'DOM Snapshot'),
        ('video_summary', 'Video Summary'),
    ))
    status = models.CharField(max_length=10, choices=(('pending','pending'),('failed','failed'),('success','success')))
    url = models.CharField(max_length=2100, blank=True, null=True)
    record_type = models.CharField(max_length=10, choices=(
        ('response','WARC Response record -- recorded from web'),
        ('resource','WARC Resource record -- file without web headers')))
    content_type = models.CharField(max_length=255, null=False, default='', help_text="HTTP Content-type header.")
    user_upload = models.BooleanField(default=False, help_text="True if the user uploaded this capture.")

    CAN_PLAY_BACK_FILTER = (Q(role="primary") & Q(status="success")) | (Q(role="screenshot") & Q(status="success"))

    def __str__(self):
        return f"{self.role} {self.status}"

    def mime_type(self):
        """
            Return normalized mime type from content_type.
            Stuff after semicolon is stripped, type is lowercased, and x- prefix is removed.
        """
        return self.content_type.split(";", 1)[0].lower().replace('/x-', '/')

    def use_sandbox(self):
        """
            Whether the iframe we use to display this capture should be sandboxed.
            Answer is yes, unless:
            a) we're playing back a PDF, which currently can't be sandboxed in Chrome
            b) the playback will be an on-demand download mediated by an interstitial,
               because some browsers (for instance, Safari) may block downloads from sandboxed iframes even when `allow-downloads` is present.
               See https://perma.cc/M36S-ZLVS for `allow-downloads` support on 6/22/22
        """
        return not self.mime_type().startswith("application/pdf") and not self.show_interstitial()

    INLINE_TYPES = {
        'image/jpeg', 
        'image/gif', 
        'image/png', 
        'image/tiff', 
        'text/html', 
        'text/plain', 
        'application/pdf',
        'application/xhtml', 
        'application/xhtml+xml', 
        'video/mp4', 
        'video/webm', 
        'video/ogg', 
        'application/ogg',
        'audio/ogg',
        'audio/mpeg',
        'audio/x-wav',
        'audio/wav'
    }

    def show_interstitial(self):
        """
            Whether we should show an interstitial view/download button instead of showing the content directly.
            True unless we recognize the mime type as something that should be shown inline (PDF/HTML/image/audio/video).
        """
        return self.mime_type() not in self.INLINE_TYPES


def get_default_archive_formats():
    return ['warc']

class CaptureJob(models.Model):
    """
        This class tracks capture jobs for purposes of:
            (1) sorting the capture queue fairly and
            (2) reporting status during a capture.
    """
    creation_timestamp = models.DateTimeField(auto_now=True, blank=True, null=True, db_index=True)
    link = models.OneToOneField(Link, related_name='capture_job', null=True, blank=True, on_delete=models.CASCADE)
    status = models.CharField(max_length=15,
                              default='invalid',
                              choices=(('pending','pending'),('in_progress','in_progress'),('completed','completed'),('deleted','deleted'),('failed','failed'),('invalid', 'invalid')),
                              db_index=True)
    message = models.TextField(null=True, blank=True) #if we move to postgres, can be a json field
    human = models.BooleanField(default=False)
    order = models.FloatField(db_index=True)
    submitted_url = models.CharField(max_length=2100, blank=True, null=False)
    created_by = models.ForeignKey(LinkUser, blank=False, null=False, related_name='capture_jobs', on_delete=models.CASCADE)
    link_batch = models.ForeignKey('LinkBatch', blank=True, null=True, related_name='capture_jobs', on_delete=models.CASCADE)
    validation_status_code = models.IntegerField(blank=True, null=True)
    engine = models.CharField(max_length=255,
                              choices=(('perma', 'perma'), ('scoop-api', 'scoop-api')),
                              default='scoop-api',
                              db_index=True)

    archive_formats = ArrayField(
        models.CharField(
            max_length=15,
            choices=(('warc','warc'),('wacz','wacz'))
        ),
        default=get_default_archive_formats
    )

    # reporting
    attempt = models.SmallIntegerField(default=0)
    step_count = models.FloatField(default=0)
    step_description = models.CharField(max_length=255, blank=True, null=True)
    capture_start_time = models.DateTimeField(blank=True, null=True)
    capture_end_time = models.DateTimeField(blank=True, null=True)
    scoop_start_time = models.DateTimeField(blank=True, null=True)
    scoop_end_time = models.DateTimeField(blank=True, null=True)
    scoop_logs = JSONField(blank=True, null=True)
    scoop_job_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    scoop_state = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    superseded = models.BooleanField(default=False, help_text='A user upload has made this CaptureJob irrelevant to the playback of its related Link')

    # settings to allow our tests to draw out race conditions
    TEST_PAUSE_TIME = 0
    TEST_ALLOW_RACE = False

    def __str__(self):
        return f"CaptureJob {self.pk}: {self.link_id}"

    class Meta:
        indexes = [
            models.Index(fields=['capture_start_time']),
        ]

    def save(self, *args, **kwargs):

        # If this job does not have an order yet (just created),
        # examine all pending jobs to place this one in a fair position in the queue.
        # "Fair" means round robin: this job will be processed after every other job submitted by this user,
        # and then after every other user waiting in line has had at least one job done.
        if not self.order:

            # get all pending jobs, in reverse priority order
            pending_jobs = CaptureJob.objects.filter(status='pending', human=self.human).order_by('-order').select_related('link')
            # narrow down to just the jobs that come *after* the most recent job submitted by this user
            pending_jobs = list(itertools.takewhile(lambda x: x.created_by_id != self.created_by_id, pending_jobs))
            # flip the list of jobs back around to the order they'll be processed in
            pending_jobs = list(reversed(pending_jobs))

            # Go through pending jobs until we find two jobs submitted by the same user.
            # It's not fair for another user to run two jobs after all of ours are done,
            # so this new job should come right before that user's second job.
            next_jobs = {}
            last_job = None
            for pending_job in pending_jobs:
                pending_job_created_by_id = pending_job.link.created_by_id
                if pending_job_created_by_id in next_jobs:
                    # pending_job is the other user's second job, so this one goes in between that and last_job
                    self.order = last_job.order + (pending_job.order - last_job.order)/2
                    break
                next_jobs[pending_job_created_by_id] = pending_job
                last_job = pending_job

            # If order isn't set yet, that means we should go last. Find the highest current order and add 1.
            if not self.order:
                if pending_jobs:
                    self.order = pending_jobs[-1].order + 1
                else:
                    self.order = (CaptureJob.objects.aggregate(Max('order'))['order__max'] or 0) + 1

        super(CaptureJob, self).save(*args, **kwargs)

    @classmethod
    def get_next_job(cls, reserve=False):
        """
            Return the next job to work on, looking first at the human queue and then at the robot queue.

            If `reserve=True`, mark the returned job with `status=in_progress` and remove from queue so the
            same job can't be returned twice. Caller must make sure the job is actually processed once returned.
        """

        # cleanup: mark any captures as deleted where link has been deleted before capture
        CaptureJob.objects.filter(link__user_deleted=True, status='pending').update(status='deleted')

        while True:
            next_job = cls.objects.filter(status='pending').order_by('-human', 'order', 'pk').first()

            if reserve and next_job:
                if cls.TEST_PAUSE_TIME:
                    time.sleep(cls.TEST_PAUSE_TIME)

                # update the returned job to be in_progress instead of pending, so it won't be returned again
                # set time using database time, so timeout comparisons will be consistent across worker servers
                update_count = CaptureJob.objects.filter(
                    status='pending',
                    pk=next_job.pk
                ).update(
                    status='in_progress',
                    capture_start_time=Now()
                )

                # if no rows were updated, another worker claimed this job already -- try again
                if not update_count and not cls.TEST_ALLOW_RACE:
                    continue

                # load up-to-date time from database
                next_job.refresh_from_db()

            return next_job

    def queue_position(self):
        """
            Search job_queues to calculate the queue position for this job -- how many pending jobs have to be processed
            before this one?

            Returns 0 if job is not pending.
        """
        if self.status != 'pending':
            return 0

        queue_position = CaptureJob.objects.filter(status='pending', order__lte=self.order, human=self.human).count()
        if not self.human:
            queue_position += CaptureJob.objects.filter(status='pending', human=True).count()

        return queue_position

    def inc_progress(self, inc, description):
        self.step_count = int(self.step_count) + inc
        self.step_description = description
        self.save(update_fields=['step_count', 'step_description'])

    def mark_completed(self, status='completed'):
        """
            Record completion time and status for this job.
        """
        if status == 'completed' and self.link and self.link.captures.count() == 0:
            logger.error(f"To investigate: {self.link.guid} has no captures, but was being marked complete")
            status = 'failed'
        self.status = status
        self.capture_end_time = timezone.now()
        self.save(update_fields=['status', 'capture_end_time', 'message'])

    def mark_failed(self, message):
        """ Mark job as failed, and record message in format for front-end display. """
        self.message = json.dumps({api_settings.NON_FIELD_ERRORS_KEY: [message]})
        self.mark_completed('failed')

    def accessible_to(self, user):
        return self.link.accessible_to(user)


class LinkBatch(models.Model):
    created_by = models.ForeignKey(LinkUser, blank=False, null=False, related_name='link_batches', on_delete=models.CASCADE)
    started_on = models.DateTimeField(auto_now=True, blank=False, null=False, db_index=True)
    target_folder = models.ForeignKey(Folder, blank=False, null=False, on_delete=models.CASCADE)
    cached_capture_job_count = models.IntegerField(default=0, db_index=True)

    class Meta:
        verbose_name_plural = "link batches"

    def accessible_to(self, user):
        return user.is_staff or self.created_by_id == user.pk

    def __str__(self):
        return f"LinkBatch {self.pk}"
