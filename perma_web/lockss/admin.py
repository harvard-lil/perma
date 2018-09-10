from django.contrib import admin

from .models import Mirror


class MirrorAdmin(admin.ModelAdmin):

    list_display = ['name', 'ip', 'hostname', 'content_url', 'enabled',]
    list_editable = ['ip', 'hostname', 'content_url', 'enabled',]


admin.site.register(Mirror, MirrorAdmin)
