from functools import wraps
import socket
import os
import errno
import tempfile
import shutil
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
import multiprocessing
from multiprocessing import Process
from contextlib import contextmanager
import urllib.parse
import json

from django.test.utils import override_settings
from django.conf import settings
from django.test import TransactionTestCase, TestCase, SimpleTestCase
from django.utils.functional import cached_property
from rest_framework.test import APIClient

import perma.tasks

TEST_ASSETS_DIR = os.path.join(settings.PROJECT_ROOT, "perma/tests/assets")


def copy_file_or_dir(src, dst):
    dst_dir = os.path.abspath(os.path.dirname(dst))
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)
    try:
        shutil.copytree(src, dst)
    except OSError as e:
        if e.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else:
            raise


class TestHTTPServer(HTTPServer):

    def server_close(self):
        """Called to clean-up the server.

        May be overridden.

        """
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass
        self.socket.close()


class TestHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Subclass SimpleHTTPRequestHandler to permit the sending of custom headers"""
    def end_headers(self):
        response_headers = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('response_headers')
        if response_headers:
            headers = json.loads(response_headers[0])
            for header, value in headers:
                self.send_header(header, value)
        return SimpleHTTPRequestHandler.end_headers(self)


def log_api_call(func):
    """
        Handy wrapper to log all API calls during tests. To enable, use:

         LOG_API_CALLS=1 fab test
    """
    if not os.environ.get('LOG_API_CALLS'):
        return func
    @wraps(func)
    def func_wrapper(self, *args, **kwargs):
        print(func.__name__, "called as user", self.handler._force_user, "with", args, kwargs)
        try:
            result = func(self, *args, **kwargs)
        except Exception as e:
            print("returning exception:", e)
            raise
        print("returning:", result)
        return result
    return func_wrapper

class LoggingAPIClient(APIClient):
    """
        Subclass of DRF's APIClient that uses log_api_call wrapper.
    """
    @log_api_call
    def get(self, *args, **kwargs):
        return super(LoggingAPIClient, self).get(*args, **kwargs)
    @log_api_call
    def post(self, *args, **kwargs):
        return super(LoggingAPIClient, self).post(*args, **kwargs)
    @log_api_call
    def put(self, *args, **kwargs):
        return super(LoggingAPIClient, self).put(*args, **kwargs)
    @log_api_call
    def patch(self, *args, **kwargs):
        return super(LoggingAPIClient, self).patch(*args, **kwargs)
    @log_api_call
    def delete(self, *args, **kwargs):
        return super(LoggingAPIClient, self).delete(*args, **kwargs)


@override_settings(BANNED_IP_RANGES=[])
class ApiResourceTestCaseMixin(SimpleTestCase):

    # TODO: Using the regular ROOT_URLCONF avoids a problem where failing tests print useless error messages,
    # because the 500.html error template includes a {% url %} lookup that isn't included in api.urls.
    # There could be a better way to handle this.
    url_base = "/api/v1"
    rejected_status_code = 401  # Unauthorized

    # reduce wait times for testing
    perma.tasks.ROBOTS_TXT_TIMEOUT = perma.tasks.AFTER_LOAD_TIMEOUT = 1

    def setUp(self):
        super(ApiResourceTestCaseMixin, self).setUp()

        self.api_client = LoggingAPIClient()
        try:
            self.list_url = "{0}{1}".format(self.url_base, self.resource_url)
        except:
            pass

    # def tearDown(self):
    #     # wipe cache -- see https://niwinz.github.io/django-redis/latest/#_testing_with_django_redis
    #     from django_redis import get_redis_connection
    #     get_redis_connection("default").flushall()

    #     return super(ApiResourceTestCaseMixin, self).tearDown()

    def get_credentials(self, user=None):
        user = user or self.user
        return "ApiKey %s" % user.api_key.key



    def detail_url(self, obj):
        return "{0}/{1}".format(self.list_url, obj.pk)

    def get_req_kwargs(self, kwargs):
        req_kwargs = {}
        if kwargs.get('format', None):
            req_kwargs['format'] = kwargs['format']
        if kwargs.get('data', None):
            req_kwargs['data'] = kwargs['data']

        # authentication
        self.api_client.force_authenticate(user=kwargs.get('user', None))

        return req_kwargs

    def successful_get(self, url, **kwargs):
        req_kwargs = self.get_req_kwargs(kwargs)

        resp = self.api_client.get(url, **req_kwargs)
        self.assertHttpOK(resp)
        self.assertValidJSONResponse(resp)
        data = self.deserialize(resp)

        if kwargs.get('fields', None):
            self.assertKeys(data, kwargs['fields'])

        if kwargs.get('count', None):
            self.assertEqual(len(data['objects']), kwargs['count'])

        return data

    def successful_post(self, url, **kwargs):
        req_kwargs = self.get_req_kwargs(kwargs)

        resp = self.api_client.post(url, **req_kwargs)
        self.assertHttpCreated(resp)
        self.assertValidJSONResponse(resp)

        return self.deserialize(resp)

    def successful_put(self, url, **kwargs):
        req_kwargs = self.get_req_kwargs(kwargs)

        resp = self.api_client.put(url, **req_kwargs)
        self.assertHttpOK(resp)

    def successful_patch(self, url, check_results=True, **kwargs):
        req_kwargs = self.get_req_kwargs(kwargs)
        get_kwargs = req_kwargs.copy()
        get_kwargs.pop('data', None)

        new_data = kwargs['data']
        if check_results:
            # Fetch the existing data for comparison.
            resp = self.api_client.get(url, **get_kwargs)
            self.assertHttpOK(resp)
            self.assertValidJSONResponse(resp)
            old_data = self.deserialize(resp)

        patch_resp = self.api_client.patch(url, **req_kwargs)
        self.assertHttpOK(patch_resp)

        if check_results:
            fresh_data = self.deserialize(self.api_client.get(url, **get_kwargs))

            for attr in kwargs['data'].keys():
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

        else:
            return self.deserialize(patch_resp)

    def successful_delete(self, url, **kwargs):
        req_kwargs = self.get_req_kwargs(kwargs)

        self.assertHttpOK(
            self.api_client.get(url, **req_kwargs))

        self.assertHttpAccepted(
            self.api_client.delete(url, **req_kwargs))

        self.assertHttpNotFound(
            self.api_client.get(url, **req_kwargs))

    ### helpers for api requests that should be rejected ###

    def rejected_method(self, method, url, expected_status_code=None, expected_data=None, **kwargs):
        req_kwargs = self.get_req_kwargs(kwargs)

        resp = getattr(self.api_client, method)(url, **req_kwargs)
        self.assertEqual(resp.status_code, expected_status_code or self.rejected_status_code)

        if expected_data:
            self.assertDictEqual(self.deserialize(resp), expected_data)

        return resp

    def rejected_get(self, url, *args, **kwargs):
        return self.rejected_method("get", url, *args, **kwargs)

    def rejected_post(self, url, *args, **kwargs):
        return self.rejected_method("post", url, *args, **kwargs)

    def rejected_put(self, url, *args, **kwargs):
        return self.rejected_method("put", url, *args, **kwargs)

    def rejected_patch(self, url, *args, **kwargs):
        get_kwargs = self.get_req_kwargs(kwargs)
        get_kwargs.pop('data', None)
        get_response = self.api_client.get(url, **get_kwargs)
        old_data = None if get_response.status_code == 401 else self.deserialize(get_response)

        result = self.rejected_method("patch", url, *args, **kwargs)

        if old_data:
            self.assertEqual(self.deserialize(self.api_client.get(url, **get_kwargs)), old_data)

        return result

    def rejected_delete(self, url, *args, **kwargs):
        get_kwargs = self.get_req_kwargs(kwargs)

        result = self.rejected_method("delete", url, *args, **kwargs)

        resp = self.api_client.get(url, **get_kwargs)
        self.assertIn(resp.status_code, [200, 401, 403])  # make sure we don't get a 404 back

        return result

    ### assert methods copied from Tastypie ###

    def deserialize(self, resp):
        return json.loads(str(resp.content, 'utf-8'))

    def assertValidJSONResponse(self, resp):
        # Modified from tastypie to allow 201's as well
        # https://github.com/toastdriven/django-tastypie/blob/master/tastypie/test.py#L448
        self.assertIn(resp.status_code, [200, 201])
        self.assertTrue(resp['Content-Type'].startswith('application/json'))
        return self.deserialize(resp)

    def assertHttpUnauthorized(self, resp):
        """
        Ensures the response is returning a HTTP 401.
        """
        return self.assertEqual(resp.status_code, 401)

    def assertHttpNotFound(self, resp):
        """
        Ensures the response is returning a HTTP 404.
        """
        return self.assertEqual(resp.status_code, 404)

    def assertHttpOK(self, resp):
        """
        Ensures the response is returning a HTTP 200.
        """
        return self.assertEqual(resp.status_code, 200)

    def assertHttpCreated(self, resp):
        """
        Ensures the response is returning a HTTP 201.
        """
        return self.assertEqual(resp.status_code, 201)

    def assertHttpAccepted(self, resp):
        """
        Ensures the response is returning either a HTTP 202 or a HTTP 204.
        """
        self.assertIn(resp.status_code, [202, 204])

    def assertKeys(self, data, expected):
        """
        This method ensures that the keys of the ``data`` match up to the keys
        of ``expected``.

        It covers the (extremely) common case where you want to make sure the
        keys of a response match up to what is expected. This is typically less
        fragile than testing the full structure, which can be prone to data
        changes.
        """
        self.assertEqual(sorted(data.keys()), sorted(expected))


class ApiResourceTestCase(ApiResourceTestCaseMixin, TestCase):
    pass

class ApiResourceTransactionTestCase(ApiResourceTestCaseMixin, TransactionTestCase):
    """
    For use with threaded tests like archive creation
    """
    server_domain = "perma.test"
    server_port = 8999
    serve_files = []

    @classmethod
    def setUpClass(cls):
        super(ApiResourceTestCaseMixin, cls).setUpClass()
        if len(cls.serve_files):
            cls.start_server()

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "_server_process", None):
            cls.kill_server()

    @classmethod
    def start_server(cls):
        """
            Set up a server with some known files to run captures against. Example:

                with run_server_in_temp_folder([
                        'test/assets/test.html',
                        'test/assets/test.pdf',
                        ['test/assets/test.html', 'some_other_url.html']):
                    assert(requests.get("http://localhost/test.html") == contents_of_file("test.html"))
                    assert(requests.get("http://localhost/some_other_url.html") == contents_of_file("test.html"))
        """
        assert socket.gethostbyname(cls.server_domain) in ('0.0.0.0', '127.0.0.1'), "Please add `127.0.0.1 " + cls.server_domain + "` to your hosts file before running this test."

        # Run in temp dir.
        # We have to (implicitly) cwd to this so SimpleHTTPRequestHandler serves the files for us.
        cwd = os.getcwd()
        cls._server_tmp = tempfile.mkdtemp()
        os.chdir(cls._server_tmp)

        # Copy over files to current temp dir, stripping paths.
        for source_file in cls.serve_files:

            # handle single strings
            if isinstance(source_file, str):
                target_url = os.path.basename(source_file)

            # handle tuple like (source_file, target_url)
            else:
                source_file, target_url = source_file

            copy_file_or_dir(os.path.join(settings.PROJECT_ROOT, TEST_ASSETS_DIR, source_file), target_url)

        # start server
        for i in range(100):
            try:
                cls._httpd = TestHTTPServer(('', cls.server_port), TestHTTPRequestHandler)
                break
            except socket.error:
                cls.server_port += 1
        else:
            raise Exception("Cannot find an open port to host TestHTTPServer.")
        cls._httpd._BaseServer__is_shut_down = multiprocessing.Event()
        cls._server_process = Process(target=cls._httpd.serve_forever)
        cls._server_process.start()

        # once the server is started, we can return to our working dir
        # and the server thread will continue to server from the tmp dir
        os.chdir(cwd)

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
        """
            Serve file relative to TEST_ASSETS_DIR.
        """
        if not getattr(self.__class__, "_server_process", None):
            self.__class__.start_server()
        dst = os.path.join(self._server_tmp, os.path.basename(src))
        if os.path.exists(dst):
            raise Exception("%s already exists -- can't serve_file." % dst)
        try:
            copy_file_or_dir(os.path.join(settings.PROJECT_ROOT, TEST_ASSETS_DIR, src), dst)
            yield
        finally:
            os.remove(dst)

    @cached_property
    def server_url(self):
        return "http://" + self.server_domain + ":" + str(self.server_port)
