from django.conf.urls import patterns, url

urlpatterns = patterns('lockss.views',
    url(r'^search/?$', 'search', name='search'),
    url(r'^fetch/(?P<path>(?:[A-Za-z0-9]{2}/)+)(?P<guid>.+)\.warc\.gz$', 'fetch_warc', name='fetch_warc'),

    # LOCKSS config URLs
    url(r'^permission/$', 'permission', name='permission'),
    url(r'^titledb.xml$', 'titledb', name='titledb'),
    url(r'^daemon_settings.txt$', 'daemon_settings', name='daemon_settings'),
)