from django.conf.urls import url, include
from django.contrib import admin
from django.conf.urls import *

admin.autodiscover()

handler500 = 'perma.views.error_management.server_error'

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),  # Django admin
    url(r'^api/', include('api.urls')), # Our API mirrored for session access
    url(r'^lockss/', include('lockss.urls', namespace='lockss')), # Our app that communicates with the mirror network
    url(r'^', include('perma.urls')), # The Perma app
]
