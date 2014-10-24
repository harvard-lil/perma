# myapp/api.py
from tastypie.resources import ModelResource
from perma.models import Link


class LinkResource(ModelResource):
    class Meta:
        resource_name = 'links'
        queryset = Link.objects.all()
