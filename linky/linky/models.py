from datetime import datetime

from linky.lib import hashids

from django.contrib.auth.models import User
from django.db import models



class Links(models.Model):
    submitted_url = models.URLField(max_length=2100, null=False, blank=False)
    creation_time = models.DateTimeField(auto_now=True)
    vetted = models.BooleanField(initial=False)
    hash_id = models.CharField(max_length=100, unique=True) # Should we store this? For backup reasons?

    def save(self, *args, **kwargs):
        # We compute our hash from our auto
        #
        # TODO: We're getting a link count each time. Find a better hashing mechanism
        # or toss this in memcache or ???
        
        links_count = Links.objects.count()
        
        hashids_lib = hashids('get salt from config file here')
        computed_hash = hashids_lib.encrypt(links_count)

        self.hash_id = computed_hash
        super(Links, self).save(*args, **kwargs)


    def __unicode__(self):
        return self.submitted_url