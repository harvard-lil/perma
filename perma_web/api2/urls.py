from django.conf.urls import url
from rest_framework.routers import APIRootView

from perma.urls import guid_pattern

import views


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
app_name = 'api2'

# The previous version of the API had a number of endpoints under /user instead of at the top level.
# This regex lets endpoints work with or without /user at the start.
legacy_user_prefix = r'^(?:user/)?'

urlpatterns = [
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
    url(r'^public/archives/%s/?$' % guid_pattern, views.PublicLinkDetailView.as_view()),

    # /archives
    url(legacy_user_prefix + r'archives/?$', views.AuthenticatedLinkListView.as_view(), name='archives'),
    # /archives/:guid
    url(legacy_user_prefix + r'archives/%s/?$' % guid_pattern, views.AuthenticatedLinkDetailView.as_view()),

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
]