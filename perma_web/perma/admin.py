from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import connection
from django.db.models.functions import Upper
from django.db.models import Count, Max, Q
from django.db.models.sql.where import WhereNode
from django.forms import ModelForm
from django.template.defaultfilters import filesizeformat
from django.utils.functional import cached_property
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from simple_history.admin import SimpleHistoryAdmin
from django_json_widget.widgets import JSONEditorWidget

from .exceptions import PermaPaymentsCommunicationException
from .models import Folder, Registrar, Organization, LinkUser, CaptureJob, Link, Capture, \
    LinkBatch, Sponsorship, InternetArchiveItem, InternetArchiveFile

### helpers ###

def new_class(name, *args, **kwargs):
    return type(name, args, kwargs)

### filters ###

class InputFilter(admin.SimpleListFilter):
    """
    Text input filter, from:
    https://hakibenita.com/how-to-add-a-text-filter-to-django-admin
    """
    template = 'admin/input_filter.html'

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return ((),)

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice


class SubmittedURLFilter(InputFilter):
    parameter_name = 'submitted_url'
    title = 'submitted URL'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(submitted_url__icontains=value)


class CreatedByFilter(InputFilter):
    parameter_name = 'created_by'
    title = 'user email'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(created_by__email__icontains=value)

class OrganizationFilter(InputFilter):
    parameter_name = 'organization_id'
    title = 'owning organization id'

    def queryset(self, request, queryset):
        try:
            value = int(self.value())
        except (ValueError, TypeError):
            value = None
        if value:
            return queryset.filter(organization=value)

class GUIDFilter(InputFilter):
    parameter_name = 'guid'
    title = 'GUID'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(guid__icontains=value).order_by(Upper('guid'))


class LinkIDFilter(InputFilter):
    parameter_name = 'guid'
    title = 'GUID'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(link__guid__icontains=value)


class ScoopJobIDFilter(InputFilter):
    parameter_name = 'scoop_job_id'
    title = 'Scoop Job ID'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(scoop_job_id=value)


class TagFilter(InputFilter):
    parameter_name = 'tag'
    title = 'tag'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(tags__name__icontains=value)

class LinkTagFilter(InputFilter):
    parameter_name = 'linktag'
    title = 'link tag'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(link__tags__name__icontains=value)


class MessageFilter(InputFilter):
    parameter_name = 'message'
    title = 'message'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(message__icontains=value)


class OwnerFilter(InputFilter):
    parameter_name = 'owner'
    title = 'owned by (email)'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(owned_by__email__icontains=value)


class OrgFilter(InputFilter):
    parameter_name = 'org'
    title = 'owned by (org)'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(organization__name__icontains=value)


class NameFilter(InputFilter):
    parameter_name = 'name'
    title = 'name'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(name__icontains=value)


class RootFilter(InputFilter):
    parameter_name = 'root'
    title = 'root folder '

    def queryset(self, request, queryset):
        try:
            value = int(self.value())
        except (ValueError, TypeError):
            value = None
        if value:
            return queryset.filter(tree_root_id=value)


class IAIdentifierFilter(InputFilter):
    parameter_name = 'identifier'
    title = 'Identifier'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(identifier__icontains=value)


class IAItemFilter(InputFilter):
    parameter_name = 'item'
    title = 'IA Item'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(item_id=value)


class IALinkIDFilter(InputFilter):
    parameter_name = 'guid'
    title = 'GUID'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(link_id=value)


class IAItemTypeFilter(admin.SimpleListFilter):
    parameter_name = 'type'
    title = 'item type'

    def lookups(self, request, model_admin):
        return (
            ('individual', 'Individual'),
            ('daily', 'Daily'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'individual':
            return queryset.filter(span__isempty=True)
        elif value == 'daily':
            return queryset.filter(span__isempty=False)


class IAFileTypeFilter(admin.SimpleListFilter):
    parameter_name = 'type'
    title = 'item type'

    def lookups(self, request, model_admin):
        return (
            ('individual', 'Individual'),
            ('daily', 'Daily'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'individual':
            return queryset.filter(item__span__isempty=True)
        elif value == 'daily':
            return queryset.filter(item__span__isempty=False)


class IAFileHasMetadataFilter(admin.SimpleListFilter):
    parameter_name = 'metadata'
    title = 'Metadata Updated?'

    def lookups(self, request, model_admin):
        return (
            ('true', 'True'),
            ('false', 'False'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'true':
            return queryset.filter(cached_title__isnull=False)
        elif value == 'false':
            return queryset.filter(cached_title__isnull=True)

class IAItemHasTasksFilter(admin.SimpleListFilter):
    parameter_name = 'tasks_in_progress'
    title = 'has tasks in progress'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'yes':
            return queryset.exclude(tasks_in_progress=0)
        elif value == 'no':
            return queryset.filter(tasks_in_progress=0)


class RegistrarNameFilter(InputFilter):
    parameter_name = 'registrar_name'
    title = 'Registrar Name'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(registrar__name__icontains=value)


class RegistrarIdFilter(InputFilter):
    parameter_name = 'registrar_id'
    title = 'Registrar ID'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            try:
                value = int(value)
            except ValueError:
                return queryset.none()
            return queryset.filter(registrar__id=value)


class JobWithDeletedLinkFilter(admin.SimpleListFilter):
    parameter_name = 'link_deleted'
    title = 'link was deleted'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'yes':
            return queryset.filter(link__user_deleted=True)
        elif value == 'no':
            return queryset.filter(Q(link__isnull=True) | Q(link__user_deleted=False))


class OrgUserFilter(InputFilter):
    parameter_name = 'org_id'
    title = 'Org ID'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            try:
                value = int(value)
            except ValueError:
                return queryset.none()
            return queryset.filter(organizations__in=[value])


class OrgUserForRegistrarFilter(InputFilter):
    parameter_name = 'org_user_for_registrar_id'
    title = 'Org User for Registrar ID'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            try:
                value = int(value)
            except ValueError:
                return queryset.none()
            try:
                registrar = Registrar.objects.get(id=value)
            except Registrar.DoesNotExist:
                return queryset.none()
            return queryset.filter(organizations__in=registrar.organizations.all())


class RegistrarUserFilter(InputFilter):
    parameter_name = 'registrar_id'
    title = 'Registrar ID'

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            try:
                value = int(value)
            except ValueError:
                return queryset.none()
            return queryset.filter(registrar_id=value)


### inlines ###

class LinkInline(admin.TabularInline):
    model = Link
    can_delete = False
    fields = ['guid', 'submitted_url', 'creation_timestamp']
    readonly_fields = ['guid', 'submitted_url', 'creation_timestamp']

class SponsorshipInline(admin.TabularInline):
    model = Sponsorship
    readonly_fields = ('created_by', 'created_at', 'status_changed')
    fk_name = 'user'
    extra = 1
    raw_id_fields = ['registrar']

class IAFileInline(admin.TabularInline):
    model = InternetArchiveFile
    fields = readonly_fields = ['id_link', 'item_link', 'cached_file_size']
    can_delete = False

    def id_link(self, obj):
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:perma_internetarchivefile_change", args=(obj.id,)),
            obj.id
        ))
    id_link.short_description = 'id'

    def item_link(self, obj):
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:perma_internetarchiveitem_change", args=(obj.item_id,)),
            obj.item_id
        ))
    item_link.short_description = 'item'

    def cached_file_size(self, obj):
        return filesizeformat(obj.cached_size)
    cached_file_size.short_description = 'cached size'



### paginator ###

class FasterAdminPaginator(Paginator):
    # This will show inaccurate
    # adapted from https://djangosnippets.org/snippets/2593/ and https://stackoverflow.com/a/39852663

    @cached_property
    def count(self):
        cursor = connection.cursor()
        cursor.execute(f"SELECT reltuples AS estimate FROM pg_class WHERE relname = '{self.object_list.query.model._meta.db_table}';")
        estimate = int(cursor.fetchone()[0])
        if estimate > 10000:
            self.estimated_count = True
            self.estimated_count_ignores_filter = bool(self.object_list.query.where)
            return estimate
        try:
            return self.object_list.count()
        except (AttributeError, TypeError):
            # AttributeError if object_list has no count() method.
            # TypeError if object_list.count() requires arguments
            # (i.e. is of type list).
            return len(self.object_list)


### admin models ###

class RegistrarChangeForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(RegistrarChangeForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            try:
                # get the latest subscription info from Perma Payments
                kwargs['instance'].get_subscription()
            except PermaPaymentsCommunicationException:
                # This gets logged inside get_subscription; don't duplicate logging here
                pass


class RegistrarAdmin(SimpleHistoryAdmin):
    form = RegistrarChangeForm

    search_fields = ['name', 'email', 'website']
    list_display = ['name', 'status', 'email', 'website', 'address', 'registrar_users', 'last_active', 'orgs_count', 'link_count', 'tag_list', 'orgs_private_by_default', 'unlimited', 'nonpaying', 'cached_subscription_status', 'cached_subscription_started', 'cached_subscription_rate', 'base_rate']
    list_editable = ['status']
    list_filter = ('status', 'unlimited', 'nonpaying', 'cached_subscription_status', 'orgs_private_by_default')
    fieldsets = (
        (None, {'fields': ('name', 'email', 'website', 'address', 'status', 'tags', 'orgs_private_by_default')}),
        ("Tier", {'fields': ('nonpaying', 'base_rate', 'cached_subscription_started', 'cached_subscription_status', 'cached_subscription_rate', 'unlimited', 'link_limit', 'link_limit_period', 'bonus_links')}),
    )
    inlines = [
        new_class("OrganizationInline", admin.TabularInline, model=Organization,
                  fields=['name', 'default_to_private'],
                  readonly_fields=['name'],
                  can_delete=False,
                  show_change_link=True),
        new_class("RegistrarUserInline", admin.TabularInline, model=LinkUser,
                  fk_name='registrar',
                  fields=['first_name', 'last_name', 'email'],
                  can_delete=False,
                  show_change_link=True),
    ]

    # statistics
    def get_queryset(self, request):
        return super(RegistrarAdmin, self).get_queryset(request).annotate(
            registrar_users=Count('users', distinct=True),
            last_active=Max('users__last_login'),
            orgs_count=Count('organizations',distinct=True)
        ).prefetch_related('tags').order_by('name')
    def registrar_users(self, obj):
        return obj.registrar_users
    def last_active(self, obj):
        return obj.last_active
    def orgs_count(self, obj):
        return obj.orgs_count

    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())

class OrganizationAdmin(SimpleHistoryAdmin):
    fields = ['name', 'registrar', 'default_to_private']
    search_fields = ['name']
    list_display = ['name', 'registrar', 'default_to_private', 'org_users', 'last_active', 'first_active', 'user_deleted', 'link_count',]
    list_filter = [RegistrarNameFilter, RegistrarIdFilter, 'default_to_private', 'user_deleted']

    paginator = FasterAdminPaginator
    show_full_result_count = False

    # statistics
    def get_queryset(self, request):
        qs = super(OrganizationAdmin, self).get_queryset(request).select_related('registrar').prefetch_related('users')
        qs.query.where = WhereNode()  # reset filters to include "deleted" objs
        return qs

    def org_users(self, obj):
        return obj.users.count()
    def last_active(self, obj):
        users = obj.users.exclude(last_login=None)
        return max(u.last_login for u in users) if users.count() else '-'
    def first_active(self, obj):
        users = obj.users.exclude(date_joined=None)
        return min(u.date_joined for u in users) if users.count() else '-'

class LinkUserAddForm(UserCreationForm):
    username = None
    # email = forms.EmailField(label="Email", max_length=254)

    class Meta:
        model = LinkUser
        fields = ("email",)

    def clean_username(self):
        return self.cleaned_data["username"]

class LinkUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = LinkUser

    def __init__(self, *args, **kwargs):
        try:
            # get the latest subscription info from Perma Payments
            kwargs['instance'].get_subscription()
        except PermaPaymentsCommunicationException:
            # This gets logged inside get_subscription; don't duplicate logging here
            pass

        super(LinkUserChangeForm, self).__init__(*args, **kwargs)

        # make sure that user's current organizations show even if they have been deleted
        self.initial['organizations'] = Organization.objects.all_with_deleted().filter(users__id=kwargs['instance'].pk)
        self.fields['organizations'].queryset = Organization.objects.all_with_deleted()\
            .filter(Q(user_deleted=False)|Q(pk__in=self.initial['organizations']))

    def clean(self):
        cleaned_data = super(LinkUserChangeForm, self).clean()

        # check that we're not trying to set both a registrar and an org
        if cleaned_data.get('registrar') and cleaned_data.get('organization'):
            raise ValidationError("User may have either an org or registrar but not both.")
        return cleaned_data


class LinkUserAdmin(UserAdmin):
    form = LinkUserChangeForm
    add_form = LinkUserAddForm
    fieldsets = (
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'raw_email', 'notes')}),
        (None, {'fields': ('password',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_confirmed', 'registrar', 'organizations', 'groups')}),
        ('Tier', {'fields': ('nonpaying', 'base_rate', 'cached_subscription_started', 'cached_subscription_status', 'cached_subscription_rate', 'unlimited', 'link_limit', 'link_limit_period', 'in_trial', 'bonus_links')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    raw_id_fields = ['registrar', 'organizations']
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_confirmed', 'in_trial', 'unlimited', 'nonpaying','cached_subscription_status', 'cached_subscription_started', 'cached_subscription_rate', 'base_rate', 'bonus_links', 'date_joined', 'last_login', 'link_count', 'registrar')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('is_staff', 'is_active', 'in_trial', 'unlimited', 'nonpaying', 'cached_subscription_status', RegistrarUserFilter, OrgUserFilter, OrgUserForRegistrarFilter)
    ordering = ('-id',)
    readonly_fields = ['date_joined']
    # Adds so many fields to the form that it becomes illegal to submit,
    # for users with many links.
    # inlines = [
    #     new_class("CreatedLinksInline", LinkInline, fk_name='created_by', verbose_name_plural="Created Links", show_change_link=True),
    # ]
    inlines = [
        SponsorshipInline,
    ]
    filter_horizontal = ['organizations',]

    paginator = FasterAdminPaginator
    show_full_result_count = False

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('registrar',)
        return qs

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            instance.created_by = request.user
            instance.save()
        formset.save_m2m()


class LinkAdmin(SimpleHistoryAdmin):
    list_display = ['guid', 'submitted_url', 'created_by', 'creation_timestamp', 'organization_id', 'tag_list', 'is_private', 'user_deleted', 'cached_can_play_back', 'captured_by_software', 'internet_archive_upload_status', 'file_size']
    list_filter = [GUIDFilter, CreatedByFilter, SubmittedURLFilter, OrganizationFilter, TagFilter, 'cached_can_play_back', 'internet_archive_upload_status']
    fieldsets = (
        (None, {'fields': ('guid', 'capture_job', 'submitted_url', 'submitted_url_surt','submitted_title', 'submitted_description', 'created_by', 'creation_timestamp', 'captured_by_software', 'captured_by_browser', 'file_size', 'replacement_link', 'tags')}),
        ('Visibility', {'fields': ('is_private', 'private_reason', 'is_unlisted',)}),
        ('User Delete', {'fields': ('user_deleted', 'user_deleted_timestamp',)}),
        ('Organization', {'fields': ('folders', 'notes')}),
        ('Mirroring', {'fields': ('archive_timestamp', 'internet_archive_upload_status', 'cached_can_play_back')}),
    )
    readonly_fields = ['guid', 'capture_job', 'folders', 'creation_timestamp', 'file_size', 'captured_by_software', 'captured_by_browser', 'archive_timestamp']
    inlines = [
        new_class("CaptureInline", admin.TabularInline, model=Capture,
                  fields=['role', 'status', 'url', 'content_type', 'record_type', 'user_upload'],
                  can_delete=False),
        new_class("CaptureJobInline", admin.StackedInline, model=CaptureJob,
                   fields=['status', 'superseded', 'message', 'step_count', 'step_description', 'human'],
                   readonly_fields=['message', 'step_count', 'step_description', 'human'],
                   can_delete=False),
        IAFileInline
    ]
    raw_id_fields = ['created_by','replacement_link']

    paginator = FasterAdminPaginator
    show_full_result_count = False

    def get_queryset(self, request):
        qs = super(LinkAdmin, self).get_queryset(request).select_related('created_by', 'capture_job').prefetch_related('tags')
        qs.query.where = WhereNode()  # reset filters to include "deleted" objs
        return qs

    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())

    def file_size(self, obj):
        return filesizeformat(obj.warc_size)

    file_size.admin_order_field = 'warc_size'


class FolderAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'tree_root_id', 'cached_path', 'owned_by', 'organization', 'sponsored_by', 'read_only']
    list_filter = [NameFilter, OwnerFilter, OrgFilter, RootFilter]
    raw_id_fields = ['tree_root', 'parent', 'created_by', 'owned_by', 'organization', 'sponsored_by']
    ordering = ('cached_path',)

    paginator = FasterAdminPaginator
    show_full_result_count = False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owned_by', 'organization', 'sponsored_by')



class CaptureJobForm(ModelForm):
    """Override so that Scoop logs display with a view-only JSON widget"""

    class Meta:
        model = CaptureJob
        fields = "__all__"
        widgets = {
            "scoop_logs": JSONEditorWidget(options={"mode": "view", "modes": ["view"]}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.get("scoop_logs").disabled = True


class CaptureJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'engine', 'status', 'superseded', 'message', 'created_by_id', 'link_id', 'human', 'submitted_url', 'scoop_state', 'scoop_job_id']
    list_filter = ['engine', CreatedByFilter, LinkIDFilter, 'status', LinkTagFilter, MessageFilter, 'superseded', JobWithDeletedLinkFilter, 'scoop_state', ScoopJobIDFilter]
    raw_id_fields = ['link', 'created_by', 'link_batch']

    paginator = FasterAdminPaginator
    show_full_result_count = False
    form = CaptureJobForm

    def get_queryset(self, request):
        return super(CaptureJobAdmin, self).get_queryset(request).select_related('link')

    def link_creation_timestamp(self, obj):
        if obj.link:
            return obj.link.creation_timestamp
        return None

    # def link_taglist(self, obj):
    #     if obj.link:
    #         return ", ".join(o.name for o in obj.link.tags.all())
    #     return None

    # def capture_time(self, obj):
    #     if obj.capture_start_time and obj.capture_end_time:
    #         return obj.capture_end_time - obj.capture_start_time
    #     return None

    # def scoop_time(self, obj):
    #     if obj.scoop_start_time and obj.scoop_end_time:
    #         return obj.scoop_end_time - obj.scoop_start_time
    #     return None


class LinkBatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_by', 'started_on', 'target_folder', 'cached_capture_job_count']
    raw_id_fields = ['created_by', 'target_folder']
    readonly_fields = ['cached_capture_job_count']

    inlines = [
        new_class("CaptureJobInline", admin.TabularInline, model=CaptureJob,
                  fields=['status', 'submitted_url', 'message', 'step_count', 'step_description', 'human'],
                  readonly_fields=['status', 'submitted_url', 'message', 'step_count', 'step_description', 'human'],
                  can_delete=False)
    ]

    paginator = FasterAdminPaginator
    show_full_result_count = False


class InternetArchiveItemAdmin(admin.ModelAdmin):
    list_display = ['identifier', 'confirmed_exists', 'cached_is_dark', 'added_date', 'span', 'cached_file_count', 'tasks_in_progress', 'complete', 'last_derived', 'derive_required', 'internet_archive_link']
    list_filter = [IAIdentifierFilter, IAItemTypeFilter, IAItemHasTasksFilter, 'confirmed_exists', 'complete', 'cached_is_dark']
    readonly_fields = ['identifier', 'cached_is_dark', 'added_date', 'span', 'cached_title', 'cached_description', 'cached_file_count', 'last_derived']

    paginator = FasterAdminPaginator
    show_full_result_count = False

    def internet_archive_link(self, obj):
        if not obj.confirmed_exists:
            return ''
        url = f'https://archive.org/details/{obj.identifier}'
        return format_html('<a target="_blank" href="{}">{}</a>', url, url)


class InternetArchiveFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'item_link', 'permalink_link', 'status', 'cached_file_size', 'cached_submitted_url', 'cached_format', ]
    list_filter = [IAItemFilter, IALinkIDFilter, IAFileTypeFilter, 'status', IAFileHasMetadataFilter]
    fields = readonly_fields = [
        'link', 'item', 'status', 'cached_file_size', 'cached_title', 'cached_comments',
        'cached_external_identifier', 'cached_external_identifier_match_date', 'cached_format',
        'cached_submitted_url', 'cached_perma_url'
    ]

    paginator = FasterAdminPaginator
    show_full_result_count = False

    def permalink_link(self, obj):
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:perma_link_change", args=(obj.link_id,)),
            obj.link_id
        ))
    permalink_link.short_description = 'GUID'

    def item_link(self, obj):
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:perma_internetarchiveitem_change", args=(obj.item_id,)),
            obj.item_id
        ))
    item_link.short_description = 'IA Item'

    def cached_file_size(self, obj):
        return filesizeformat(obj.cached_size)
    cached_file_size.short_description = 'cached size'


# change Django defaults, because 'extra' isn't helpful anymore now you can add more with javascript
admin.TabularInline.extra = 0
admin.StackedInline.extra = 0

# remove builtin models
admin.site.unregister(Site)

# add our models
admin.site.register(Link, LinkAdmin)
admin.site.register(LinkBatch, LinkBatchAdmin)
admin.site.register(CaptureJob, CaptureJobAdmin)
admin.site.register(LinkUser, LinkUserAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Registrar, RegistrarAdmin)
admin.site.register(Folder, FolderAdmin)
admin.site.register(InternetArchiveItem, InternetArchiveItemAdmin)
admin.site.register(InternetArchiveFile, InternetArchiveFileAdmin)
