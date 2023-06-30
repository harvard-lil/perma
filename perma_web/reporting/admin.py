from django.contrib import admin
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.html import format_html

from perma.admin import RegistrarAdmin, RegistrarNameFilter, RegistrarIdFilter

from reporting.models import FederalCourt, FederalCourtOrganization


RegistrarNameFilter.title = "Court/Registrar Name"
RegistrarIdFilter.title = "Court/Registrar ID"


class FederalCourtAdmin(RegistrarAdmin):
    list_display = ['name', 'last_active', 'get_registrar_users', 'org_users_total', 'org_users_distinct', 'orgs', 'orgs_total', 'link_count']
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
            org_user_distinct=Count('organizations__users', distinct=True),
            active_orgs_count=Count('organizations', filter=Q(organizations__user_deleted=False), distinct=True)

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
        base_url = reverse("admin:reporting_federalcourtorganization_changelist")
        return format_html('<a href="{}?registrar_id={}&user_deleted__exact=0">{}</a>', base_url, obj.id, obj.active_orgs_count)

    def orgs_total(self, obj):
        base_url = reverse("admin:reporting_federalcourtorganization_changelist")
        return format_html('<a href="{}?registrar_id={}">{}</a>', base_url, obj.id, obj.orgs_count)
    orgs_total.short_description = 'orgs (with deleted)'


class FederalCourtOrganizationAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['id', 'court', 'name', 'org_users', 'link_count']
    list_filter = [RegistrarNameFilter, RegistrarIdFilter, 'user_deleted']
    ordering = ['registrar__manual_sort_order', 'name']

    def court(self, obj):
        url = reverse("admin:reporting_federalcourt_change", args=(obj.registrar_id,))
        return format_html('<a href="{}">{}</a>', url, obj.registrar.name)
    court.short_description = 'Court/Registrar'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('registrar').annotate(
            org_users=Count('users'),
        )

    def org_users(self, obj):
        base_url = reverse("admin:perma_linkuser_changelist")
        return format_html('<a href="{}?org_id={}">{}</a>', base_url, obj.id, obj.org_users)



admin.site.register(FederalCourt, FederalCourtAdmin)
admin.site.register(FederalCourtOrganization, FederalCourtOrganizationAdmin)
