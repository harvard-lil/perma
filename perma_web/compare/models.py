from __future__ import unicode_literals
from django.db import models
from django.conf import settings

class Compare(models.Model):
    original_guid = models.CharField(max_length=255, null=False, blank=False, editable=False)
    guid = models.CharField(max_length=255, null=False, blank=False, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    image_diff = models.ImageField(upload_to='image_difss', blank=True, null=True)
    image_diff_thumb = models.ImageField(upload_to='image_diff_thumb', blank=True, null=True)
    #TODO: track our archived images since we'll do some resizing ()
    #old_image = models.ImageField(upload_to='resized_compares', blank=True, null=True)
    #new_image = models.ImageField(upload_to='resized_compares', blank=True, null=True)

# in diff app, create diff model,
# diff model: (new archive guid associated with original guid and user created)
# 	original archive
# 		timestamp ?
# 	new archive
# 		timestamp
# 	created_by
