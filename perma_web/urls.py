from django.conf.urls import patterns, url, include
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),  # Django admin
    url(r'^api/', include('api.urls')), # Our API mirrored for session access
    url(r'^monitor/', include('monitor.urls')), # Our app that monitors Perma
    url(r'^', include('perma.urls')), # The Perma app
)
