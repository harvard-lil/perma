from django.conf import settings
from django.conf.urls import patterns, url, include
from django.http import HttpResponse
from django.views.generic.base import RedirectView

from tastypie.api import Api, NamespacedApi
from api.resources import (LinkResource,
                           FolderResource,
                           CurrentUserResource,
                           CurrentUserLinkResource,
                           CurrentUserFolderResource,
                           CurrentUserOrganizationResource,
                           PublicLinkResource,
                           CurrentUserCaptureJobResource)

### collateral ###

class RedirectWithRootDomain(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        url = super(RedirectWithRootDomain, self).get_redirect_url(*args, **kwargs)
        return self.request.scheme + '://' + settings.HOST + url

collateral_urls = patterns('',
  url(r'^/?$', RedirectWithRootDomain.as_view(url='/docs/developer', permanent=True))
)

### v1 ###

v1_api = Api(api_name='v1')

# /public/archives
v1_api.register(PublicLinkResource())

# /archives
# /folders/<id>/archives
v1_api.register(LinkResource())

# /folders
# /folders/<id>/folders
v1_api.register(FolderResource())

# /user
# /user/archives
# /user/folders
# /user/organizations
# /user/capture_jobs
v1_api.register(CurrentUserResource())
v1_api.register(CurrentUserLinkResource())
v1_api.register(CurrentUserFolderResource())
v1_api.register(CurrentUserOrganizationResource())
v1_api.register(CurrentUserCaptureJobResource())

### v1a ###

v1a_api = NamespacedApi(api_name='v1a', urlconf_namespace='v1a')
v1a_api._registry = v1_api._registry.copy()
v1a_api._canonicals = v1_api._canonicals.copy()

### add API versions to urlpatters ###

urlpatterns = v1_api.urls + v1a_api.urls + collateral_urls

### error handlers ###

handler404 = lambda (request): HttpResponse(status=404)
handler500 = lambda (request): HttpResponse(status=500)

### django debug toolbar ###

if settings.DEBUG and hasattr(settings, 'DEBUG_TOOLBAR_CONFIG'):
    import debug_toolbar
    urlpatterns += patterns('',
                            url(r'^__debug__/', include(debug_toolbar.urls)),
                            )