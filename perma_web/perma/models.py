import hashlib
import io
import json
import os
import logging
import random
import re
import socket
import tempfile
import time
from contextlib import contextmanager
from urllib import urlencode
from urlparse import urlparse
import simple_history
import requests
from django.core.signing import TimestampSigner, BadSignature
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

from hanzo import warctools
from mptt.managers import TreeManager
from simple_history.models import HistoricalRecords
from werkzeug.urls import iri_to_uri

import django.contrib.auth.models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import models, transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.functional import cached_property
from mptt.models import MPTTModel, TreeForeignKey
from model_utils import FieldTracker
from pywb.cdx.cdxobject import CDXObject
from pywb.warc.cdxindexer import write_cdx_index
from taggit.managers import TaggableManager

from .utils import copy_file_data


logger = logging.getLogger(__name__)


### HELPERS ###

class DeletableManager(models.Manager):
    """
        Manager that excludes results where user_deleted=True by default.
    """
    def get_queryset(self):
        # exclude deleted entries by default
        return super(DeletableManager, self).get_queryset().filter(user_deleted=False)

    def all_with_deleted(self):
        return super(DeletableManager, self).get_queryset()


class DeletableModel(models.Model):
    """
        Abstract base class that lets a model track deletion.
    """
    user_deleted = models.BooleanField(default=False, verbose_name="Deleted by user")
    user_deleted_timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def safe_delete(self):
        self.user_deleted = True
        self.user_deleted_timestamp = timezone.now()

### MODELS ###

class RegistrarQuerySet(QuerySet):
    def approved(self):
        return self.filter(status="approved")

class Registrar(models.Model):
    """
    This is generally a library.
    """
    name = models.CharField(max_length=400)
    email = models.EmailField(max_length=254)
    website = models.URLField(max_length=500)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    status = models.CharField(max_length=20, default='pending', choices=(('pending','pending'),('approved','approved'),('denied','denied')))

    show_partner_status = models.BooleanField(default=False, help_text="Whether to show this registrar in our list of partners.")
    partner_display_name = models.CharField(max_length=400, blank=True, null=True, help_text="Optional. Use this to override 'name' for the partner list.")
    logo = models.ImageField(upload_to='registrar_logos', blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    link_count = models.IntegerField(default=0) # A cache of the number of links under this registrars's purview (sum of all associated org links)

    objects = RegistrarQuerySet.as_manager()
    tracker = FieldTracker()
    history = HistoricalRecords()
    tags = TaggableManager()

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class OrganizationQuerySet(QuerySet):
    def accessible_to(self, user):
        qset = self.user_access_filter(user)
        if qset is None:
            return self.none()
        else:
            return self.filter(qset)

    def user_access_filter(self, user):
        if user.is_organization_user:
            return Q(id__in=user.organizations.all())
        elif user.is_registrar_user():
            return Q(registrar_id=user.registrar_id)
        elif user.is_staff:
            return Q()  # all
        else:
            return None


OrganizationManager = DeletableManager.from_queryset(OrganizationQuerySet)


class Organization(DeletableModel):
    """
    This is generally a journal.
    """
    name = models.CharField(max_length=400)
    registrar = models.ForeignKey(Registrar, null=True, related_name="organizations")
    shared_folder = models.OneToOneField('Folder', blank=True, null=True, related_name="organization_")  # related_name isn't used, just set to avoid name collision with Folder.organization
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    default_to_private = models.BooleanField(default=False)
    link_count = models.IntegerField(default=0) # A cache of the number of links under this org's purview

    objects = OrganizationManager()
    tracker = FieldTracker()
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        name_has_changed = self.tracker.has_changed('name')
        super(Organization, self).save(*args, **kwargs)
        if not self.shared_folder:
            # Make sure shared folder is created for each org.
            self.create_shared_folder()
        elif name_has_changed:
            # Rename shared folder if org name changes.
            self.shared_folder.name = self.name
            self.shared_folder.save()

    def __unicode__(self):
        return self.name

    def create_shared_folder(self):
        if self.shared_folder:
            return
        shared_folder = Folder(name=self.name, organization=self, is_shared_folder=True)
        shared_folder.save()
        self.shared_folder = shared_folder
        self.save()


class LinkUserManager(BaseUserManager):
    def create_user(self, email, registrar, organization, date_joined, first_name, last_name, authorized_by, confirmation_code, password=None):
        """
        Creates and saves a User with the given email, registrar and password.
        """

        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            registrar=registrar,
            date_joined = date_joined,
            first_name = first_name,
            last_name = last_name,
            authorized_by = authorized_by,
            confirmation_code = confirmation_code
        )

        user.set_password(password)
        user.save()

        user.organizations.add(organization)
        user.save()

        user.create_root_folder()

        return user


class LinkUser(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        db_index=True,
        error_messages={'unique': u"A user with that email address already exists.",}
    )
    
    registrar = models.ForeignKey(Registrar, blank=True, null=True, related_name='users', help_text="If set, this user is a registrar user. This should not be set if org is set!")
    pending_registrar = models.ForeignKey(Registrar, blank=True, null=True, related_name='pending_users')
    organizations = models.ManyToManyField(Organization, blank=True, related_name='users', help_text="If set, this user is an org user. This should not be set if registrar is set!")
    is_active = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=45, blank=True)
    last_name = models.CharField(max_length=45, blank=True)
    confirmation_code = models.CharField(max_length=45, blank=True)
    root_folder = models.OneToOneField('Folder', blank=True, null=True)
    requested_account_type = models.CharField(max_length=45, blank=True, null=True)
    requested_account_note = models.CharField(max_length=45, blank=True, null=True)
    link_count = models.IntegerField(default=0) # A cache of the number of links created by this user
    monthly_link_limit = models.IntegerField(default=settings.MONTHLY_CREATE_LIMIT)

    objects = LinkUserManager()
    tracker = FieldTracker()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'

    def save(self, *args, **kwargs):
        super(LinkUser, self).save(*args, **kwargs)

        # make sure root folder is created for each user.
        if not self.root_folder:
            self.create_root_folder()

    def get_full_name(self):
        """ Use either First Last or first half of email address as user's name. """
        return "%s %s" % (self.first_name, self.last_name) if self.first_name or self.last_name else \
            self.email.split('@')[0]

    def get_short_name(self):
        """ Use either First or Last or first half of email address as user's short name. """
        return self.first_name or self.last_name or self.email.split('@')[0]

    # On Python 3: def __str__(self):
    def __unicode__(self):
        return self.email

    def all_folder_trees(self):
        """
            Get all folders for this user, including shared folders
        """

        orgs = self.get_orgs().select_related('shared_folder')

        return [self.root_folder.get_descendants(include_self=True)] + \
            ([org.shared_folder.get_descendants(include_self=True) for org in orgs if org])

    def get_orgs(self):
        """
            Get organizations in which this user is a member
        """

        if self.is_organization_user:
            return self.organizations.all()
        if self.is_registrar_user():
            return self.registrar.organizations.all()
        if self.is_staff:
            return Organization.objects.all()

        return Organization.objects.none()

    def get_links_remaining(self):
        today = timezone.now()

        link_count = Link.objects.filter(creation_timestamp__year=today.year, creation_timestamp__month=today.month, created_by_id=self.id, organization_id=None).count()
        return self.monthly_link_limit - link_count

    def create_root_folder(self):
        if self.root_folder:
            return
        try:
            # this branch only used during transition to root folders -- should be removed eventually
            root_folder = Folder.objects.filter(created_by=self, name=u"My Links", parent=None)[0]
            root_folder.is_root_folder = True
        except IndexError:
            root_folder = Folder(name=u'My Links', created_by=self, is_root_folder=True)
        root_folder.save()
        self.root_folder = root_folder
        self.save()

    def as_json(self, request=None):
        from api.resources import LinkUserResource
        return LinkUserResource().as_json(self, request)

    ### permissions ###

    def has_perm(self, perm, obj=None):
        """
            Does the user have a specific permission?
            Simplest possible answer: Yes, always
            This is only used by the django admin for is_staff=True users.
        """
        return True

    def has_module_perms(self, app_label):
        """
            Does the user have permissions to view the app `app_label`?
            Simplest possible answer: Yes, always
            This is only used by the django admin for is_staff=True users.
        """
        return True

    def has_limit(self):
        """ Does the user have a link creation limit? """
        return bool(not self.is_staff and not self.is_registrar_user() and not self.is_organization_user)

    def is_registrar_user(self):
        """ Is the user a member of a registrar? """
        return bool(self.registrar_id)

    def has_registrar_pending(self):
        """ Has requested creation of registrar """
        return bool(self.pending_registrar)

    @cached_property
    def is_organization_user(self):
        """ Is the user a member of an org? """
        return self.organizations.exists()

    ### link permissions ###

    def can_view(self, link):
        """
            Not all links are viewable by all users -- some users
            have privileged access to view private links. For example,
            a user can view their own private links.
        """
        if not link.is_private:
            return True
        return self.can_edit(link)

    def can_edit(self, link):
        """ Link is editable if it is in a folder accessible to this user. """
        if self.is_anonymous():
            return False
        if self.is_staff:
            return True
        return Folder.objects.accessible_to(self).filter(links=link).exists()

    def can_delete(self, link):
        """
            An archive can be deleted if it is less than 24 hours old-style
            and it was created by a user or someone in the org.
        """
        return not link.is_archive_eligible() and self.can_edit(link)

    def can_toggle_private(self, link):
        if not self.can_edit(link):
            return False
        if link.is_private and not self.is_staff and link.private_reason != 'user':
            return False
        return True

    def can_edit_registrar(self, registrar):
        return self.is_staff or self.registrar == registrar

    def can_edit_organization(self, organization):
        return self.organizations.filter(pk=organization.pk).exists()


# special history tracking for custom user object -- see http://django-simple-history.readthedocs.org/en/latest/reference.html
simple_history.register(LinkUser)

# This ugly business makes these functions available on logged-out users as well as logged-in,
# by monkeypatching Django's AnonymousUser object.
for func_name in ['can_view', 'can_edit', 'can_delete', 'can_toggle_private']:
    setattr(django.contrib.auth.models.AnonymousUser, func_name, getattr(LinkUser, func_name).__func__)


class FolderQuerySet(QuerySet):
    def user_access_filter(self, user):
        # personal folders
        filter = Q(owned_by=user)

        # folders owned by orgs in which the user a member
        orgs = user.get_orgs()
        if orgs:
            filter |= Q(organization__in=orgs)

        return filter

    def accessible_to(self, user):
        return self.filter(self.user_access_filter(user))


FolderManager = TreeManager.from_queryset(FolderQuerySet)


class Folder(MPTTModel):
    name = models.CharField(max_length=255, null=False, blank=False)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    creation_timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='folders_created',)

    # this may be null if this is the shared folder for a org
    owned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='folders',)

    # this will be set if this is inside a shared folder
    organization = models.ForeignKey(Organization, null=True, blank=True, related_name='folders')

    # true if this is the apex shared folder (not subfolder) for a org
    is_shared_folder = models.BooleanField(default=False)

    # true if this is the apex folder for a user
    is_root_folder = models.BooleanField(default=False)

    objects = FolderManager()
    tracker = FieldTracker()

    def save(self, *args, **kwargs):
        # set defaults
        if not self.pk:
            # set ownership same as parent
            if self.parent:
                if self.parent.organization:
                    self.organization = self.parent.organization
                else:
                    self.owned_by = self.parent.owned_by
            if self.created_by and not self.owned_by and not self.organization:
                self.owned_by = self.created_by

        parent_has_changed = self.tracker.has_changed('parent_id')

        super(Folder, self).save(*args, **kwargs)

        if parent_has_changed:
            # make sure that child folders share organization and owned_by with new parent folder
            # (one or the other should be set, but not both)
            if self.parent.organization_id:
                self.get_descendants(include_self=True).update(organization=self.parent.organization_id, owned_by=None)
            else:
                self.get_descendants(include_self=True).update(owned_by=self.parent.owned_by_id, organization=None)

    class MPTTMeta:
        order_insertion_by = ['name']

    def is_empty(self):
        return not self.children.exists() and not self.links.exists()

    def __unicode__(self):
        return self.name

    def contained_links(self):
        return Link.objects.filter(folders__in=self.get_descendants(include_self=True))

    def display_level(self):
        """
            Get hierarchical level for this folder. If this is a shared folder, level should be one higher
            because it is displayed below user's root folder.
        """
        return self.level + (1 if self.organization_id else 0)


class LinkQuerySet(QuerySet):
    def user_access_filter(self, user):
        """
            User can see/modify a link if they created it or it is in an org folder they belong to.
        """
        # personal links
        filter = Q(folders__owned_by=user)

        # links owned by orgs in which the user a member
        orgs = user.get_orgs()
        if orgs:
            filter |= Q(folders__organization__in=orgs)

        return filter

    def accessible_to(self, user):
        return self.filter(self.user_access_filter(user))

    def discoverable(self):
        """ Limit queryset to Links that can be publicly found by searching. """
        return self.filter(is_unlisted=False, is_private=False)


LinkManager = DeletableManager.from_queryset(LinkQuerySet)


HEADER_CHECK_TIMEOUT = 10  # keeping this setting out here allows tests to override it for speed

class Link(DeletableModel):
    """
    This is the core of the Perma link.
    """
    guid = models.CharField(max_length=255, null=False, blank=False, primary_key=True, editable=False)
    view_count = models.IntegerField(default=1)
    submitted_url = models.URLField(max_length=2100, null=False, blank=False)
    creation_timestamp = models.DateTimeField(default=timezone.now, editable=False)
    submitted_title = models.CharField(max_length=2100, null=False, blank=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='created_links',)
    organization = models.ForeignKey(Organization, null=True, blank=True, related_name='links')
    folders = models.ManyToManyField(Folder, related_name='links', blank=True)
    notes = models.TextField(blank=True)
    internet_archive_upload_status = models.CharField(max_length=20,
                                                      default='not_started',
                                                      choices=(('not_started','not_started'),('completed','completed'),('failed','failed'),('failed_permanently','failed_permanently'),('deleted','deleted')))

    warc_size = models.IntegerField(blank=True, null=True)

    is_private = models.BooleanField(default=False)
    private_reason = models.CharField(max_length=10, blank=True, null=True, choices=(('policy','Robots.txt or meta tag'),('user','At user direction'),('takedown','At request of content owner')))
    is_unlisted = models.BooleanField(default=False)

    archive_timestamp = models.DateTimeField(blank=True, null=True, help_text="Date after which this link is eligible to be copied by the mirror network.")

    thumbnail_status = models.CharField(max_length=10, null=True, blank=True, choices=(
        ('generating', 'generating'), ('generated', 'generated'), ('failed', 'failed')))

    objects = LinkManager()
    tracker = FieldTracker()
    history = HistoricalRecords()

    @cached_property
    def safe_url(self):
        """ Encoded URL as string rather than unicode. """
        return iri_to_uri(self.submitted_url)

    @cached_property
    def url_details(self):
        return urlparse(self.safe_url)

    @cached_property
    def ip(self):
        try:
            return socket.gethostbyname(self.url_details.netloc.split(':')[0])
        except socket.gaierror:
            return False

    @cached_property
    def headers(self):
        try:
            return requests.get(
                self.safe_url,
                verify=False,  # don't check SSL cert?
                headers={'User-Agent': settings.CAPTURE_USER_AGENT, 'Accept-Encoding': '*'},
                timeout=HEADER_CHECK_TIMEOUT,
                stream=True  # we're only looking at the headers
            ).headers
        except (requests.ConnectionError, requests.Timeout):
            return False

    def save(self, *args, **kwargs):
        # Set a default title if one is missing
        if not self.submitted_title:
            self.submitted_title = self.url_details.netloc

        initial_folder = kwargs.pop('initial_folder', None)

        if self.tracker.has_changed('is_unlisted') or self.tracker.has_changed('is_private'):
            CDXLine.objects.filter(link_id=self.pk).update(is_unlisted=self.is_unlisted, is_private=self.is_private)

        if not self.pk:
            if not self.archive_timestamp:
                self.archive_timestamp = self.creation_timestamp + settings.ARCHIVE_DELAY
            if not kwargs.pop("pregenerated_guid", False):
                # not self.pk => not created yet
                # only try 100 attempts at finding an unused GUID
                # (100 attempts should never be necessary, since we'll expand the keyspace long before
                # there are frequent collisions)
                guid_character_set = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
                for i in range(100):
                    # Generate an 8-character random string like "1A2B3C4D"
                    guid = ''.join(random.choice(guid_character_set) for _ in range(8))

                    # apply standard formatting (hyphens)
                    guid = Link.get_canonical_guid(guid)

                    # Avoid GUIDs starting with four letters (in case we need those later)
                    match = re.search(r'^[A-Z]{4}', guid)

                    if not match and not Link.objects.filter(guid=guid).exists():
                        break
                else:
                    raise Exception("No valid GUID found in 100 attempts.")
                self.guid = guid

        if self.is_private and not self.private_reason:
            self.private_reason = 'user'

        super(Link, self).save(*args, **kwargs)

        if not self.folders.count():
            if not initial_folder:
                if self.created_by and self.created_by.root_folder:
                    initial_folder = self.created_by.root_folder
            if initial_folder:
                self.folders.add(initial_folder)

    def __unicode__(self):
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
            If folder is None, link is moved to root (no folder).
        """
        # remove this link from any folders it's in for this user
        self.folders.remove(*self.folders.accessible_to(user))
        # add it back to the given folder
        if folder:
            self.folders.add(folder)
            if not folder.organization:
                self.organization = None
            else:
                self.organization = folder.organization
            self.save(update_fields=['organization'])

    def can_upload_to_internet_archive(self):
        """ Return True if this link is appropriate for upload to IA. """
        return self.is_discoverable()

    def as_json(self, request=None):
        from api.resources import LinkResource
        return LinkResource().as_json(self, request)

    def guid_as_path(self):
        # For a GUID like ABCD-1234, return a path like AB/CD/12.
        stripped_guid = re.sub('[^0-9A-Za-z]+', '', self.guid)
        guid_parts = [stripped_guid[i:i + 2] for i in range(0, len(stripped_guid), 2)]
        return '/'.join(guid_parts[:-1])

    def warc_storage_file(self):
        return os.path.join(settings.WARC_STORAGE_DIR, self.guid_as_path(), '%s.warc.gz' % self.guid)

    # def get_thumbnail(self, image_data=None):
    #     if self.thumbnail_status == 'failed' or self.thumbnail_status == 'generating':
    #         return None
    #
    #     thumbnail_path = os.path.join(settings.THUMBNAIL_STORAGE_PATH, self.guid_as_path(), 'thumbnail.png')
    #
    #     if self.thumbnail_status == 'generated' and default_storage.exists(thumbnail_path):
    #         return default_storage.open(thumbnail_path)
    #
    #     try:
    #
    #         warc_url = None
    #         image = None
    #
    #         if image_data:
    #             image = Image(blob=image_data)
    #         else:
    #
    #             if self.screenshot_capture and self.screenshot_capture.status == 'success':
    #                 warc_url = self.screenshot_capture.url
    #             else:
    #                 pdf_capture = self.captures.filter(content_type__startswith='application/pdf').first()
    #                 if pdf_capture:
    #                     warc_url = pdf_capture.url
    #
    #             if warc_url:
    #                 self.thumbnail_status = 'generating'
    #                 self.save(update_fields=['thumbnail_status'])
    #
    #                 headers, data = self.replay_url(warc_url)
    #                 temp_file = tempfile.NamedTemporaryFile(suffix='.' + warc_url.rsplit('.', 1)[-1])
    #                 for chunk in data:
    #                     temp_file.write(chunk)
    #                 temp_file.flush()
    #                 image = Image(filename=temp_file.name + "[0]")  # [0] limits ImageMagick to first page of PDF
    #
    #         if image:
    #             with imagemagick_temp_dir():
    #                 with image as opened_img:
    #                     opened_img.transform(resize='600')
    #                     # opened_img.resize(600,600)
    #                     with Image(width=600, height=600) as dst_image:
    #                         dst_image.composite(opened_img, 0, 0)
    #                         dst_image.compression_quality = 60
    #                         default_storage.store_data_to_file(dst_image.make_blob('png'), thumbnail_path, overwrite=True)
    #
    #             self.thumbnail_status = 'generated'
    #             self.save(update_fields=['thumbnail_status'])
    #
    #             return default_storage.open(thumbnail_path)
    #
    #     except Exception as e:
    #         print "Thumbnail generation failed for %s: %s" % (self.guid, e)
    #
    #     self.thumbnail_status = 'failed'
    #     self.save(update_fields=['thumbnail_status'])

    def delete_related(self):
        CDXLine.objects.filter(link_id=self.pk).delete()
        Capture.objects.filter(link_id=self.pk).delete()

    def is_archive_eligible(self):
        """
            True if it's older than 24 hours
        """
        return self.archive_timestamp < timezone.now()

    @cached_property
    def screenshot_capture(self):
        return self.captures.filter(role='screenshot').first()

    @cached_property
    def primary_capture(self):
        return self.captures.filter(role='primary').first()

    @cached_property
    def favicon_capture(self):
        return self.captures.filter(role='favicon').first()

    def write_warc_header(self, out_file):
        # build warcinfo header
        headers = [
            (warctools.WarcRecord.ID, warctools.WarcRecord.random_warc_uuid()),
            (warctools.WarcRecord.TYPE, warctools.WarcRecord.WARCINFO),
            (warctools.WarcRecord.DATE, warctools.warc.warc_datetime_str(self.creation_timestamp))
        ]
        warcinfo_fields = [
            b'operator: Perma.cc',
            b'format: WARC File Format 1.0',
            b'Perma-GUID: %s' % self.guid,
        ]
        data = b'\r\n'.join(warcinfo_fields) + b'\r\n'
        warcinfo_record = warctools.WarcRecord(headers=headers, content=(b'application/warc-fields', data))
        warcinfo_record.write_to(out_file, gzip=True)

    def write_warc_resource_record(self, source_file_handle_or_data, url, content_type, warc_date=None, out_file=None):
        data = source_file_handle_or_data.read() if hasattr(source_file_handle_or_data, 'read') else source_file_handle_or_data
        return self.write_warc_record(warctools.WarcRecord.RESOURCE, url, data, content_type, warc_date, out_file)

    def write_warc_metadata_record(self, metadata, url, concurrent_to, warc_date=None, out_file=None):
        data = json.dumps(metadata)
        extra_headers = [
            (warctools.WarcRecord.CONCURRENT_TO, concurrent_to)
        ]
        return self.write_warc_record(warctools.WarcRecord.RESOURCE, url, data, "application/json", warc_date, out_file, extra_headers)

    def write_warc_record(self, record_type, url, data, content_type, warc_date=None, out_file=None, extra_headers=None):
        # set default date and convert to string if necessary
        warc_date = warc_date or timezone.now()
        if hasattr(warc_date, 'isoformat'):
            warc_date = warctools.warc.warc_datetime_str(warc_date)

        close_file = not out_file
        out_file = out_file or self.open_warc_for_writing()
        headers = [
            (warctools.WarcRecord.TYPE, record_type),
            (warctools.WarcRecord.ID, warctools.WarcRecord.random_warc_uuid()),
            (warctools.WarcRecord.DATE, warc_date),
            (warctools.WarcRecord.URL, url),
            (warctools.WarcRecord.BLOCK_DIGEST, b'sha1:%s' % hashlib.sha1(data).hexdigest())
        ]
        if extra_headers:
            headers.extend(extra_headers)
        record = warctools.WarcRecord(headers=headers, content=(content_type, data))
        record.write_to(out_file, gzip=True)

        if close_file:
            self.close_warc_after_writing(out_file)

        return headers

    def write_warc_raw_data(self, source_file_handle_or_data, out_file=None):
        close_file = not out_file
        out_file = out_file or self.open_warc_for_writing()
        if hasattr(source_file_handle_or_data, 'read'):
            copy_file_data(source_file_handle_or_data, out_file)
        else:
            out_file.write(source_file_handle_or_data)
        if close_file:
            self.close_warc_after_writing(out_file)

    def open_warc_for_writing(self):
        out = tempfile.TemporaryFile()
        if default_storage.exists(self.warc_storage_file()):
            copy_file_data(default_storage.open(self.warc_storage_file()), out)
        else:
            self.write_warc_header(out)
        return out

    def close_warc_after_writing(self, out):
        out.flush()
        out.seek(0)
        default_storage.store_file(out, self.warc_storage_file(), overwrite=True)
        out.close()

    def safe_delete_warc(self):
        WARC_STORAGE_PATH = os.path.join(settings.MEDIA_ROOT, settings.WARC_STORAGE_DIR)
        guid_path = self.guid_as_path()
        try:
            old_name = os.path.join(WARC_STORAGE_PATH, guid_path, '%s.warc.gz' % self.guid)
            new_name = os.path.join(WARC_STORAGE_PATH, guid_path, '%s_replaced.warc.gz' % self.guid)
            os.rename(old_name, new_name)
        except OSError:
            return

    def replay_url(self, url):
        """
            Given a URL contained in this WARC, return the headers and data as played back by pywb.
        """
        import sys
        from warc_server.app import application

        fake_environ = {'HTTP_COOKIE': {}, 'QUERY_STRING': '', 'REQUEST_METHOD': 'GET', 'SCRIPT_NAME': '',
                        'SERVER_NAME': 'fake', 'SERVER_PORT': '80', 'SERVER_PROTOCOL': 'HTTP/1.1',
                        'wsgi.errors': sys.stderr, 'wsgi.input': sys.stdin}

        fake_environ['PATH_INFO'] = '/%s/%s' % (self.guid, url)

        headers = {}

        def fake_start_response(status, response_headers, exc_info=None):
            headers.update(response_headers)

        data = application(fake_environ, fake_start_response)

        return headers, data

    def base_playback_url(self, host=None):
        host = host or settings.WARC_HOST
        return u"%s/warc/%s/" % (("//" + host if host else ''), self.guid)

    def create_access_token(self):
        """
            Return an access token for accessing this link.
            Access token consists of the link GUID, signed by Django with the current timestamp.
        """
        return TimestampSigner().sign(self.pk)

    def validate_access_token(self, token, max_age=60):
        """
            Validate an access token for this link.
            Access token should be the link GUID, signed by Django no more than max_age seconds ago.
        """
        try:
            return TimestampSigner().unsign(token, max_age=max_age) == self.pk
        except BadSignature:
            return False

    def is_discoverable(self):
        return not self.is_private and not self.is_unlisted

    ### functions to deal with link-specific caches ###

    @classmethod
    def get_cdx_cache_key(cls, guid):
        return "cdx-"+guid

    @classmethod
    def get_warc_cache_key(cls, warc_storage_file):
        return "warc-"+re.sub('[^\w-]', '', warc_storage_file)

    def clear_cache(self):
        cache.delete(Link.get_cdx_cache_key(self.guid))
        cache.delete(Link.get_warc_cache_key(self.warc_storage_file()))


class Capture(models.Model):
    link = models.ForeignKey(Link, null=False, related_name='captures')
    role = models.CharField(max_length=10, choices=(('primary','primary'),('screenshot','screenshot'),('favicon','favicon')))
    status = models.CharField(max_length=10, choices=(('pending','pending'),('failed','failed'),('success','success')))
    url = models.CharField(max_length=2100, blank=True, null=True)
    record_type = models.CharField(max_length=10, choices=(
        ('response','WARC Response record -- recorded from web'),
        ('resource','WARC Resource record -- file without web headers')))
    content_type = models.CharField(max_length=255, null=False, default='', help_text="HTTP Content-type header.")
    user_upload = models.BooleanField(default=False, help_text="True if the user uploaded this capture.")

    def __unicode__(self):
        return "%s %s" % (self.role, self.status)

    def write_warc_resource_record(self, in_file, warc_date=None, out_file=None):
        return self.link.write_warc_resource_record(in_file, self.url, self.content_type, warc_date, out_file)

    def get_headers(self):
        headers, data = self.link.replay_url(self.url)
        return headers

    def read_content_type(self):
        """
            Read content-type from warc file.
            TODO: This does NOT work if the capture starts with a redirect to a different URL.
        """
        for key, val in self.get_headers().iteritems():
            if key.lower() == 'content-type':
                return val
        return ''

    def use_sandbox(self):
        """
            Whether the iframe we use to display this capture should be sandboxed.
            Answer is yes unless we're playing back a PDF, which currently can't
            be sandboxed in Chrome.
        """
        return not self.content_type.startswith("application/pdf")

    INLINE_TYPES = {'image/jpeg', 'image/gif', 'image/png', 'image/tiff', 'text/html', 'text/plain', 'application/pdf',
                    'application/xhtml', 'application/xhtml+xml'}

    def show_interstitial(self):
        """
            Whether we should show an interstitial view/download button instead of showing the content directly.
            True unless we recognize the mime type as something that should be shown inline (PDF/HTML/image).
        """
        return self.mime_type() not in self.INLINE_TYPES

    def mime_type(self):
        """
            Return normalized mime type from content_type.
            Stuff after semicolon is stripped, type is lowercased, and x- prefix is removed.
        """
        return self.content_type.split(";", 1)[0].lower().replace('/x-', '/')

    def url_fragment(self):
        return ("id_/" if self.record_type == 'resource' else "") + self.url

    def playback_url(self):
        if not self.url:
            return None
        return self.link.base_playback_url() + self.url_fragment()

    def playback_url_with_access_token(self):
        """
            Return a URL that will allow playback of a private link.
            If link is not private, returns regular playback URL.

            IMPORTANT: Links returned by this function should only be displayed to authorized users.
        """
        if not self.link.is_private:
            return self.playback_url()
        return mark_safe("//%s%s?%s" % (
            settings.WARC_HOST,
            reverse('user_management_set_access_token_cookie'),
            urlencode({
                'token': self.link.create_access_token(),
                'guid': self.link_id,
                'next': self.url_fragment(),
            })
        ))


class CaptureJob(models.Model):
    """
        This class tracks capture jobs for purposes of:
            (1) sorting the capture queue fairly and
            (2) reporting status during a capture.
    """
    link = models.OneToOneField(Link, related_name='capture_job')
    status = models.CharField(max_length=15,
                              default='pending',
                              choices=(('pending','pending'),('in_progress','in_progress'),('completed','completed'),('deleted','deleted'),('failed','failed')))
    human = models.BooleanField(default=False)

    # reporting
    attempt = models.SmallIntegerField(default=0)
    step_count = models.FloatField(default=0)
    step_description = models.CharField(max_length=255, blank=True, null=True)
    capture_start_time = models.DateTimeField(blank=True, null=True)
    capture_end_time = models.DateTimeField(blank=True, null=True)

    CACHE_KEY = 'capture_job_queue'

    # Don't use the cache if we're using background celery processes and the local memory cache (presumably in the dev
    # environment) -- caching the queue only works if all threads see the same cache.
    USE_CACHE = settings.RUN_TASKS_ASYNC is False or 'LocMemCache' not in settings.CACHES['default']['BACKEND']

    # used for testing, to find concurrency errors
    CACHE_DELAY = 0
    USE_LOCK = True

    def __unicode__(self):
        return u"CaptureJob %s: %s" % (self.pk, self.link_id)

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super(CaptureJob, self).save(*args, **kwargs)

        # add new jobs to the job queue
        if is_new:
            with self.get_job_queues() as job_queues:
                self.add_to_queue(job_queues)

    @classmethod
    def clear_cache(cls):
        """ Wipe the queue cache -- mostly useful for tests. """
        cache.delete(cls.CACHE_KEY)

    @classmethod
    @contextmanager
    def get_job_queues(cls):
        """
            This is a context manager we can use to get LOCKED access to a dictionary of all pending CaptureJobs. The
            dictionary is generated from the database the first time but then stored in the cache for faster access.
            If a caller updates pending CaptureJobs in the database, it should also update the cache.
            Any changes to the dictionary made by the caller will be saved back to the cache.

            Example usage:

                with CaptureJob.get_job_queues() as job_queues:
                    # do atomic-access stuff with job_queues

            job_queues format:

                  {'human': {
                      <user_id>: {
                          'last_job_time':<CaptureJob.capture_start_time as integer>,
                          'next_jobs':[<CaptureJob.pk>,<CaptureJob.pk>]
                      },
                      <user_id>: { ... },
                   'robot':{ ... }
                  }

        """

        with transaction.atomic():

            # Use select_for_update on the first CaptureJob to claim a lock on the cache.
            if cls.USE_LOCK:
                lock_row = cls.objects.order_by('pk').select_for_update().first()  # noqa

            # try fetching queue from cache
            job_queues = cache.get(CaptureJob.CACHE_KEY) if cls.USE_CACHE else None

            # if not, regenerate cache
            if job_queues is None:

                # mark any captures as deleted where link has been deleted before capture
                CaptureJob.objects.filter(link__user_deleted=True, status='pending').update(status='deleted')

                # Grab all pending jobs in a dict by job type (human or robot) and user ID.
                job_queues = {'human': {}, 'robot': {}}
                pending_jobs = cls.objects.filter(status='pending').order_by('pk').select_related('link')
                for job in pending_jobs:
                    job.add_to_queue(job_queues)

            yield job_queues

            # optional delay, used solely for our concurrency tests
            if cls.CACHE_DELAY:
                time.sleep(cls.CACHE_DELAY)

            # save any changes made by caller
            if cls.USE_CACHE:
                cache.set(CaptureJob.CACHE_KEY, job_queues)

    def add_to_queue(self, job_queues):
        """
            Insert a single job in the appropriate queue.
        """
        job_type = 'human' if self.human else 'robot'
        job_queue = job_queues[job_type]
        user_id = self.link.created_by_id
        if user_id not in job_queue:
            last_job = CaptureJob.objects.filter(link__created_by_id=user_id).exclude(status='pending').order_by('-pk').first()
            job_queue[user_id] = {
                'next_jobs': [],
                'last_job_time': last_job.capture_start_time.isoformat() if last_job else '0'
            }
        if self.pk not in job_queue[user_id]['next_jobs']:
            job_queue[user_id]['next_jobs'].append(self.pk)

    @classmethod
    def sort_job_queue(cls, job_queue):
        """
            Sort users in a job queue by preference.
        """
        return sorted(
            job_queue.iteritems(),
            key=lambda x: (
                x[1]['last_job_time'],  # whose previous job is oldest?
                x[1]['next_jobs'][0])  # whose next job is oldest?
        )

    @classmethod
    def get_next_job(cls, reserve=False):
        """
            Return the next job to work on, looking first at the human queue and then at the robot queue.

            If `reserve=True`, mark the returned job with `status=in_progress` and remove from queue so the
            same job can't be returned twice. Caller must make sure the job is actually processed once returned.
        """
        with cls.get_job_queues() as job_queues:

            # look first at the human queue, or if that's empty at the robot queue
            job_queue = job_queues['human'] or job_queues['robot']

            if not job_queue:
                return  # no jobs to process

            next_user_id, next_user = cls.sort_job_queue(job_queue)[0]
            next_job = cls.objects.get(pk=next_user['next_jobs'][0])

            # mark the job as in_progress so we won't return it the next time this is called
            if reserve:
                # update db
                next_job.status = 'in_progress'
                next_job.capture_start_time = timezone.now()
                next_job.save()

                # update cache
                next_user['next_jobs'].pop(0)
                if next_user['next_jobs']:
                    next_user['last_job_time'] = next_job.capture_start_time.isoformat()
                else:
                    del job_queue[next_user_id]

            return next_job

    def queue_position(self):
        """
            Search job_queues to calculate the queue position for this job -- how many pending jobs have to be processed
            before this one?

            Returns:
                0 if job is not pending
                -1 if job is pending but not in queue.
        """
        if self.status != 'pending':
            return 0

        # Grab the job queues and figure out which queue we're looking at -- human or robot
        with self.get_job_queues() as job_queues:
            pass
        queue_position = 1
        if self.human:
            queue = job_queues['human']
        else:
            queue = job_queues['robot']

            # if robot, count all of the human jobs that will have to be processed first
            queue_position += sum(len(i['next_jobs']) for i in job_queues['human'].itervalues())

        # make sure job is in queue
        user_id = self.link.created_by_id
        if user_id not in queue or self.pk not in queue[user_id]['next_jobs']:
            # job isn't in queue
            return -1

        # Jobs are processed round-robin. First figure out which round this job will be in.
        job_round = queue[user_id]['next_jobs'].index(self.pk)

        # Next add all of the jobs that will be processed in previous rounds.
        queue_position += sum(len(i['next_jobs'][:job_round]) for i in queue.itervalues())

        # For the last round, this job will be reached partway through. Sort the jobs to find out which users will go
        # first, and then add 1 for each user who will have jobs left in the final round and comes before this user.
        sorted_jobs = self.sort_job_queue(queue)
        sorted_user_ids = [i[0] for i in sorted_jobs]
        queue_position += sum(1 for j in sorted_jobs[:sorted_user_ids.index(user_id)] if len(j[1]['next_jobs'])>job_round)

        return queue_position

    def mark_completed(self, status='completed'):
        """
            Record completion time and status for this job.
        """
        self.status = status
        self.capture_end_time = timezone.now()
        self.save(update_fields=['status', 'capture_end_time'])


#########################
# Stats related models
#########################

class WeekStats(models.Model):
    """
    Our stats dashboard displays weekly stats. Let's house those here.
    """

    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True)


    links_sum = models.IntegerField(default=0)
    users_sum = models.IntegerField(default=0)
    organizations_sum = models.IntegerField(default=0)
    registrars_sum = models.IntegerField(default=0)


class MinuteStats(models.Model):
    """
    To see how the flag is blowing in Perma land, we log sums
    for key points activity each minute
    """

    creation_timestamp = models.DateTimeField(auto_now_add=True)

    links_sum = models.IntegerField(default=0)
    users_sum = models.IntegerField(default=0)
    organizations_sum = models.IntegerField(default=0)
    registrars_sum = models.IntegerField(default=0)


class CDXLineManager(models.Manager):
    def create_all_from_link(self, link):
        warc_path = link.warc_storage_file()
        with default_storage.open(warc_path, 'rb') as warc_file, io.BytesIO() as cdx_io:
            write_cdx_index(cdx_io, warc_file, warc_path)
            cdx_io.seek(0)
            next(cdx_io) # first line is a header so skip it
            results = []
            for line in cdx_io:
                cdxline = CDXLine.objects.get_or_create(raw=line, link_id=link.guid)[0]
                cdxline.is_unlisted = link.is_unlisted
                cdxline.is_private = link.is_private
                cdxline.save()
                results.append(cdxline)

        return results


class CDXLine(models.Model):
    link_id = models.CharField(null=True, max_length=255, db_index=True)
    urlkey = models.CharField(max_length=2100, null=False, blank=False)
    raw = models.TextField(null=False, blank=False)
    is_unlisted = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)

    objects = CDXLineManager()

    def __init__(self, *args, **kwargs):
        super(CDXLine, self).__init__(*args, **kwargs)
        if self.raw:
            self.__set_defaults()

    @cached_property
    def parsed(self):
        return CDXObject(self.raw)

    def __set_defaults(self):
        if not self.urlkey:
            self.urlkey = self.parsed['urlkey']

    @cached_property
    def timestamp(self):
        return self.parsed['timestamp']

    def is_revisit(self):
        return self.parsed.is_revisit()


class UncaughtError(models.Model):
    current_url = models.TextField()
    user_agent = models.TextField()
    stack = models.TextField()
    name = models.TextField()
    message = models.TextField()
    custom_message = models.TextField()
    user = models.ForeignKey(LinkUser, null=True, blank=True, related_name="errors_triggered")
    created_at = models.DateTimeField(default=timezone.now)

    resolved = models.BooleanField(default=False)
    resolved_by_user = models.ForeignKey(LinkUser, null=True, blank=True, related_name="errors_resolved")
