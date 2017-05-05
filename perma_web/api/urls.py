from django.conf import settings
from django.conf.urls import url, include
from django.http import HttpResponse
from django.views.generic import RedirectView
from rest_framework.routers import APIRootView

from perma.urls import guid_pattern

from . import views


# helpers
class RedirectWithRootDomain(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        url = super(RedirectWithRootDomain, self).get_redirect_url(*args, **kwargs)
        return self.request.scheme + '://' + settings.HOST + url

# list views that should appear in the HTML version of the API root
root_view = APIRootView.as_view(api_root_dict={
    'folders': 'folders',
    'capture_jobs': 'capture_jobs',
    'archives': 'archives',
    'public_archives': 'public_archives',
    'organizations': 'organizations',
    'user': 'user',
})

# reverse() URL namespace
app_name = 'api'

# The previous version of the API had a number of endpoints under /user instead of at the top level.
# This regex lets endpoints work with or without /user at the start.
legacy_user_prefix = r'^(?:user/)?'

urlpatterns = [
    # /v1
    url('^v1/', include([
        # /folders
        url(legacy_user_prefix + r'folders/?$', views.FolderListView.as_view(), name='folders'),
        # /folders/:id
        url(legacy_user_prefix + r'folders/(?P<pk>[0-9]+)/?$', views.FolderDetailView.as_view()),
        # /folders/:id/folders
        url(r'^(?P<parent_type>folders)/(?P<parent_id>[0-9]+)/folders/?$', views.FolderListView.as_view()),
        # /folders/:id/folders/:id
        url(r'^(?P<parent_type>folders)/(?P<parent_id>[0-9]+)/folders/(?P<pk>[0-9]+)/?$', views.FolderDetailView.as_view()),
        # /folders/:id/archives
        url(r'^(?P<parent_type>folders)/(?P<parent_id>[0-9]+)/archives/?$', views.AuthenticatedLinkListView.as_view()),
        # /folders/:id/archives/:guid
        url(r'^(?P<parent_type>folders)/(?P<parent_id>[0-9]+)/archives/%s/?$' % guid_pattern, views.MoveLinkView.as_view()),

        # /public/archives
        url(r'^public/archives/?$', views.PublicLinkListView.as_view(), name='public_archives'),
        # /public/archives/:guid
        url(r'^public/archives/%s/?$' % guid_pattern, views.PublicLinkDetailView.as_view(), name='public_archives'),

        # /archives
        url(legacy_user_prefix + r'archives/?$', views.AuthenticatedLinkListView.as_view(), name='archives'),
        # /archives/:guid
        url(legacy_user_prefix + r'archives/%s/?$' % guid_pattern, views.AuthenticatedLinkDetailView.as_view(), name='archives'),

        # /capture_jobs
        url(legacy_user_prefix + r'capture_jobs/?$', views.CaptureJobListView.as_view(), name='capture_jobs'),
        # /capture_jobs/:id
        url(legacy_user_prefix + r'capture_jobs/(?P<pk>[0-9]+)/?$', views.CaptureJobDetailView.as_view()),
        # /capture_jobs/:guid
        url(legacy_user_prefix + r'capture_jobs/%s/?$' % guid_pattern, views.CaptureJobDetailView.as_view()),

        # /organizations
        url(legacy_user_prefix + r'organizations/?$', views.OrganizationListView.as_view(), name='organizations'),
        # /organizations/:id
        url(legacy_user_prefix + r'organizations/(?P<pk>[0-9]+)/?$', views.OrganizationDetailView.as_view()),

        # /user
        url(r'^user/?$', views.LinkUserView.as_view(), name='user'),

        # /
        url(r'^$', root_view)
    ])),

    # redirect plain api.perma.cc/ and perma.cc/api/ to docs:
    url(r'^$', RedirectWithRootDomain.as_view(url='/docs/developer'))
]

### error handlers ###

def handler404(request):
    HttpResponse(status=404)
def handler500(request):
    HttpResponse(status=500)

### django debug toolbar ###

if settings.DEBUG and hasattr(settings, 'DEBUG_TOOLBAR_CONFIG'):
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]
