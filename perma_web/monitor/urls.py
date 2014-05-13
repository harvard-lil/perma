from django.conf.urls import patterns, url

urlpatterns = patterns('monitor.views',
    url(r'^archive/?$', 'monitor_archive', name='monitor_archive'),
)