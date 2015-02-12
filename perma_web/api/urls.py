from django.conf import settings
from tastypie.api import Api
from api.resources import (VestingOrgResource,
                           LinkResource,
                           FolderResource,
                           AssetResource,
                           RegistrarResource,
                           CurrentUserResource,
                           CurrentUserLinkResource,
                           CurrentUserFolderResource,
                           CurrentUserVestingOrgResource, PublicLinkResource)

v1_api = Api(api_name='v1')
# v1_api.register(VestingOrgResource())
# v1_api.register(AssetResource())
# v1_api.register(RegistrarResource())

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

urlpatterns = v1_api.urls
