from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.sites.models import Site
from django.db.models import Count, Max, Min

from mptt.admin import MPTTModelAdmin

from .models import *
from .admin_utils import new_class, InlineEditLinkMixin

### inlines ###

class LinkInline(admin.TabularInline):
    model = Link
    can_delete = False
    fields = ['guid', 'submitted_url', 'creation_timestamp', 'vested']
    readonly_fields = ['guid', 'submitted_url', 'creation_timestamp', 'vested']


### admin models ###


class RegistrarAdmin(admin.ModelAdmin):
    search_fields = ['name', 'email', 'website']
    list_display = ['name', 'email', 'website', 'vested_links', 'registrar_users', 'last_active', 'vesting_orgs_count']
    inlines = [
        new_class("VestingOrgInline", InlineEditLinkMixin, admin.TabularInline, model=VestingOrg,
                  fields=['name',],
                  can_delete=False),
        new_class("RegistrarUserInline", InlineEditLinkMixin, admin.TabularInline, model=LinkUser,
                  fields=['first_name', 'last_name', 'email'],
                  can_delete=False),
    ]

    # statistics
    def get_queryset(self, request):
        return super(RegistrarAdmin, self).get_queryset(request).annotate(
            vested_links=Count('vesting_orgs__link',distinct=True),
            registrar_users=Count('linkuser', distinct=True),
            last_active=Max('linkuser__last_login', distinct=True),
            vesting_orgs_count=Count('vesting_orgs',distinct=True)
        )
    def vested_links(self, obj):
        return obj.vested_links
    def registrar_users(self, obj):
        return obj.registrar_users
    def last_active(self, obj):
        return obj.last_active
    def vesting_orgs_count(self, obj):
        return obj.vesting_orgs_count


class VestingOrgAdmin(admin.ModelAdmin):
    fields = ['name', 'registrar']
    search_fields = ['name']
    list_display = ['name', 'registrar', 'vesting_users', 'last_active', 'first_active', 'vested_links']
    list_filter = ['registrar']
    inlines = [
        new_class("VestingOrgUserInline", InlineEditLinkMixin, admin.TabularInline, model=LinkUser,
                  fields=['first_name', 'last_name', 'email'],
                  can_delete = False),
    ]

    # statistics
    def get_queryset(self, request):
        return super(VestingOrgAdmin, self).get_queryset(request).annotate(
            vesting_users=Count('users', distinct=True),
            last_active=Max('users__last_login', distinct=True),
            first_active=Min('users__date_joined', distinct=True),
            vested_links=Count('link', distinct=True),
        )
    def vesting_users(self, obj):
        return obj.vesting_users
    def last_active(self, obj):
        return obj.last_active
    def first_active(self, obj):
        return obj.first_active
    def vested_links(self, obj):
        return obj.vested_links


class LinkUserChangeForm(UserChangeForm):
    class Meta:
        model = LinkUser

    def __init__(self, *args, **kwargs):
        del self.base_fields['username']
        super(LinkUserChangeForm, self).__init__(*args, **kwargs)


class LinkUserAdmin(UserAdmin):
    form = LinkUserChangeForm
    fieldsets = (
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        (None, {'fields': ('password',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_confirmed', 'groups', 'registrar', 'vesting_org')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    filter_horizontal = ('groups',)
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_confirmed', 'date_joined', 'last_login', 'created_links_count', 'vested_links_count')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('is_staff', 'is_active', 'groups')
    ordering = None
    readonly_fields = ['date_joined']
    inlines = [
        new_class("CreatedLinksInline", InlineEditLinkMixin, LinkInline, fk_name='created_by', verbose_name_plural="Created Links"),
        new_class("VestedLinksInline", InlineEditLinkMixin, LinkInline, fk_name='vested_by_editor', verbose_name_plural="Vested Links"),
    ]

    # statistics
    def get_queryset(self, request):
        return super(LinkUserAdmin, self).get_queryset(request).annotate(
            vested_links_count=Count('vested_links', distinct=True),
            created_links_count = Count('created_links', distinct=True)
        )
    def vested_links_count(self, obj):
        return obj.vested_links_count
    def created_links_count(self, obj):
        return obj.created_links_count


class LinkAdmin(admin.ModelAdmin):
    list_display = ['guid', 'submitted_url', 'submitted_title', 'creation_timestamp', 'vested']
    search_fields = ['guid', 'submitted_url', 'submitted_title']
    fieldsets = (
        (None, {'fields': ('guid', 'submitted_url', 'submitted_title', 'created_by', 'creation_timestamp', 'view_count')}),
        ('Vesting', {'fields': ('vested', 'vested_by_editor', 'vesting_org', 'vested_timestamp')}),
        ('Dark Archive', {'fields': ('dark_archived', 'dark_archived_robots_txt_blocked', 'dark_archived_by',)}),
        ('User Delete', {'fields': ('user_deleted', 'user_deleted_timestamp',)}),
        ('Organization', {'fields': ('folders', 'notes')}),
    )
    readonly_fields = ['guid', 'view_count', 'folders', 'creation_timestamp']
    inlines = [
        new_class("AssetInline", admin.TabularInline, model=Asset,
                  fields=['base_storage_path', 'image_capture', 'warc_capture', 'pdf_capture', 'text_capture'],
                  can_delete=False, max_num=1),
    ]


class FolderAdmin(MPTTModelAdmin):
    list_display = ['name', 'owned_by', 'vesting_org']
    list_filter = ['owned_by', 'vesting_org']



# change Django defaults, because 'extra' isn't helpful anymore now you can add more with javascript
admin.TabularInline.extra = 0
admin.StackedInline.extra = 0

# remove builtin models
admin.site.unregister(Site)
admin.site.unregister(Group)

# add our models
admin.site.register(Link, LinkAdmin)
admin.site.register(LinkUser, LinkUserAdmin)
admin.site.register(VestingOrg, VestingOrgAdmin)
admin.site.register(Registrar, RegistrarAdmin)
admin.site.register(Folder, FolderAdmin)