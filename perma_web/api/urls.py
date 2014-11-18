from django.conf.urls import *
from tastypie.api import Api
from api.resources import (CurrentUserResource,
                           VestingOrgResource,
                           LinkResource,
                           FolderResource,
                           AssetResource)

v1_api = Api(api_name='v1')
v1_api.register(CurrentUserResource())
v1_api.register(VestingOrgResource())
v1_api.register(LinkResource())
v1_api.register(FolderResource())
v1_api.register(AssetResource())

urlpatterns = v1_api.urls
