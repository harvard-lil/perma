from datetime import datetime
import logging

from lib.hashids import hashids

from django.contrib.auth.models import User, Permission, Group
from django.db.models.signals import post_syncdb
from django.contrib.contenttypes.models import ContentType
from django.db import models

logger = logging.getLogger(__name__)

try:
    from linky.local_settings import *
except ImportError, e:
    logger.error('Unable to load local_settings.py:', e)

class Journal(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=400)
    journal_logo = models.URLField(max_length=2100, null=False, blank=False)

    def __unicode__(self):
        return self.name

class Link(models.Model):
    submitted_url = models.URLField(max_length=2100, null=False, blank=False)
    creation_time = models.DateTimeField(auto_now=True)
    submitted_title = models.CharField(max_length=2100, null=False, blank=False)
    vestted = models.BooleanField(default=False)
    vestted_by_editor = models.ForeignKey(User, null=True, blank=True)
    vestted_timestamp = models.DateTimeField(null=True, blank=True)
    vestted_by_journal = models.ForeignKey(Journal, null=True, blank=True)
    hash_id = models.CharField(max_length=100, unique=True) # Should we store this? For backup reasons?

    def save(self, *args, **kwargs):
        # We compute our hash from our auto
        #
        # TODO: We're getting a link count each time. Find a better hashing mechanism
        # or toss this in memcache or ???
        
        link_count = Link.objects.count()
        
        hashids_lib = hashids(INTERNAL['SALT'])
        computed_hash = hashids_lib.encrypt(link_count)

        self.hash_id = computed_hash
        super(Link, self).save(*args, **kwargs)


    def __unicode__(self):
        return self.submitted_url
        

# Non-model stuff

def add_groups_and_permissions(sender, **kwargs):
    """
    This syncdb hook adds our permissions and our groups
    """
    
    # All possible perms in linky
    initial_perms = [{
        "codename": "can_vest",
        "name": "Can vest Linky Links"
        },
        {
            "codename": "can_create_editors",
            "name": "Can create editors"
        },
        {
            "codename": "can_deactivate_editors",
            "name": "Can deactivate editors"
        },
        {
            "codename": "can_create_journals",
            "name": "Can create journals"
        },
        {
            "codename": "can_deactivate_journals",
            "name": "Can deactivate journals"
        },
        {
            "codename": "can_create_librarians",
            "name": "Can create librarians"
        },
        {
            "codename": "can_deactivate_librarians",
            "name": "Can deactivate librarians"
        },
        {
            "codename": "can_deactivate_linky_links",
            "name": "Can deactivate linky links"
        }]
    
    # Add our groups
    initial_groups = [
    {
        "model": "auth.group",
        "fields": {
            "name": "linky_admin"
        },
        "perms": [{
            "codename": "can_vest"
        }]
    },
    {
        "model": "auth.group",
        "fields": {
            "name": "librarian"
        },
        "perms": [{
            "codename": "can_vest"
        },
        {
            "codename": "can_create_editors"
        },
        {
            "codename": "can_deactivate_editors"
        }]
    },
    {
        "model": "auth.group",
        "fields": {
            "name": "managing_editor"
        },
        "perms": [{
            "codename": "can_vest"
        },
        {
            "codename": "can_create_editors"
        },
        {
            "codename": "can_deactivate_editors"
        },
        {
            "codename": "can_create_journals"
        }]
    },
    {
        "model": "auth.group",
        "fields": {
            "name": "editor"
        },
        "perms": [{
            "codename": "can_vest"
        },
        {
            "codename": "can_create_editors"
        },
        {
            "codename": "can_deactivate_editors"
        },
        {
            "codename": "can_create_journals"
        },
        {
            "codename": "can_create_journals"
        },
        {
            "codename": "can_create_librarians"
        },
        {
            "codename": "can_deactivate_librarians"
        },
        {
            "codename": "can_deactivate_linky_links"
        }]
    }]
    
    existing_perms = Permission.objects.filter()

    if not existing_perms:
        # We need a content_type for our perms. We'll use link for now, but this isn't right
        content_type = ContentType.objects.get_for_model(Link)
        
        for initial_perm in initial_perms:
            Permission.objects.create(content_type=content_type, codename=initial_perm['codename'], name=initial_perm['name'])        


    existing_groups = Group.objects.filter()
    
    if not existing_groups:    
        for initial_group in initial_groups:
            group = Group.objects.create(name=initial_group['fields']['name'])
            if 'perms' in initial_group:
                for group_perm in initial_group['perms']:
                    perm = Permission.objects.get(codename=group_perm['codename'])
                    group.permissions.add(perm)
                    group.save()

        
# load groups and permissions
post_syncdb.connect(add_groups_and_permissions)