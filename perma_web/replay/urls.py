from django.conf import settings
from django.conf.urls import url, include
from django.http import HttpResponse

from django.urls import path

from . import views

urlpatterns = [
    path('', views.iframe, name='iframe'),
    path('static/vendors/replay-web-page/', views.replay_fallback, name='replay_fallback'),
]

### error handlers ###

def handler404(request, exception):
    return HttpResponse('Page Not Found', status=404)
def handler500(request):
    return HttpResponse('Internal Server Error', status=500)

### django debug toolbar ###

if settings.DEBUG and hasattr(settings, 'DEBUG_TOOLBAR_CONFIG'):
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]
