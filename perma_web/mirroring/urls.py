from django.conf.urls import patterns, url
from perma.urls import guid_pattern

urlpatterns = patterns('mirroring.views',
    url(r'^render_link/?$', 'single_link_json', name='single_link_json'),
    url(r'^export/updates/?$', 'export_updates', name='export_updates'),
    url(r'^export/full/?$', 'export_database', name='export_database'),
    url(r'^import/updates/?$', 'import_updates', name='import_updates'),
    url(r'^import/full/?$', 'import_database', name='import_database'),
    url(r'^import/media/?$', 'media_sync', name='media_sync'),
)