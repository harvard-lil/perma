from django.conf.urls import *
from tastypie.api import Api
from api.resources import LinkResource, FolderResource

v1_api = Api(api_name='v1')
v1_api.register(LinkResource(), canonical=True)
v1_api.register(FolderResource(), canonical=True)

urlpatterns = v1_api.urls
