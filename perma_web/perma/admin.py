from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db.models import Count, Max
from django.db.models.sql.where import WhereNode

from mptt.admin import MPTTModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import *
from .admin_utils import new_class, InlineEditLinkMixin

### inlines ###

class LinkInline(admin.TabularInline):
    model = Link
    can_delete = False
    fields = ['guid', 'submitted_url', 'creation_timestamp']
    readonly_fields = ['guid', 'submitted_url', 'creation_timestamp']


### admin models ###


class RegistrarAdmin(SimpleHistoryAdmin):
    search_fields = ['name', 'email', 'website']
    list_display = ['name', 'status', 'email', 'website', 'show_partner_status', 'partner_display_name', 'logo', 'latitude', 'longitude', 'registrar_users', 'last_active', 'orgs_count', 'link_count', 'tag_list']
    list_editable = ['show_partner_status', 'partner_display_name', 'latitude', 'longitude', 'status']
    fieldsets = (
        (None, {'fields': ('name', 'email', 'website', 'status', 'tags')}),
        ("Partner Display", {'fields': ('show_partner_status', 'partner_display_name', 'logo', 'latitude', 'longitude')}),
    )
    inlines = [
        new_class("OrganizationInline", InlineEditLinkMixin, admin.TabularInline, model=Organization,
                  fields=['name',],
                  can_delete=False),
        new_class("RegistrarUserInline", InlineEditLinkMixin, admin.TabularInline, model=LinkUser,
                  fk_name='registrar',
                  fields=['first_name', 'last_name', 'email'],
                  can_delete=False),
    ]

    # statistics
    def get_queryset(self, request):
        return super(RegistrarAdmin, self).get_queryset(request).annotate(
            registrar_users=Count('users', distinct=True),
            last_active=Max('users__last_login', distinct=True),
            orgs_count=Count('organizations',distinct=True)
        ).prefetch_related('tags')
    def registrar_users(self, obj):
        return obj.registrar_users
    def last_active(self, obj):
        return obj.last_active
    def orgs_count(self, obj):
        return obj.orgs_count

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

class OrganizationAdmin(SimpleHistoryAdmin):
    fields = ['name', 'registrar']
    search_fields = ['name']
    list_display = ['name', 'registrar', 'org_users', 'last_active', 'first_active', 'user_deleted', 'link_count',]
    list_filter = ['registrar', 'user_deleted']
    
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
        super(LinkUserChangeForm, self).__init__(*args, **kwargs)

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
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        (None, {'fields': ('password',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_confirmed', 'registrar', 'organizations', 'monthly_link_limit')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_confirmed', 'date_joined', 'last_login', 'link_count', 'registrar')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('is_staff', 'is_active')
    ordering = None
    readonly_fields = ['date_joined']
    inlines = [
        new_class("CreatedLinksInline", InlineEditLinkMixin, LinkInline, fk_name='created_by', verbose_name_plural="Created Links"),
    ]
    filter_horizontal = ['organizations']


class LinkAdmin(SimpleHistoryAdmin):
    list_display = ['guid', 'submitted_url', 'submitted_title', 'created_by', 'creation_timestamp','user_deleted']
    search_fields = ['guid', 'submitted_url', 'submitted_title']
    fieldsets = (
        (None, {'fields': ('guid', 'submitted_url', 'submitted_title', 'created_by', 'creation_timestamp', 'view_count', 'warc_size')}),
        ('Visibility', {'fields': ('is_private', 'private_reason', 'is_unlisted',)}),
        ('User Delete', {'fields': ('user_deleted', 'user_deleted_timestamp',)}),
        ('Organization', {'fields': ('folders', 'notes')}),
        ('Mirroring', {'fields': ('archive_timestamp',)})
    )
    readonly_fields = ['guid', 'view_count', 'folders', 'creation_timestamp']  #, 'archive_timestamp']
    inlines = [
        new_class("CaptureInline", admin.TabularInline, model=Capture,
                  fields=['url', 'content_type', 'record_type', 'user_upload'],
                  can_delete=False),
    ]
    raw_id_fields = ['created_by',]

    def get_queryset(self, request):
        qs = super(LinkAdmin, self).get_queryset(request).select_related('created_by',)
        qs.query.where = WhereNode()  # reset filters to include "deleted" objs
        return qs


class FolderAdmin(MPTTModelAdmin):
    list_display = ['name', 'owned_by', 'organization']
    list_filter = ['owned_by', 'organization']


class CaptureJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'link_id', 'created_by', 'creation_timestamp', 'human']
    list_filter = ['status']
    raw_id_fields = ['link']

    def get_queryset(self, request):
        return super(CaptureJobAdmin, self).get_queryset(request).filter(link__user_deleted=False).select_related('link','link__created_by')

    def created_by(self, obj):
        return obj.link.created_by
    def creation_timestamp(self, obj):
        return obj.link.creation_timestamp

# change Django defaults, because 'extra' isn't helpful anymore now you can add more with javascript
admin.TabularInline.extra = 0
admin.StackedInline.extra = 0

# remove builtin models
admin.site.unregister(Site)
admin.site.unregister(Group)

# add our models
admin.site.register(Link, LinkAdmin)
admin.site.register(CaptureJob, CaptureJobAdmin)
admin.site.register(LinkUser, LinkUserAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Registrar, RegistrarAdmin)
admin.site.register(Folder, FolderAdmin)
