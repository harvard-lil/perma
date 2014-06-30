from django.conf.urls import patterns, url
from perma.urls import guid_pattern

urlpatterns = patterns('mirroring.views',
    url(r'^assets/%s?/?$' % guid_pattern, 'link_assets', name='link_assets'),
    url(r'^update/%s?/?$' % guid_pattern, 'do_update_perma', name='update_link'),
    url(r'^render/%s/?$' % guid_pattern, 'single_link_json', name='single_link_json'),
)