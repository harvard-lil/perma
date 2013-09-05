from django.conf.urls import patterns, url, include
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns('',
    
    # Common Pages
    url(r'^', include('perma.urls')),
)