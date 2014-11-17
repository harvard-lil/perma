from django.test.utils import override_settings
from tastypie.test import ResourceTestCase, TestApiClient
from api.serializers import MultipartSerializer

@override_settings(STATICFILES_STORAGE='pipeline.storage.NonPackagingPipelineStorage',
                   PIPELINE_ENABLED=False,
                   # Load the api subdomain routes
                   ROOT_URLCONF='api.urls',
                   SUBDOMAIN_URLCONFS={})

class ApiResourceTestCase(ResourceTestCase):

    def setUp(self):
        super(ApiResourceTestCase, self).setUp()
        self.api_client = TestApiClient(serializer=MultipartSerializer())
        self.url_base = "/v1"
        
