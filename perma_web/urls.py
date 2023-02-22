from django.conf.urls import handler500, include
from django.contrib import admin
from django.urls import re_path

# Setting our custom route handler so that images are displayed properly
# Used implicitly by Django
handler500 = 'perma.views.error_management.server_error'  # noqa

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),  # Django admin
    re_path(r'^api/', include('api.urls')), # Our API mirrored for session access
    re_path(r'^lockss/', include('lockss.urls', namespace='lockss')), # Our app that communicates with the mirror network
    re_path(r'^', include('perma.urls')), # The Perma app
]
