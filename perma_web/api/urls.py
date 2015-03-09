from django.conf.urls import patterns, include
from tastypie.api import Api, NamespacedApi
from api.resources import (LinkResource,
                           FolderResource,
                           CurrentUserResource,
                           CurrentUserLinkResource,
                           CurrentUserFolderResource,
                           CurrentUserVestingOrgResource, PublicLinkResource)

### v1 ###

v1_api = Api(api_name='v1')

# /public/archives
v1_api.register(PublicLinkResource())

# /archives
v1_api.register(LinkResource())

# /folders
# /folders/<id>/folders
# /folders/<id>/archives
v1_api.register(FolderResource())

# /user
# /user/archives
# /user/folders
# /user/vesting_orgs
v1_api.register(CurrentUserResource())
v1_api.register(CurrentUserLinkResource())
v1_api.register(CurrentUserFolderResource())
v1_api.register(CurrentUserVestingOrgResource())

### v1a ###

v1a_api = NamespacedApi(api_name='v1a', urlconf_namespace='v1a')
v1a_api._registry = v1_api._registry.copy()
v1a_api._canonicals = v1_api._canonicals.copy()

### add API versions to urlpatters ###

urlpatterns = v1_api.urls + v1a_api.urls

