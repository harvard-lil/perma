import json
import os
import socket
import subprocess
from time import sleep
import tempdir

from django.core.files.storage import default_storage
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.conf import settings

from perma.models import Asset
from perma.views import link_management
import perma.tasks

from .utils import PermaTestCase


TEST_ASSETS_DIR = os.path.join(settings.PROJECT_ROOT, "perma/tests/assets")



@override_settings(MIRRORING_ENABLED=True)
class TasksTestCase(PermaTestCase):

    def setUp(self):
        # Make sure requests go to dashboard server.
        self.client.defaults['SERVER_NAME'] = settings.MIRROR_USERS_SUBDOMAIN + '.perma.dev'

        # Log in.
        self.log_in_user('test_vesting_member@example.com')

        # Temp location for generated media.
        self.temp_dir = tempdir.TempDir()
        self.REAL_MEDIA_ROOT = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = self.temp_dir.name

    def tearDown(self):
        settings.MEDIA_ROOT = self.REAL_MEDIA_ROOT

    ### Helpers ###

    def get_response_and_asset(self, *args, **kwargs):
        """
            Post a request with the given params, parse the result and
            return both the HTTP response and generated Asset object if any.
        """
        response = self.client.post(*args, **kwargs)
        if not response.status_code == 201:
            return response, None
        guid = json.loads(response.content)['linky_id']
        return response, Asset.objects.get(link_id=guid)

    def assert_asset_has(self, asset, capture_type):
        """
            Make sure capture of given type was created on disk and stored with this asset.
        """
        self.assertTrue(
            default_storage.exists(os.path.join(asset.base_storage_path, getattr(asset, capture_type))),
            "Failed to create %s for %s." % (capture_type, asset.link.submitted_url))

    ### Tests ###

    def test_create_link(self):
        """
            Test various archive creation scenarios.
            Note that these will return immediately instead of kicking off celery tasks,
            because PermaTestCase sets settings.RUN_TASKS_ASYNC to False.
        """

        # helpers
        def create_link(url):
            return self.get_response_and_asset(reverse('create_link'), {'url': url}, HTTP_USER_AGENT='user_agent')

        # Start the server we'll try to archive.
        server = subprocess.Popen(['python', '-m', 'SimpleHTTPServer', '8999'], cwd=TEST_ASSETS_DIR)
        sleep(.5) # wait for server to start
        try:

            # We have to use perma.dev rather than localhost for our test server, because
            # PhantomJS won't proxy requests to localhost.
            # See https://github.com/ariya/phantomjs/issues/11342
            test_server_url = "http://perma.dev:8999"

            # Make sure perma.dev resolves to localhost
            try:
                assert socket.gethostbyname('perma.dev')=='127.0.0.1'
            except (socket.gaierror, AssertionError):
                self.fail("Please add `127.0.0.1 perma.dev` to your hosts file before running this test.")

            # Confirm that local IP captures are banned by default, then unban for testing.
            response, asset = create_link(test_server_url)
            self.assertEqual(response.content, "Not a valid IP.", "Request to localhost should have been blocked.")
            with self.settings(BANNED_IP_RANGES=[]):

                # HTML capture.
                perma.tasks.ROBOTS_TXT_TIMEOUT = perma.tasks.AFTER_LOAD_TIMEOUT = 1  # reduce wait times for testing
                response, asset = create_link(test_server_url+"/test.html")
                self.assertEqual(response.status_code, 201, "Unexpected response %s: %s" % (response.status_code ,response.content))
                self.assert_asset_has(asset, "image_capture")
                self.assert_asset_has(asset, "warc_capture")
                self.assertTrue(
                    default_storage.exists(os.path.join(settings.MEDIA_ARCHIVES_ROOT, asset.base_storage_path+".zip")),
                    "Zip archive not created.")
                # TODO: check that warc capture works (maybe in test of landing page)

                # PDF capture.
                response, asset = create_link(test_server_url + "/test.pdf")
                self.assertEqual(response.status_code, 201)
                self.assert_asset_has(asset, "pdf_capture")

                # Invalid URL.
                response, asset = create_link("not_a_real_url")
                self.assertEqual(response.status_code, 400)

                # Non-working URL.
                link_management.HEADER_CHECK_TIMEOUT = 1 # only wait a second before giving up
                response, asset = create_link("http://192.0.2.1/")
                self.assertEqual(response.status_code, 400)

        finally:
            server.terminate()

    def test_upload_file(self):
        """
            Test file upload.
        """
        # helpers
        def upload_file(file_name):
            with open(os.path.join(TEST_ASSETS_DIR, file_name)) as file:
                 return self.get_response_and_asset(
                    reverse('upload_link'),
                    {'title':'test','url':'http://test.com','file':file})

        # Test PDF upload.
        response, asset = upload_file('test.pdf')
        self.assertEqual(response.status_code, 201,
                         "Unexpected response %s: %s" % (response.status_code, response.content))
        self.assert_asset_has(asset, "pdf_capture")

        # Test bad file upload.
        response, asset = upload_file('test.html')
        self.assertEqual(response.status_code, 400)
