from datetime import datetime
import logging
import random

from django.contrib.auth.models import User, Permission, Group
from django.db.models.signals import post_syncdb
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)

from linky.utils import base

logger = logging.getLogger(__name__)


class Registrar(models.Model):
    """
    This is generally a library.
    """
    name = models.CharField(max_length=400)
    email = models.EmailField(max_length=254)
    website = models.URLField(max_length=500)

    def __unicode__(self):
        return self.name


class LinkUserManager(BaseUserManager):
    def create_user(self, email, registrar, date_joined, first_name, last_name, authorized_by, confirmation_code, password=None, groups=None):
        """
        Creates and saves a User with the given email, registrar and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            registrar=registrar,
            groups=groups,
            date_joined = date_joined,
            first_name = first_name,
            last_name = last_name,
            authorized_by = authorized_by,
            confirmation_code = confirmation_code
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, registrar, password, groups, date_joined, first_name, last_name, authorized_by, confirmation_code):
        """
        Creates and saves a superuser with the given email, registrar and password.
        """
        user = self.create_user(email,
            password=password,
            registrar=registrar,
            groups=groups,
            date_joined = date_joined,
            first_name = first_name,
            last_name = last_name,
            authorized_by = authorized_by,
            confirmation_code = confirmation_code
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class LinkUser(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        db_index=True,
    )
    registrar = models.ForeignKey(Registrar, null=True)
    groups = models.ManyToManyField(Group, null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateField(auto_now_add=True)
    first_name = models.CharField(max_length=45, blank=True)
    last_name = models.CharField(max_length=45, blank=True)
    authorized_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='authorized_by_manager')
    confirmation_code = models.CharField(max_length=45, blank=True)

    objects = LinkUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    # On Python 3: def __str__(self):
    def __unicode__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

class Link(models.Model):
    """
    This is the core of the Perma link.
    """
    guid = models.CharField(max_length=255, null=False, blank=False, primary_key=True)
    view_count = models.IntegerField(default=0)
    submitted_url = models.URLField(max_length=2100, null=False, blank=False)
    creation_timestamp = models.DateTimeField(auto_now=True)
    submitted_title = models.CharField(max_length=2100, null=False, blank=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='created_by',)
    vested = models.BooleanField(default=False)
    vested_by_editor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='vested_by_editor')
    vested_timestamp = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        To generate our globally unique identifiers, we draw a number out of a large number space,
        58^10. We convert that to base58 (like base64, but without the confusing I,1,O,0 characters.
        so that our URL is short(ish). And we append a 0. This 0 is
        a way to namespace identifiers created at this Perma creation source.
        """
        if not self.pk:
            # not self.pk => not created yet
            guid = '0'
            while guid.startswith('0'):
                random_id = random.randint(0, 58**10)
                guid = base.convert(random_id, base.BASE10, base.BASE58)
            guid = '0' + guid
            self.guid = guid
        super(Link, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.submitted_url

class Asset(models.Model):
    """
    Our archving logic generates a bung of different assets. We store those on disk. We use
    this class to track those locations.
    """
    link = models.ForeignKey(Link, null=False)
    base_storage_path = models.CharField(max_length=2100, null=True, blank=True) # where we store these assets, relative to some base in our settings
    favicon = models.CharField(max_length=2100, null=True, blank=True) # Retrieved favicon
    image_capture = models.CharField(max_length=2100, null=True, blank=True) # Headless browser image capture
    warc_capture = models.CharField(max_length=2100, default='pending', null=True, blank=True) # Heretrix capture
    instapaper_timestamp = models.DateTimeField(null=True)
    instapaper_cap = models.TextField(null=True)
    instapaper_hash = models.CharField(max_length=2100, null=True)
    instapaper_id = models.IntegerField(null=True)


#######################
# Non-model stuff
#######################
def add_groups_and_permissions(sender, **kwargs):
    """
    This syncdb hook adds our our groups
    """

    # Add our groups
    initial_groups = [
    {
        "model": "auth.group",
        "fields": {
            "name": "user"
        },
    },
    {
        "model": "auth.group",
        "fields": {
            "name": "journal_member"
        },
    },
    {
        "model": "auth.group",
        "fields": {
            "name": "registrar_member"
        },
    },
    {
        "model": "auth.group",
        "fields": {
            "name": "registry_member"
        },
    }]

    existing_groups = Group.objects.filter()

    if not existing_groups:
        for initial_group in initial_groups:
            group = Group.objects.create(name=initial_group['fields']['name'])


# load groups and permissions
post_syncdb.connect(add_groups_and_permissions)
