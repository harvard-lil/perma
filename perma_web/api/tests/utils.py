from django.test.utils import override_settings
from tastypie.test import ResourceTestCase, TestApiClient
from api.serializers import MultipartSerializer

import socket
import perma.tasks

# for server_thread
from django.utils.functional import cached_property
import os
import tempfile
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

    url_base = "/v1"

    server_domain = "perma.dev"
    server_port = 8999
    serve_files = []

    perma.tasks.ROBOTS_TXT_TIMEOUT = perma.tasks.AFTER_LOAD_TIMEOUT = 1  # reduce wait times for testing

    @classmethod
    def setUpClass(cls):
        if len(cls.serve_files):
            cls.start_server()

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "_server_process", None):
            cls.kill_server()

    def setUp(self):
        super(ApiResourceTestCase, self).setUp()
        self.api_client = TestApiClient(serializer=MultipartSerializer())

    def get_credentials(self, user=None):
        user = user or self.user
        return self.create_apikey(username=user.email, api_key=user.api_key.key)

    @classmethod
    def start_server(cls):
        """
            Set up a server with some known files to run captures against. Example:

                with run_server_in_temp_folder(['test/assets/test.html','test/assets/test.pdf']):
                    assert(requests.get("http://localhost/test.html") == contents_of_file("test.html"))
        """
        try:
            assert socket.gethostbyname(cls.server_domain) == '127.0.0.1'
        except (socket.gaierror, AssertionError):
            cls.fail("Please add `127.0.0.1 " + cls.server_domain + "` to your hosts file before running this test.")

        # Run in temp dir.
        # We have to (implicitly) cwd to this so SimpleHTTPRequestHandler serves the files for us.
        cls._old_cwd = os.getcwd()
        cls._tmpdir = tempfile.mkdtemp()
        os.chdir(cls._tmpdir)
        print("Created temp dir " + cls._tmpdir)

        # Copy over files to current temp dir, stripping paths.
        print("Serving files:")
        for file in cls.serve_files:
            print("- " + file)
            shutil.copyfile(os.path.join(cls._old_cwd, file), os.path.basename(file))

        # start server
        httpd = HTTPServer(('', cls.server_port), SimpleHTTPRequestHandler)
        httpd._BaseServer__is_shut_down = multiprocessing.Event()
        cls._server_process = Process(target=httpd.serve_forever)
        cls._server_process.start()
        return cls._server_process

    @classmethod
    def kill_server(cls):
        cls._server_process.terminate()
        os.chdir(cls._old_cwd)
        shutil.rmtree(cls._tmpdir)

    @cached_property
    def server_url(self):
        return "http://" + self.server_domain + ":" + str(self.server_port)
