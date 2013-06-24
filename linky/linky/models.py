from datetime import datetime
import logging

from lib.hashids import hashids

from django.contrib.auth.models import User
from django.db import models

logger = logging.getLogger(__name__)

try:
    from linky.local_settings import *
except ImportError, e:
    logger.error('Unable to load local_settings.py:', e)

class Publication(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=400)

    def __unicode__(self):
        return self.name

class Link(models.Model):
    submitted_url = models.URLField(max_length=2100, null=False, blank=False)
    creation_time = models.DateTimeField(auto_now=True)
    submitted_title = models.CharField(max_length=2100, null=False, blank=False)
    vetted = models.BooleanField(default=False)
    vetted_by_editor = models.ForeignKey(User, null=True, blank=True)
    vetted_timestamp = models.DateTimeField(null=True, blank=True)
    vetted_by_publication = models.ForeignKey(Publication, null=True, blank=True)
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