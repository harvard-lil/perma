from django.urls import re_path
from . import views

app_name='lockss'
urlpatterns = [
    re_path(r'^search/?$', views.search, name='search'),
    re_path(r'^fetch/(?P<path>(?:[A-Za-z0-9]{2}/)+)(?P<guid>.+)\.warc\.gz$', views.fetch_warc, name='fetch_warc'),

    # LOCKSS config URLs
    re_path(r'^permission/$', views.permission, name='permission'),
    re_path(r'^titledb.xml$', views.titledb, name='titledb'),
    re_path(r'^daemon_settings.txt$', views.daemon_settings, name='daemon_settings'),
]
