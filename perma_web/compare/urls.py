from django.conf.urls import url
from compare import views

old_guid_pattern = r'(?P<old_guid>[a-zA-Z0-9\-]{8,11})'
new_guid_pattern = r'(?P<new_guid>[a-zA-Z0-9\-]{8,11})'

urlpatterns = [
    url(r'^%s/compare/?$' % old_guid_pattern, views.list, name='main'),
    url(r'^%s/compare/create?$' % old_guid_pattern, views.capture_create, name='capture_create'),
    url(r'^%s/compare/%s?$' % (old_guid_pattern, new_guid_pattern), views.capture_compare, name='capture_compare'),
    url(r'^%s/compare/%s/get-resource-list?$' % (old_guid_pattern, new_guid_pattern), views.get_resource_list, name='get_resource_list'),
    url(r'^%s/compare-img/?$' % old_guid_pattern, views.image_compare, name='image_compare'),
]
