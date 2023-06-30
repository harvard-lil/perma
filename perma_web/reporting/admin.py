from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from perma.admin import RegistrarAdmin

from reporting.models import FederalCourt


class FederalCourtAdmin(RegistrarAdmin):
    list_display = ['name', 'last_active', 'get_registrar_users', 'org_users_total', 'org_users_distinct', 'orgs', 'link_count']
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
            org_user_total=Count('organizations__users'),
            org_user_distinct=Count('organizations__users', distinct=True)
        )

    def get_registrar_users(self, obj):
        base_url = reverse("admin:perma_linkuser_changelist")
        return format_html('<a href="{}?registrar_id={}">{}</a>', base_url, obj.id, obj.registrar_users)
    get_registrar_users.short_description = 'registrar users'

    def org_users_total(self, obj):
        base_url = reverse("admin:perma_linkuser_changelist")
        return format_html('<a href="{}?org_user_for_registrar_id={}">{}</a>', base_url, obj.id, obj.org_user_total)
    org_users_total.short_description = 'org users (total)'

    def org_users_distinct(self, obj):
        base_url = reverse("admin:perma_linkuser_changelist")
        return format_html('<a href="{}?org_user_for_registrar_id={}">{}</a>', base_url, obj.id, obj.org_user_distinct)
    org_users_distinct.short_description = 'org users (distinct)'

    def orgs(self, obj):
        base_url = reverse("admin:perma_organization_changelist")
        return format_html('<a href="{}?registrar_id={}">{}</a>', base_url, obj.id, obj.orgs_count)


admin.site.register(FederalCourt, FederalCourtAdmin)
