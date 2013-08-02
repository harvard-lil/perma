from django.conf.urls import patterns, url, include
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns('',
    
    # Common Pages
    url(r'^', include('linky.linky.urls')),
)