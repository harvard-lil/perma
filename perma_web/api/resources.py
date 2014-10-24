# myapp/api.py
from tastypie import fields
from tastypie.resources import ModelResource
from perma.models import LinkUser, Link, Folder, VestingOrg


class LinkUserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = LinkUser.objects.all()

class VestingOrgResource(ModelResource):
    class Meta:
        resource_name = 'vesting_orgs'
        queryset = VestingOrg.objects.all()

class LinkResource(ModelResource):
    created_by = fields.ForeignKey(LinkUserResource, 'created_by', full=True, null=True, blank=True)
    vested_by_editor = fields.ForeignKey(LinkUserResource, 'vested_by_editor', full=True, null=True, blank=True)
    vesting_org = fields.ForeignKey(VestingOrgResource, 'vesting_org', full=True, null=True)

    class Meta:
        resource_name = 'archives'
        queryset = Link.objects.all()

class FolderResource(ModelResource):
    class Meta:
        resource_name = 'folders'
        queryset = Folder.objects.all()
