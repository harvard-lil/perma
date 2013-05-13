from django.conf.urls.defaults import patterns, url, include
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns('',
    
    # Common Pages
    url(r'^', include('linky.linky.urls')),
)