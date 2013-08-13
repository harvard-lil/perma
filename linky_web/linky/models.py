from datetime import datetime
import logging

from django.contrib.auth.models import User, Permission, Group
from django.db.models.signals import post_syncdb
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

try:
    from linky.local_settings import *
except ImportError, e:
    logger.error('Unable to load local_settings.py: %s', e)


class Registrar(models.Model):
    """ This is generally a library. """
    name = models.CharField(max_length=400)
    email = models.EmailField(max_length=254)
    website = models.URLField(max_length=500)

    def __unicode__(self):
        return self.name

####################################
# Extending Django's user
# This is something we'll rework when we upgrage to 1.5
####################################
class UserProfile(models.Model):
    user = models.OneToOneField(User)
    registrar = models.ForeignKey(Registrar, null=True)
    
    def __str__(self):  
          return "%s's profile" % self.user  

def create_user_profile(sender, instance, created, **kwargs):  
    if created:  
       profile, created = UserProfile.objects.get_or_create(user=instance)  

post_save.connect(create_user_profile, sender=User)

####################################
# End of user profile stuff
####################################

class Link(models.Model):
    submitted_url = models.URLField(max_length=2100, null=False, blank=False)
    creation_timestamp = models.DateTimeField(auto_now=True)
    submitted_title = models.CharField(max_length=2100, null=False, blank=False)
    created_by = models.ForeignKey(User, null=True, blank=True, related_name='created_by',)
    vested = models.BooleanField(default=False)
    vested_by_editor = models.ForeignKey(User, null=True, blank=True, related_name='vested_by_editor')
    vested_timestamp = models.DateTimeField(null=True, blank=True)

    
    """def save(self, *args, **kwargs):
        # We compute our hash from our auto
        #
        # TODO: We're getting a link count each time. Find a better hashing mechanism
        # or toss this in memcache or ???
        
        link_count = Link.objects.count()
        
        hashids_lib = hashids(INTERNAL['SALT'])
        computed_hash = hashids_lib.encrypt(link_count)

        self.hash_id = computed_hash
        super(Link, self).save(*args, **kwargs)"""
        
    def __unicode__(self):
        return self.submitted_url

class Asset(models.Model):
    """ We use this to track our generated assets, per link """
    link = models.ForeignKey(Link, null=False)
    base_storage_path = models.CharField(max_length=2100, null=True, blank=True) # where we store these assets, relative to some base in our settings
    favicon = models.CharField(max_length=2100, null=True, blank=True) # Retrieved favicon
    image_capture = models.CharField(max_length=2100, null=True, blank=True) # Headless browser image capture
    warc_capture = models.CharField(max_length=2100, null=True, blank=True) # Heretrix capture


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