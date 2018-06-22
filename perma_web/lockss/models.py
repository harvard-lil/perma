from django.db import models
from django.core.cache import cache as django_cache


class Mirror(models.Model):
    name = models.CharField(max_length=255)
    ip = models.CharField(max_length=15, help_text="E.g. 12.34.56.78")
    hostname = models.CharField(max_length=255, help_text="E.g. mirror.example.com")
    peer_port = models.IntegerField(default=9729, help_text="Port where this mirror listens for other LOCKSS nodes.")
    content_url = models.URLField(max_length=255, help_text="E.g. https://mirror.example.edu:8080/")
    enabled = models.BooleanField(default=True)

    class Meta(object):
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(Mirror, self).save(*args, **kwargs)
        self._invalidate_cached_mirrors()

    def delete(self, *args, **kwargs):
        super(Mirror, self).delete(*args, **kwargs)
        self._invalidate_cached_mirrors()

    @classmethod
    def get_cached_mirrors(cls):
        """
            Get a list of {'name':,'content_url':,'ip':} dicts for each active mirror.
            Keep result in cache.
        """
        # get mirror list from cache
        mirrors = django_cache.get('mirrors')
        attrs = ('name', 'content_url', 'ip')
        if mirrors is None:
            mirrors = [dict((attr, getattr(mirror, attr)) for attr in attrs) for mirror in cls.objects.filter(enabled=True)]
            django_cache.set('mirrors', mirrors)

        # return mirrors
        if mirrors:
            return mirrors
        return []

    def _invalidate_cached_mirrors(self):
        django_cache.delete('mirrors')
