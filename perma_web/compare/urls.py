from django.conf.urls import url
from compare import views

original_guid_pattern = r'(?P<original_guid>[a-zA-Z0-9\-]{8,11})'
new_guid_pattern = r'(?P<new_guid>[a-zA-Z0-9\-]{8,11})'

urlpatterns = [
    #url(r'(?P<guid>.+)/diff/?$', views.diff_entry, name='diff_entry'),
    url(r'^%s/compare/?$' % original_guid_pattern, views.list, name='main'),
    url(r'^%s/compare/create?$' % original_guid_pattern, views.capture_create, name='capture_create'),
    url(r'^%s/compare/%s?$' % (original_guid_pattern, new_guid_pattern), views.capture_compare),
    url(r'^%s/compare/%s?type=capture$' % (original_guid_pattern, new_guid_pattern), views.capture_compare, name='capture_compare'), #>> guid compare guid, allows for sharing too
    url(r'^%s/compare/%s?type=image$' % (original_guid_pattern, new_guid_pattern), views.capture_compare, name='image_compare'),
]
