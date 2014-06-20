from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
    url(r'^monitor/', include('monitor.urls')), # Our app that monitors Perma
    url(r'^mirroring/', include('mirroring.urls', namespace='mirroring')), # Our app that handles mirroring
    url(r'^', include('perma.urls')), # The Perma app
)