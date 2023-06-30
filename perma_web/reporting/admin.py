from django.contrib import admin
import csv
from datetime import date
from io import StringIO

from django.db.models import Count, Q
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html

from perma.admin import RegistrarAdmin, RegistrarNameFilter, RegistrarIdFilter

from reporting.models import FederalCourt, FederalCourtOrganization

RegistrarNameFilter.title = "Court/Registrar Name"
RegistrarIdFilter.title = "Court/Registrar ID"


###
# CSV Helpers
###

MAX_CSV_RESULTS = 1_000
CSV_PARAM = '_csv'

class CsvPlaceholderFilter(admin.SimpleListFilter):
    """
    Admin views that use the CsvResponseMixin check the request query string for
    CSV_PARAM, and if present, ouput a CSV instead of the standard HTML view.

    Django interprets the CSV_PARAM as a filter, raises IncorrectLookupParameters
    unless one is present. So, we provide this no-op, hidden filter.

    Thanks https://stackoverflow.com/a/68550839!
    """
    parameter_name = CSV_PARAM
    title = ''

    # hide from filter pane
    def has_output(self):
        return False

    # these two function below must be implemented for SimpleListFilter to work
    # (any implementation that doesn't affect queryset is fine)
    def lookups(self, request, model_admin):
        return (request.GET.get(self.parameter_name), ''),

    def queryset(self, request, queryset):
        return queryset


class CsvResponseMixin():
    try:
        list_filter = list_filter.append(CsvPlaceholderFilter)
    except NameError:
        list_filter = [CsvPlaceholderFilter]

    @property
    def field_list(self):
        """Return a list of fields to be included in the CSV output for this class"""
        return []

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['csv_param'] = CSV_PARAM

        if CSV_PARAM in request.GET:

            qs = self.get_queryset(request)[:MAX_CSV_RESULTS]

            output = StringIO()
            export = [[field[0] for field in self.csv_field_list]]
            for obj in qs:
                row = [str(getattr(obj, field[1])) for field in self.csv_field_list]
                export.append(row)
            csv.writer(output).writerows(export)
            return self.csv_response(output)

        return super().changelist_view(request, extra_context)


    def csv_response(self, output_rows):
        """Return a response object of type CSV given a datastructure of rows of string output"""
        return HttpResponse(
            output_rows.getvalue().encode(),
            headers={
                "Content-Type": "text/csv",
                "Content-Disposition": f'attachment; filename="{self.model._meta.model_name}-{date.today().isoformat()}.csv',
            },
        )


class FederalCourtAdmin(CsvResponseMixin, RegistrarAdmin):
    list_display = ['name', 'last_active', 'get_registrar_users', 'org_users_total', 'org_users_distinct', 'orgs', 'orgs_total', 'link_count']
    list_editable = []
    ordering = ['manual_sort_order']
    fieldsets = (
        (None, {'fields': ('name', 'email', 'website', 'orgs_private_by_default')}),
        ("Internal", {'fields': ('manual_sort_order',)}),
    )

    @property
    def csv_field_list(self):
        return [
            ('Name', 'name'),
            ('Last Active', 'last_active'),
            ('Registrar Users', 'registrar_users'),
            ('Org Users (Total)', 'org_user_total'),
            ('Org Users (Distinct)', 'org_user_distinct'),
            ('Orgs', 'active_orgs_count'),
            ('Orgs (With Deleted)', 'orgs_count'),
            ('Link Count', 'link_count')
        ]

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


class FederalCourtOrganizationAdmin(CsvResponseMixin, admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['id', 'court', 'name', 'org_users', 'link_count']
    list_filter = [RegistrarNameFilter, RegistrarIdFilter, 'user_deleted']
    ordering = ['registrar__manual_sort_order', 'name']

    @property
    def csv_field_list(self):
        return [
            ('ID', 'id'),
            ('Court', 'registrar'),
            ('Name', 'name'),
            ('Org Users', 'org_users'),
            ('Link Count', 'link_count')
        ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('registrar').annotate(
            org_users=Count('users'),
        )

    def court(self, obj):
        url = reverse("admin:reporting_federalcourt_change", args=(obj.registrar_id,))
        return format_html('<a href="{}">{}</a>', url, obj.registrar.name)
    court.short_description = 'Court/Registrar'

    def org_users(self, obj):
        base_url = reverse("admin:perma_linkuser_changelist")
        return format_html('<a href="{}?org_id={}">{}</a>', base_url, obj.id, obj.org_users)



admin.site.register(FederalCourt, FederalCourtAdmin)
admin.site.register(FederalCourtOrganization, FederalCourtOrganizationAdmin)
