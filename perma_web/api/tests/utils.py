from django.test.utils import override_settings
from django.conf import settings
from tastypie.test import ResourceTestCase, TestApiClient
from api.serializers import MultipartSerializer

import socket
import perma.tasks

# for web server
from django.utils.functional import cached_property
import os
import tempfile
import shutil
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import multiprocessing
from multiprocessing import Process


@override_settings(ROOT_URLCONF='api.urls')
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

        self._media_org = settings.MEDIA_ROOT
        self._media_tmp = settings.MEDIA_ROOT = tempfile.mkdtemp()
        print("Created MEDIA_ROOT temp dir " + settings.MEDIA_ROOT)

    def tearDown(self):
        settings.MEDIA_ROOT = self._media_org
        shutil.rmtree(self._media_tmp)
        print("Removed MEDIA_ROOT temp dir " + self._media_tmp)

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
        cls._cwd_org = os.getcwd()
        cls._server_tmp = tempfile.mkdtemp()
        os.chdir(cls._server_tmp)
        print("Created server temp dir " + cls._server_tmp)

        # Copy over files to current temp dir, stripping paths.
        print("Serving files:")
        for file in cls.serve_files:
            print("- " + file)
            shutil.copyfile(os.path.join(cls._cwd_org, file), os.path.basename(file))

        # start server
        httpd = HTTPServer(('', cls.server_port), SimpleHTTPRequestHandler)
        httpd._BaseServer__is_shut_down = multiprocessing.Event()
        cls._server_process = Process(target=httpd.serve_forever)
        cls._server_process.start()
        return cls._server_process

    @classmethod
    def kill_server(cls):
        cls._server_process.terminate()
        os.chdir(cls._cwd_org)
        shutil.rmtree(cls._server_tmp)

    @cached_property
    def server_url(self):
        return "http://" + self.server_domain + ":" + str(self.server_port)
