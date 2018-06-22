from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^search/?$', views.search, name='search'),
    url(r'^fetch/(?P<path>(?:[A-Za-z0-9]{2}/)+)(?P<guid>.+)\.warc\.gz$', views.fetch_warc, name='fetch_warc'),

    # LOCKSS config URLs
    url(r'^permission/$', views.permission, name='permission'),
    url(r'^titledb.xml$', views.titledb, name='titledb'),
    url(r'^daemon_settings.txt$', views.daemon_settings, name='daemon_settings'),
]
