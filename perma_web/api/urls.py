from django.conf import settings
from django.conf.urls import include
from django.http import HttpResponse
from django.urls import re_path
from rest_framework.routers import APIRootView

from perma.urls import guid_pattern

from . import views

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
    re_path('^v1/', include([
        # /folders
        re_path(legacy_user_prefix + r'folders/?$', views.FolderListView.as_view(), name='folders'),
        # /folders/:id
        re_path(legacy_user_prefix + r'folders/(?P<pk>[0-9]+)/?$', views.FolderDetailView.as_view()),
        # /folders/:id/folders
        re_path(r'^(?P<parent_type>folders)/(?P<parent_id>[0-9]+)/folders/?$', views.FolderListView.as_view()),
        # /folders/:id/folders/:id
        re_path(r'^(?P<parent_type>folders)/(?P<parent_id>[0-9]+)/folders/(?P<pk>[0-9]+)/?$', views.FolderDetailView.as_view()),
        # /folders/:id/archives
        re_path(r'^(?P<parent_type>folders)/(?P<parent_id>[0-9]+)/archives/?$', views.AuthenticatedLinkListView.as_view()),
        # /folders/:id/archives/export
        re_path(r'^(?P<parent_type>folders)/(?P<parent_id>[0-9]+)/archives/export/?$', views.AuthenticatedLinkListExportView.as_view()),
        # /folders/:id/archives/:guid
        re_path(fr'^(?P<parent_type>folders)/(?P<parent_id>[0-9]+)/archives/{guid_pattern}/?$', views.MoveLinkView.as_view()),

        # /public/archives
        re_path(r'^public/archives/?$', views.PublicLinkListView.as_view(), name='public_archives'),
        # /public/archives/:guid
        re_path(fr'^public/archives/{guid_pattern}/?$', views.PublicLinkDetailView.as_view(), name='public_archives'),
        # /public/archives/:guid/download
        re_path(fr'^public/archives/{guid_pattern}/download/?$', views.PublicLinkDownloadView.as_view(), name='public_archives_download'),
        # /archives
        re_path(legacy_user_prefix + r'archives/?$', views.AuthenticatedLinkListView.as_view(), name='archives'),
        # /archives/export
        re_path(legacy_user_prefix + r'archives/export/?$', views.AuthenticatedLinkListExportView.as_view(), name='archives_export'),
        # /archives/batches
        re_path(legacy_user_prefix + r'archives/batches/?$', views.LinkBatchesListView.as_view(), name='link_batches'),
        # /archives/batches/:id
        re_path(legacy_user_prefix + r'archives/batches/(?P<pk>[0-9]+)/?$', views.LinkBatchesDetailView.as_view(), name='link_batch'),
        # /archives/batches/:id/export
        re_path(legacy_user_prefix + r'archives/batches/(?P<pk>[0-9]+)/export/?$', views.LinkBatchesDetailExportView.as_view(), name='link_batch_export'),
        # /archives/:guid
        re_path(legacy_user_prefix + fr'archives/{guid_pattern}/?$', views.AuthenticatedLinkDetailView.as_view(), name='archives'),
        # /archives/:guid/download
        re_path(legacy_user_prefix + fr'archives/{guid_pattern}/download/?$', views.AuthenticatedLinkDownloadView.as_view(), name='archives_download'),

        # /capture_jobs
        re_path(legacy_user_prefix + r'capture_jobs/?$', views.CaptureJobListView.as_view(), name='capture_jobs'),
        # /capture_jobs/:id
        re_path(legacy_user_prefix + r'capture_jobs/(?P<pk>[0-9]+)/?$', views.CaptureJobDetailView.as_view()),
        # /capture_jobs/:guid
        re_path(legacy_user_prefix + fr'capture_jobs/{guid_pattern}/?$', views.CaptureJobDetailView.as_view()),

        # /organizations
        re_path(legacy_user_prefix + r'organizations/?$', views.OrganizationListView.as_view(), name='organizations'),
        # /organizations/:id
        re_path(legacy_user_prefix + r'organizations/(?P<pk>[0-9]+)/?$', views.OrganizationDetailView.as_view()),

        # /user
        re_path(r'^user/?$', views.LinkUserView.as_view(), name='user'),

        # / ('/v1/' only, not '/v1')
        re_path(r'^$', root_view)
    ])),

    # redirect plain api.perma.cc/ and perma.cc/api/ to docs:
    re_path(r'^$', views.DeveloperDocsView.as_view())
]

### error handlers ###

def handler404(request, exception):
    return HttpResponse('Page Not Found', status=404)
def handler500(request):
    return HttpResponse('Internal Server Error', status=500)

### django debug toolbar ###

if settings.DEBUG and hasattr(settings, 'DEBUG_TOOLBAR_CONFIG'):
    import debug_toolbar
    urlpatterns += [re_path(r'^__debug__/', include(debug_toolbar.urls))]

# views that only load when running our tests:
# if settings.TESTING:
from .tests import views as test_views
urlpatterns += [
    re_path(r'tests/redirect-to-file$', test_views.redirect_to_file, name='redirect_to_file')
]
