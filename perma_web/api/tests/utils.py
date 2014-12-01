from django.test.utils import override_settings
from tastypie.test import ResourceTestCase, TestApiClient
from api.serializers import MultipartSerializer

# for server_thread
from django.utils.functional import cached_property
import os
import tempdir
import shutil
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import multiprocessing
from multiprocessing import Process


@override_settings(RUN_TASKS_ASYNC=False,  # avoid sending celery tasks to queue -- just run inline
                   # django-pipeline causes problems if enabled for tests, so disable it.
                   # That's not great because it's a less accurate test -- when we upgrade to Django 1.7, consider using
                   # StaticLiveServerCase instead. http://stackoverflow.com/a/22058962/307769
                   STATICFILES_STORAGE='pipeline.storage.NonPackagingPipelineStorage',
                   PIPELINE_ENABLED=False,
                   # Load the api subdomain routes
                   ROOT_URLCONF='api.urls',
                   SUBDOMAIN_URLCONFS={})
class ApiResourceTestCase(ResourceTestCase):

    serve_files = []
    port = 8999

    def setUp(self):
        super(ApiResourceTestCase, self).setUp()
        self.api_client = TestApiClient(serializer=MultipartSerializer())
        self.url_base = "/v1"
        if len(self.serve_files):
            self.server_thread.start()

    def tearDown(self):
        if len(self.serve_files):
            self.server_thread.terminate()

    def get_credentials(self, user=None):
        user = user or self.user
        return self.create_apikey(username=user.email, api_key=user.api_key.key)

    @cached_property
    def server_thread(self):
        """
            Set up a server with some known files to run captures against. Example:

                with run_server_in_temp_folder(['test/assets/test.html','test/assets/test.pdf']):
                    assert(requests.get("http://localhost/test.html") == contents_of_file("test.html"))
        """
        # Run in temp dir.
        # We have to (implicitly) cwd to this so SimpleHTTPRequestHandler serves the files for us.
        old_cwd = os.getcwd()
        with tempdir.in_tempdir():

            # Copy over files to current temp dir, stripping paths.
            for file in self.serve_files:
                shutil.copyfile(os.path.join(old_cwd, file), os.path.basename(file))

            # start server
            httpd = HTTPServer(('', self.port), SimpleHTTPRequestHandler)
            httpd._BaseServer__is_shut_down = multiprocessing.Event()
            return Process(target=httpd.serve_forever)

    @cached_property
    def server_url(self):
        return "http://perma.dev:" + str(self.port) + "/perma/tests/assets/target_capture_files"
