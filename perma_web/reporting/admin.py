from django.contrib import admin
from django.db.models import Count

from perma.admin import RegistrarAdmin

from reporting.models import FederalCourt

class FederalCourtAdmin(RegistrarAdmin):
    list_display = ['name', 'last_active', 'registrar_users', 'org_users', 'orgs_count', 'link_count']
    list_editable = []
    list_filter = []
    ordering = ['manual_sort_order']
    fieldsets = (
        (None, {'fields': ('name', 'email', 'website', 'orgs_private_by_default')}),
        ("Internal", {'fields': ('manual_sort_order',)}),
    )

    # additional statistics
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            org_users=Count('organizations__users')
        )

    def org_users(self, obj):
        return obj.org_users

admin.site.register(FederalCourt, FederalCourtAdmin)
