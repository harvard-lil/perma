from django.contrib import admin

from .models import *


class MirrorAdmin(admin.ModelAdmin):
    name = models.CharField(max_length=255)
    ip = models.CharField(max_length=15, help_text="E.g. 12.34.56.78")
    hostname = models.CharField(max_length=255, help_text="E.g. mirror.example.com")
    peer_port = models.IntegerField(default=9729, help_text="Port where this mirror listens for other LOCKSS nodes.")
    content_url = models.URLField(max_length=255, help_text="E.g. https://mirror.example.edu:8080/")
    enabled = models.BooleanField(default=True)

    list_display = ['name', 'ip', 'hostname', 'content_url', 'enabled',]
    list_editable = ['ip', 'hostname', 'content_url', 'enabled',]


admin.site.register(Mirror, MirrorAdmin)
