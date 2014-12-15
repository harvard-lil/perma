from django.test.utils import override_settings
from django.conf import settings
from django.test import TransactionTestCase
from tastypie.test import ResourceTestCase, TestApiClient
from api.serializers import MultipartSerializer

import socket
import perma.tasks

# for web server
from django.utils.functional import cached_property
import os
import errno
import tempfile
import shutil
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import multiprocessing
from multiprocessing import Process
from contextlib import contextmanager

TEST_ASSETS_DIR = os.path.join(settings.PROJECT_ROOT, "perma/tests/assets")


def copy_file_or_dir(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as e:
        if e.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else:
            raise


@override_settings(ROOT_URLCONF='api.urls', BANNED_IP_RANGES=[])
class ApiResourceTestCase(ResourceTestCase):

    url_base = "/v1"

    server_domain = "perma.dev"
    server_port = 8999
    serve_files = []

    # reduce wait times for testing
    perma.tasks.ROBOTS_TXT_TIMEOUT = perma.tasks.AFTER_LOAD_TIMEOUT = 1

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

    def tearDown(self):
        settings.MEDIA_ROOT = self._media_org
        shutil.rmtree(self._media_tmp)

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
            copy_file_or_dir(os.path.join(cls._cwd_org, file),
                             os.path.basename(file))

        # start server
        cls._httpd = HTTPServer(('', cls.server_port), SimpleHTTPRequestHandler)
        cls._httpd._BaseServer__is_shut_down = multiprocessing.Event()
        cls._server_process = Process(target=cls._httpd.serve_forever)
        cls._server_process.start()

        # once the server is started, we can return to our working dir
        # and the server thread will continue to server from the tmp dir
        os.chdir(cls._cwd_org)

        return cls._server_process

    @classmethod
    def kill_server(cls):
        # If you don't close the server before terminating
        # the thread the port isn't freed up.
        cls._httpd.server_close()
        cls._server_process.terminate()
        shutil.rmtree(cls._server_tmp)

    @contextmanager
    def serve_file(self, src):
        dst = os.path.join(self._server_tmp, os.path.basename(src))
        try:
            copy_file_or_dir(src, dst)
            yield
        finally:
            os.remove(dst)

    @cached_property
    def server_url(self):
        return "http://" + self.server_domain + ":" + str(self.server_port)

    def successful_patch(self, url, user, new_vals):
        old_data = self.deserialize(self.api_client.get(url, format='json'))
        new_data = old_data.copy()
        new_data.update(new_vals)

        # count = Link.objects.count()
        resp = self.api_client.patch(url,
                                     data=new_data,
                                     authentication=self.get_credentials(user))
        self.assertHttpAccepted(resp)

        # Make sure the count hasn't changed & we did an update.
        # self.assertEqual(Link.objects.count(), count)

        fresh_data = self.deserialize(self.api_client.get(url, format='json'))
        for attr in new_vals.keys():
            try:
                # Make sure the data actually changed
                self.assertNotEqual(fresh_data[attr], old_data[attr])
                # Make sure the data changed to what we specified
                self.assertEqual(fresh_data[attr], new_data[attr])
            except AssertionError:
                # If we specified a nested ID, we'll be getting back an object
                if str(new_data[attr]).isdigit() and isinstance(fresh_data[attr], dict):
                    self.assertEqual(new_data[attr], fresh_data[attr]['id'])
                else:
                    raise
            except KeyError:
                pass

        return fresh_data

    def rejected_patch(self, url, user, new_vals):
        old_data = self.deserialize(self.api_client.get(url, format='json'))
        new_data = old_data.copy()
        new_data.update(new_vals)

        # count = Link.objects.count()
        resp = self.api_client.patch(url,
                                     data=new_data,
                                     authentication=self.get_credentials(user))
        self.assertHttpRejected(resp)

        # self.assertEqual(Link.objects.count(), count)
        self.assertEqual(
            self.deserialize(self.api_client.get(url, format='json')),
            old_data)

        return resp


class ApiResourceTransactionTestCase(ApiResourceTestCase):
    """
    For use with threaded tests like archive creation
    See https://github.com/toastdriven/django-tastypie/issues/684#issuecomment-65910589
    Remove when upgraded to Django 1.7?
    """
    _fixture_setup = TransactionTestCase._fixture_setup
    _fixture_teardown = TransactionTestCase._fixture_teardown
