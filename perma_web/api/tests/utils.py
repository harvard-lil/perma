from django.test.utils import override_settings
from tastypie.test import ResourceTestCase

@override_settings(STATICFILES_STORAGE='pipeline.storage.NonPackagingPipelineStorage',
                   PIPELINE_ENABLED=False,
                   # Load the api subdomain routes
                   ROOT_URLCONF='api.urls',
                   SUBDOMAIN_URLCONFS={})

class ApiResourceTestCase(ResourceTestCase):

    def setUp(self):
        super(ApiResourceTestCase, self).setUp()
        self.url_base = "/v1"
