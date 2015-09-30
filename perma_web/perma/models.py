import hashlib
import io
import json
from mimetypes import MimeTypes
import os
import logging
import random
import re
import socket
import tempfile
from urlparse import urlparse
from hanzo import warctools
import requests
from wand.image import Image

from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.conf import settings
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

from api.validations import get_mime_type
from .utils import copy_file_data


logger = logging.getLogger(__name__)


class Registrar(models.Model):
    """
    This is generally a library.
    """
    name = models.CharField(max_length=400)
    email = models.EmailField(max_length=254)
    website = models.URLField(max_length=500)
    date_created = models.DateField(auto_now_add=True, null=True)
    default_organization = models.OneToOneField('Organization', blank=True, null=True, related_name='default_for_registrars') # each registrar gets a default org
    is_approved = models.BooleanField(default=False)

    show_partner_status = models.BooleanField(default=False, help_text="Whether to show this registrar in our list of partners.")
    partner_display_name = models.CharField(max_length=400, blank=True, null=True, help_text="Optional. Use this to override 'name' for the partner list.")
    logo = models.ImageField(upload_to='registrar_logos', blank=True, null=True)

    tracker = FieldTracker()

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        super(Registrar, self).save(*args, **kwargs)
        self.create_default_org()

    def __unicode__(self):
        return self.name
        
    def create_default_org(self):
        """
            Create a default org for this registrar, if there isn't
            one. (When registrar member creates an archive, we
            associate that archive with this org by default.)
        """
        
        if hasattr(self, 'default_organization') and self.default_organization is not None:
            return
        else:
            org = Organization(registrar=self, name="Default Organization")
            org.save()
            self.default_organization = org
            self.save()


class OrganizationQuerySet(QuerySet):
    def accessible_to(self, user):
        qset = Organization.objects.user_access_filter(user)
        if qset is None:
            return self.none()
        else:
            return self.filter(qset)


class OrganizationManager(models.Manager):
    """
        Org manager that can enforce user access perms.
    """
    def get_queryset(self):
        return OrganizationQuerySet(self.model, using=self._db)

    def user_access_filter(self, user):
        if user.is_organization_member:
            return Q(id__in=user.organizations.all())
        elif user.is_registrar_member():
            return Q(registrar_id=user.registrar_id)
        elif user.is_staff:
            return Q()  # all
        else:
            return None

    def accessible_to(self, user):
        return self.get_queryset().accessible_to(user)


class Organization(models.Model):
    """
    This is generally a journal.
    """
    name = models.CharField(max_length=400)
    registrar = models.ForeignKey(Registrar, null=True, related_name="organizations")
    shared_folder = models.OneToOneField('Folder', blank=True, null=True, related_name="organization_")  # related_name isn't used, just set to avoid name collision with Folder.organization
    date_created = models.DateField(auto_now_add=True, null=True)
    default_to_private = models.BooleanField(default=False)

    objects = OrganizationManager()
    tracker = FieldTracker()

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
    )
    registrar = models.ForeignKey(Registrar, blank=True, null=True, related_name='users', help_text="If set, this user is a registrar member. This should not be set if org is set!")
    pending_registrar = models.IntegerField(blank=True, null=True)
    organizations = models.ManyToManyField(Organization, blank=True, null=True, related_name='users', help_text="If set, this user is an org member. This should not be set if registrar is set!")
    is_active = models.BooleanField(default=True)
    is_confirmed = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateField(auto_now_add=True)
    first_name = models.CharField(max_length=45, blank=True)
    last_name = models.CharField(max_length=45, blank=True)
    confirmation_code = models.CharField(max_length=45, blank=True)
    root_folder = models.OneToOneField('Folder', blank=True, null=True)
    requested_account_type = models.CharField(max_length=45, blank=True, null=True)
    requested_account_note = models.CharField(max_length=45, blank=True, null=True)

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
        
        orgs = self.get_orgs()

        return [self.root_folder.get_descendants(include_self=True)] + \
            ([org.shared_folder.get_descendants(include_self=True) for org in orgs if org])

    def get_orgs(self):
        """
            Get organizations in which this user is a member
        """

        if self.is_organization_member:
            return self.organizations.all()
        if self.is_registrar_member():
            return self.registrar.organizations.all()
        if self.is_staff:
            return Organization.objects.all()
            
        return []
        
    def get_links_remaining(self):
    	today = timezone.now()
    	link_count = Link.objects.filter(creation_timestamp__year=today.year, creation_timestamp__month=today.month, created_by_id=self.id, organization_id=None).count()
    	return settings.MONTHLY_CREATE_LIMIT - link_count

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

    def can_vest(self):
        """ Can the user vest links? """
        return bool(self.is_staff or self.is_registrar_member() or self.is_organization_member)
        
    def has_limit(self):
        """ Does the user have a link creation limit? """
        return bool(not self.is_staff and not self.is_registrar_member() and not self.is_organization_member)

    def is_registrar_member(self):
        """ Is the user a member of a registrar? """
        return bool(self.registrar_id)
        
    def has_registrar_pending(self):
        """ Has requested creation of registrar """
        return bool(self.pending_registrar)

    @cached_property
    def is_organization_member(self):
        """ Is the user a member of an org? """
        return self.organizations.exists()


class FolderQuerySet(QuerySet):
    def accessible_to(self, user):
        return self.filter(Folder.objects.user_access_filter(user))


class FolderManager(models.Manager):
    """
        Folder manager that can enforce user access perms.
    """
    def get_queryset(self):
        return FolderQuerySet(self.model, using=self._db)

    def user_access_filter(self, user):
        # personal folders
        filter = Q(owned_by=user)

        # folders owned by orgs in which the user a member
        orgs = user.get_orgs()
        if orgs:
            filter |= Q(organization=orgs)

        return filter

    def accessible_to(self, user):
        return self.get_queryset().accessible_to(user)


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
    def accessible_to(self, user):
        return self.filter(Link.objects.user_access_filter(user))


class LinkManager(models.Manager):
    """
        Link manager that can enforce user access perms.
    """
    def get_queryset(self):
        # exclude deleted entries by default
        return LinkQuerySet(self.model, using=self._db).filter(user_deleted=False)

    def all_with_deleted(self):
        return super(LinkManager, self).get_query_set()

    def deleted_set(self):
        return super(LinkManager, self).get_query_set().filter(user_deleted=True)

    def user_access_filter(self, user):
        """
            User can see/modify a link if they created it or it is in an org folder they belong to.
        """
        # personal links
        filter = Q(folders__owned_by=user)

        # links owned by orgs in which the user a member
        orgs = user.get_orgs()
        if orgs:
            filter |= Q(folders__organization=orgs)

        return filter

    def accessible_to(self, user):
        return self.get_queryset().accessible_to(user)

HEADER_CHECK_TIMEOUT = 10
# This is the PhantomJS default agent
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/534.34 (KHTML, like Gecko) PhantomJS/1.9.0 (development) Safari/534.34"

class Link(models.Model):
    """
    This is the core of the Perma link.
    """
    guid = models.CharField(max_length=255, null=False, blank=False, primary_key=True, editable=False)
    view_count = models.IntegerField(default=1)
    submitted_url = models.URLField(max_length=2100, null=False, blank=False)
    creation_timestamp = models.DateTimeField(default=timezone.now, editable=False)
    submitted_title = models.CharField(max_length=2100, null=False, blank=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='created_links',)
    dark_archived = models.BooleanField(default=False)
    dark_archived_robots_txt_blocked = models.BooleanField(default=False)
    dark_archived_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='darchived_links')
    user_deleted = models.BooleanField(default=False)
    user_deleted_timestamp = models.DateTimeField(null=True, blank=True)
    vested = models.BooleanField(default=False)
    vested_by_editor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='vested_links')
    vested_timestamp = models.DateTimeField(null=True, blank=True)
    organization = models.ForeignKey(Organization, null=True, blank=True)
    folders = models.ManyToManyField(Folder, related_name='links', blank=True, null=True)
    notes = models.TextField(blank=True)
    is_private = models.BooleanField(default=False)

    archive_timestamp = models.DateTimeField(blank=True, null=True, help_text="Date after which this link is eligible to be copied by the mirror network.")

    thumbnail_status = models.CharField(max_length=10, null=True, blank=True, choices=(
        ('generating', 'generating'), ('generated', 'generated'), ('failed', 'failed')))

    objects = LinkManager()
    tracker = FieldTracker()

    @cached_property
    def url_details(self):
        return urlparse(self.submitted_url)

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
                self.submitted_url,
                verify=False,  # don't check SSL cert?
                headers={'User-Agent': USER_AGENT, 'Accept-Encoding': '*'},
                timeout=HEADER_CHECK_TIMEOUT,
                stream=True  # we're only looking at the headers
            ).headers
        except (requests.ConnectionError, requests.Timeout):
            return False

    # media_type is a file extension-ish normalized mimemedia_type
    @cached_property
    def media_type(self):
        if self.headers.get('content-type', '').lower() in ['application/pdf', 'application/x-pdf'] or self.submitted_url.endswith('.pdf'):
            return 'pdf'
        else:
            return False

    def save(self, *args, **kwargs):
        # Set a default title if one is missing
        if not self.submitted_title:
            self.submitted_title = self.url_details.netloc

        initial_folder = kwargs.pop('initial_folder', None)

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
        # handle legacy 10/11-char GUIDs
        if '-' not in guid and (len(guid) == 10 or len(guid) == 11):
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

    def can_view(self, user):
        """
            Not all links are viewable by all users -- some users
            have privileged access to view dark archived links. For example, 
            a user can view their own dark archived links.
        """

        if not self.dark_archived:
            return True

        if self.created_by == user:
            return True

        if self.organization in user.get_orgs:
            return True

        return False

    def get_expiration_date(self):
        """ Return date when this link will theoretically be deleted. """
        return self.creation_timestamp + settings.LINK_EXPIRATION_TIME

    def can_delete(self, user):
        """ An archive can be deleted if it is less than 24 hours old-style
            and it was created by a user or someone in the org """

        if not user.is_authenticated():
            return False

        user_has_delete_privs = False

        if user.is_staff or self.created_by == user or self.organization in user.get_orgs():
            user_has_delete_privs = True

        return timezone.now() < self.archive_timestamp and user_has_delete_privs

    def can_upload_to_internet_archive(self):
        """ Return True if this link is appropriate for upload to IA. """
        return self.vested \
               and not self.dark_archived and not self.dark_archived_robots_txt_blocked

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

    def get_thumbnail(self, image_data=None):
        if self.thumbnail_status == 'failed' or self.thumbnail_status == 'generating':
            return None

        thumbnail_path = os.path.join(settings.THUMBNAIL_STORAGE_PATH, self.guid_as_path(), 'thumbnail.png')

        if self.thumbnail_status == 'generated' and default_storage.exists(thumbnail_path):
            return default_storage.open(thumbnail_path)

        try:

            warc_url = None
            image = None

            if image_data:
                image = Image(blob=image_data)
            else:

                if self.screenshot_capture and self.screenshot_capture.status == 'success':
                    warc_url = self.screenshot_capture.url
                else:
                    pdf_capture = self.captures.filter(content_type__startswith='application/pdf').first()
                    if pdf_capture:
                        warc_url = pdf_capture.url

                if warc_url:
                    self.thumbnail_status = 'generating'
                    self.save(update_fields=['thumbnail_status'])

                    headers, data = self.replay_url(warc_url)
                    temp_file = tempfile.NamedTemporaryFile(suffix='.' + warc_url.rsplit('.', 1)[-1])
                    for chunk in data:
                        temp_file.write(chunk)
                    temp_file.flush()
                    image = Image(filename=temp_file.name + "[0]")  # [0] limits ImageMagick to first page of PDF

            if image:
                with imagemagick_temp_dir():
                    with image as opened_img:
                        opened_img.transform(resize='600')
                        # opened_img.resize(600,600)
                        with Image(width=600, height=600) as dst_image:
                            dst_image.composite(opened_img, 0, 0)
                            dst_image.compression_quality = 60
                            default_storage.store_data_to_file(dst_image.make_blob('png'), thumbnail_path, overwrite=True)

                self.thumbnail_status = 'generated'
                self.save(update_fields=['thumbnail_status'])

                return default_storage.open(thumbnail_path)

        except Exception as e:
            print "Thumbnail generation failed for %s: %s" % (self.guid, e)

        self.thumbnail_status = 'failed'
        self.save(update_fields=['thumbnail_status'])

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

    @transaction.atomic
    def export_warc(self):
        # by using select_for_update and checking for existence of this file,
        # we make sure that we won't accidentally try to create the file multiple
        # times in parallel.
        asset = self.assets.select_for_update().first()
        if not asset:
            return  # this is not an old-style Link
        if default_storage.exists(self.warc_storage_file()):
            return

        guid = self.guid
        out = self.open_warc_for_writing()

        def write_resource_record(file_path, url, content_type):
            self.write_warc_resource_record(
                default_storage.open(file_path),
                url.encode('utf8'),
                content_type,
                default_storage.created_time(file_path),
                out)

        def write_metadata_record(metadata, target_headers):
            concurrent_to = (v for k, v in target_headers if k == warctools.WarcRecord.ID).next()
            warc_date = (v for k, v in target_headers if k == warctools.WarcRecord.DATE).next()
            url = (v for k, v in target_headers if k == warctools.WarcRecord.URL).next()
            self.write_warc_metadata_record(metadata, url, concurrent_to, warc_date, out)

        # write PDF capture
        if asset.pdf_capture and ('cap' in asset.pdf_capture or 'upload' in asset.pdf_capture):
            file_path = os.path.join(asset.base_storage_path, asset.pdf_capture)
            headers = write_resource_record(file_path, "file:///%s/%s" % (guid, asset.pdf_capture), 'application/pdf')
            #write_metadata_record({'role':'primary', 'user_upload':asset.user_upload}, headers)

        # write image capture (if it's not a PDF thumbnail)
        elif (asset.image_capture and ('cap' in asset.image_capture or 'upload' in asset.image_capture)):
            file_path = os.path.join(asset.base_storage_path, asset.image_capture)
            mime_type = get_mime_type(asset.image_capture)
            write_resource_record(file_path, "file:///%s/%s" % (guid, asset.image_capture), mime_type)

        if asset.warc_capture:
            # write WARC capture
            if asset.warc_capture == 'archive.warc.gz':
                file_path = os.path.join(asset.base_storage_path, asset.warc_capture)
                self.write_warc_raw_data(default_storage.open(file_path), out)

            # write wget capture
            elif asset.warc_capture == 'source/index.html':
                mime = MimeTypes()
                for root, dirs, files in default_storage.walk(os.path.join(asset.base_storage_path, 'source')):
                    rel_path = root.split(asset.base_storage_path, 1)[-1]
                    for file_name in files:
                        mime_type = mime.guess_type(file_name)[0]
                        write_resource_record(os.path.join(root, file_name),
                                              "file:///%s%s/%s" % (guid, rel_path, file_name), mime_type)

        self.close_warc_after_writing(out)

        # regenerate CDX index
        self.cdx_lines.all().delete()

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

    def playback_url(self):
        if not self.url:
            return None
        return u"%s%s%s" % (self.link.base_playback_url(), "id_/" if self.record_type == 'resource' else "", self.url)


class Asset(models.Model):
    """
    Our archiving logic generates a bunch of different assets. We store those on disk. We use
    this class to track those locations.
    """
    link = models.ForeignKey(Link, null=False, related_name='assets')
    base_storage_path = models.CharField(max_length=2100, null=True, blank=True)  # where we store these assets, relative to some base in our settings
    favicon = models.CharField(max_length=2100, null=True, blank=True)  # Retrieved favicon
    image_capture = models.CharField(max_length=2100, null=True, blank=True)  # Headless browser image capture
    warc_capture = models.CharField(max_length=2100, null=True, blank=True)  # source capture
    pdf_capture = models.CharField(max_length=2100, null=True, blank=True)  # We capture a PDF version (through a user upload or through our capture)

    user_upload = models.BooleanField(
        default=False)  # whether the user uploaded this file or we fetched it from the web
    user_upload_file_name = models.CharField(max_length=2100, null=True, blank=True)  # if user upload, the original file name of the upload

    tracker = FieldTracker()

    CAPTURE_STATUS_PENDING = 'pending'
    CAPTURE_STATUS_FAILED = 'failed'

    def __init__(self, *args, **kwargs):
        super(Asset, self).__init__(*args, **kwargs)
        if self.link_id and not self.base_storage_path:
            self.base_storage_path = self.link.generate_storage_path()

    def base_url(self, extra=u""):
        return "%s/%s" % (self.base_storage_path, extra)

    def favicon_url(self):
        return self.base_url(self.favicon)

    def resource_url(self, url):
        return "id_/file:///%s/%s" % (self.link_id, url)

    def image_url(self):
        return self.resource_url(self.image_capture)

    def pdf_url(self):
        return self.resource_url(self.pdf_capture)

    def warc_url(self):
        if self.warc_capture and self.warc_capture=='archive.warc.gz':
            return self.link.submitted_url
        else:
            return self.resource_url(self.warc_capture)

    def warc_download_url(self):
        if '.warc' in self.warc_capture:
            return self.base_url(self.warc_capture)
        return None


#########################
# Stats related models
#########################

class Stat(models.Model):
    """
    We have a stats page. A sort of dashboard that displays aggregate counts on users
    and storage space and whatever the heck else might be fun to look at.

    We compute an aggregate count nightly (or whenever we set our celery periodic task to run)
    """

    # The time of this stats entry
    creation_timestamp = models.DateTimeField(auto_now_add=True)

    # Our user counts
    regular_user_count = models.IntegerField(default=1)
    org_member_count = models.IntegerField(default=1)
    org_manager_count = models.IntegerField(default=1)  # keeping this for legacy counts, doesn't mean anything
    registrar_member_count = models.IntegerField(default=1)
    registry_member_count = models.IntegerField(default=1)

    # Our org count
    org_count = models.IntegerField(default=1)

    # Our registrar count
    registrar_count = models.IntegerField(default=1)

    # Our link counts
    unvested_count = models.IntegerField(default=1)
    vested_count = models.IntegerField(default=1)
    darchive_takedown_count = models.IntegerField(default=0)
    darchive_robots_count = models.IntegerField(default=0)    

    # Our google analytics counts
    global_uniques = models.IntegerField(default=1)

    # Our size count
    disk_usage = models.FloatField(default=0.0)

    # TODO, we also display the top 10 perma links in the stats view
    # we should probably generate these here or put them in memcache or something


class CDXLineManager(models.Manager):
    def create_all_from_link(self, link):
        warc_path = link.warc_storage_file()
        with default_storage.open(warc_path, 'rb') as warc_file, io.BytesIO() as cdx_io:
            write_cdx_index(cdx_io, warc_file, warc_path)
            cdx_io.seek(0)
            next(cdx_io) # first line is a header so skip it
            results = [CDXLine.objects.get_or_create(link=link, raw=line)[0] for line in cdx_io]

        return results


class CDXLine(models.Model):
    link = models.ForeignKey(Link, null=True, related_name='cdx_lines')
    asset = models.ForeignKey(Asset, null=True, related_name='cdx_lines')
    urlkey = models.CharField(max_length=2100, null=False, blank=False)
    raw = models.TextField(null=False, blank=False)

    objects = CDXLineManager()

    def __init__(self, *args, **kwargs):
        super(CDXLine, self).__init__(*args, **kwargs)
        if self.raw:
            self.__set_defaults()

    @cached_property
    def __parsed(self):
        return CDXObject(self.raw)

    def __set_defaults(self):
        if not self.urlkey:
            self.urlkey = self.__parsed['urlkey']

    @cached_property
    def timestamp(self):
        return self.__parsed['timestamp']

    def is_revisit(self):
        return self.__parsed.is_revisit()


