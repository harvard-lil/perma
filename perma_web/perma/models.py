import io
import os
import logging
import random
import re
import socket
from urlparse import urlparse
import requests

from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.functional import cached_property
from mptt.models import MPTTModel, TreeForeignKey
from model_utils import FieldTracker
from pywb.cdx.cdxobject import CDXObject
from pywb.warc.cdxindexer import write_cdx_index


logger = logging.getLogger(__name__)


class Registrar(models.Model):
    """
    This is generally a library.
    """
    name = models.CharField(max_length=400)
    email = models.EmailField(max_length=254)
    website = models.URLField(max_length=500)
    date_created = models.DateField(auto_now_add=True, null=True)
    organization = models.OneToOneField('Organization', blank=True, null=True, related_name='default_for_registrars') # each registrar gets a default org
    is_approved = models.BooleanField(default=False)

    # what info to send downstream
    mirror_fields = ('name', 'email', 'website')

    tracker = FieldTracker()

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
        
        if self.default_organization:
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
    shared_folder = models.OneToOneField('Folder', blank=True, null=True)
    date_created = models.DateField(auto_now_add=True, null=True)

    # what info to send downstream
    mirror_fields = ('name', 'registrar')

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
            if self.created_by and not self.owned_by and not self.organization
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

    # what info to send downstream
    mirror_fields = ('guid', 'submitted_url', 'creation_timestamp', 'submitted_title', 'dark_archived',
                     'dark_archived_robots_txt_blocked', 'user_deleted', 'user_deleted_timestamp',
                     'vested', 'vested_timestamp', 'organization')

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
        if self.headers.get('content-type', None) in ['application/pdf', 'application/x-pdf'] or self.submitted_url.endswith('.pdf'):
            return 'pdf'
        else:
            return False

    def save(self, *args, **kwargs):
        # Set a default title if one is missing
        if not self.submitted_title:
            self.submitted_title = self.url_details.netloc

        initial_folder = kwargs.pop('initial_folder', None)

        if not self.pk and not kwargs.get("pregenerated_guid", False):
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
        if "pregenerated_guid" in kwargs:
            del kwargs["pregenerated_guid"]

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

    def generate_storage_path(self):
        """
            Generate the path where assets for this link should be stored.
        """
        if not self.guid:
            raise Exception("Can only generate storage path after link is saved.")
        creation_date = self.creation_timestamp
        return "/".join(str(x) for x in [creation_date.year, creation_date.month, creation_date.day, creation_date.hour, creation_date.minute, self.guid])

    def get_expiration_date(self):
        """ Return date when this link will theoretically be deleted. """
        return self.creation_timestamp + settings.LINK_EXPIRATION_TIME

    def can_upload_to_internet_archive(self):
        """ Return True if this link is appropriate for upload to IA. """
        return self.vested \
               and not self.dark_archived and not self.dark_archived_robots_txt_blocked \
               and self.assets.filter(warc_capture__contains='.warc').exists()

    def as_json(self, request=None):
        from api.resources import LinkResource
        return LinkResource().as_json(self, request)


class Asset(models.Model):
    """
    Our archiving logic generates a bunch of different assets. We store those on disk. We use
    this class to track those locations.
    """
    link = models.ForeignKey(Link, null=False, related_name='assets')
    base_storage_path = models.CharField(max_length=2100, null=True, blank=True)  # where we store these assets, relative to some base in our settings
    favicon = models.CharField(max_length=2100, null=True, blank=True)  # Retrieved favicon
    image_capture = models.CharField(max_length=2100, null=True, blank=True)  # Headless browser image capture
    warc_capture = models.CharField(max_length=2100, null=True, blank=True)  # source capture, probably point to an index.html page
    pdf_capture = models.CharField(max_length=2100, null=True, blank=True)  # We capture a PDF version (through a user upload or through our capture)

    user_upload = models.BooleanField(
        default=False)  # whether the user uploaded this file or we fetched it from the web
    user_upload_file_name = models.CharField(max_length=2100, null=True, blank=True)  # if user upload, the original file name of the upload

    last_integrity_check = models.DateTimeField(blank=True, null=True)  # for a mirror server, the last time our disk assets were checked against upstream
    integrity_check_succeeded = models.NullBooleanField(blank=True, null=True)      # whether the last integrity check succeeded

    # what info to send downstream
    mirror_fields = ('link', 'base_storage_path', 'image_capture', 'warc_capture', 'pdf_capture', 'favicon')

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

    def image_url(self):
        return self.base_url(self.image_capture)

    def warc_url(self, host=settings.WARC_HOST):
        if self.warc_capture and '.warc' in self.warc_capture:
            return ("//"+host if host else '') + \
                   u"/warc/%s/%s" % (self.link.guid, self.link.submitted_url)
        else:
            return settings.MEDIA_URL+self.base_url(self.warc_capture)

    def warc_download_url(self):
        if '.warc' in self.warc_capture:
            return self.base_url(self.warc_capture)
        return None

    def pdf_url(self):
        return self.base_url(self.pdf_capture)

    def walk_files(self):
        """ Return iterator of all files for this asset. """
        return default_storage.walk(self.base_storage_path)

    def verify_media(self):
        if settings.MIRROR_SERVER:
            from mirroring.tasks import background_media_sync
            urls = []
            if self.image_capture and '.png' in self.image_capture:
                urls.append(self.base_url(self.image_capture))
            if self.pdf_capture and '.pdf' in self.pdf_capture:
                urls.append(self.base_url(self.pdf_capture))
            if self.warc_capture and '.warc' in self.warc_capture:
                urls.append(self.base_url(self.warc_capture))

            missing_urls = [url for url in urls if not default_storage.exists(url)]
            background_media_sync(paths=missing_urls)

            still_missing_urls = [url for url in missing_urls if not default_storage.exists(url)]
            if still_missing_urls:
                logger.error("Verifying media failed for %s: still missing %s." % (self.link_id, still_missing_urls))
                self.integrity_check_succeeded = False
            else:
                self.integrity_check_succeeded = True

            self.last_integrity_check = timezone.now()
            self.save()


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
    member_count = models.IntegerField(default=1)
    manager_count = models.IntegerField(default=1)
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
    def create_all_from_asset(self, asset):
        results = []
        warc_path = os.path.join(asset.base_storage_path, asset.warc_capture)
        with default_storage.open(warc_path, 'rb') as warc_file, io.BytesIO() as cdx_io:
            write_cdx_index(cdx_io, warc_file, warc_path)
            cdx_io.seek(0)
            next(cdx_io) # first line is a header so skip it
            for line in cdx_io:
                results.append(CDXLine.objects.get_or_create(asset=asset, raw=line)[0])

        return results


class CDXLine(models.Model):
    urlkey = models.URLField(max_length=2100, null=False, blank=False)
    raw = models.TextField(null=False, blank=False)
    asset = models.ForeignKey(Asset, null=False, blank=False, related_name='cdx_lines')
    objects = CDXLineManager()

    def __init__(self, *args, **kwargs):
        super(CDXLine, self).__init__(*args, **kwargs)
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


### read only mode ###

# install signals to prevent database writes if settings.READ_ONLY_MODE is set

### this is in models for now because it's annoying to put it in signals.py and resolve circular imports with models.py
### in Django 1.8 we can avoid that issue by putting this in signals.py and importing it from ready()
### https://docs.djangoproject.com/en/dev/topics/signals/

from django.contrib.sessions.models import Session
from django.db.models.signals import pre_save

from .utils import ReadOnlyException

write_whitelist = (
    (Session, None),
    (LinkUser, {'password'}),
    (LinkUser, {'last_login'}),
)

def read_only_mode(sender, instance, **kwargs):
    for whitelist_sender, whitelist_fields in write_whitelist:
        if whitelist_sender==sender and (whitelist_fields is None or whitelist_fields==kwargs['update_fields']):
            return
    raise ReadOnlyException("Read only mode enabled.")

if settings.READ_ONLY_MODE:
    pre_save.connect(read_only_mode)
