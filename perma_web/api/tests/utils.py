from django.test.utils import override_settings
from tastypie.test import ResourceTestCase, TestApiClient
from api.serializers import MultipartSerializer

@override_settings(RUN_TASKS_ASYNC=False, # avoid sending celery tasks to queue -- just run inline
                   # django-pipeline causes problems if enabled for tests, so disable it.
                   # That's not great because it's a less accurate test -- when we upgrade to Django 1.7, consider using
                   # StaticLiveServerCase instead. http://stackoverflow.com/a/22058962/307769
                   STATICFILES_STORAGE='pipeline.storage.NonPackagingPipelineStorage',
                   PIPELINE_ENABLED=False,
                   # Load the api subdomain routes
                   ROOT_URLCONF='api.urls',
                   SUBDOMAIN_URLCONFS={})

class ApiResourceTestCase(ResourceTestCase):

    def setUp(self):
        super(ApiResourceTestCase, self).setUp()
        self.api_client = TestApiClient(serializer=MultipartSerializer())
        self.url_base = "/v1"

    def get_credentials(self, user=None):
        user = user or self.user
        return self.create_apikey(username=user.email, api_key=user.api_key.key)
