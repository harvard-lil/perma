from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SimpleHTTPServer import SimpleHTTPRequestHandler
from contextlib import contextmanager
import json
from multiprocessing import Process
import multiprocessing
import os
import socket
import shutil
import tempdir

from django.core.files.storage import default_storage
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.conf import settings

from perma.models import Asset, Folder, Link
from perma.views import link_management
import perma.tasks

from .utils import PermaTestCase


TEST_ASSETS_DIR = os.path.join(settings.PROJECT_ROOT, "perma/tests/assets")

# helpers
@contextmanager
def run_server_in_temp_folder(files=[], port=8999):
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
        for file in files:
            shutil.copyfile(os.path.join(old_cwd, file), os.path.basename(file))

        # start server
        httpd = HTTPServer(('', port), SimpleHTTPRequestHandler)
        httpd._BaseServer__is_shut_down = multiprocessing.Event()
        server_thread = Process(target=httpd.serve_forever)
        server_thread.start()

        try:
            # run body of `with` block
            yield
        finally:
            # shut down server
            server_thread.terminate()


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

    def test_link_create_and_edit(self):
        """
            Test various archive creation scenarios.
            Note that these will return immediately instead of kicking off celery tasks,
            because PermaTestCase sets settings.RUN_TASKS_ASYNC to False.
        """

        # helpers
        def create_link(url):
            return self.get_response_and_asset(reverse('create_link'), {'url': url}, HTTP_USER_AGENT='user_agent')

        # Make sure perma.dev resolves to localhost
        try:
            assert socket.gethostbyname('perma.dev')=='127.0.0.1'
        except (socket.gaierror, AssertionError):
            self.fail("Please add `127.0.0.1 perma.dev` to your hosts file before running this test.")

        # We have to use perma.dev rather than localhost for our test server, because
        # PhantomJS won't proxy requests to localhost.
        # See https://github.com/ariya/phantomjs/issues/11342
        test_server_url = "http://perma.dev:8999"

        # Start test server to run captures against.
        with run_server_in_temp_folder([os.path.join(TEST_ASSETS_DIR, 'target_capture_files/test.html'),
                                        os.path.join(TEST_ASSETS_DIR, 'target_capture_files/test.pdf')]):

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
                self.assertFalse(asset.link.dark_archived_robots_txt_blocked)
                self.assertEqual(asset.link.submitted_title, "Test title.")
                # TODO: check that warc capture works

                # PDF capture.
                response, asset = create_link(test_server_url + "/test.pdf")
                self.assertEqual(response.status_code, 201)
                self.assert_asset_has(asset, "pdf_capture")

                # Invalid URL.
                response, asset = create_link("not_a_real_url")
                self.assertEqual(response.status_code, 400)

                # Non-resolving URL.
                response, asset = create_link("slkdfuiosdfnsdjn.com")
                self.assertEqual(response.status_code, 400)

                # Non-working URL.
                link_management.HEADER_CHECK_TIMEOUT = 1 # only wait 1 second before giving up
                response, asset = create_link("http://192.0.2.1/")
                self.assertEqual(response.status_code, 400)

                ## dark_archive scenarios:

                # noarchive
                with open(os.path.join("noarchive.html"), 'w') as file:
                    file.write('<html><head><meta name="rOboTs" content="foo nOaRcHiVe bar"></head></html>')
                response, asset = create_link(test_server_url + "/noarchive.html")
                self.assertTrue(asset.link.dark_archived_robots_txt_blocked)

                # robots.txt
                with open(os.path.join("robots.txt"), 'w') as file:
                    file.write('User-agent: Perma\nDisallow: /')
                response, asset = create_link(test_server_url + "/test.html")
                self.assertTrue(asset.link.dark_archived_robots_txt_blocked)
                os.remove("robots.txt")
                # TODO: check that robots.txt appears in warc capture


    def test_upload_file(self):
        """
            Test file upload.
        """
        # helpers
        def upload_file(file_name):
            with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', file_name)) as file:
                 return self.get_response_and_asset(
                    reverse('upload_link'),
                    {'title':'test','url':'http://test.com','file':file})

        # Test PDF upload.
        response, asset = upload_file('test.pdf')
        self.assertEqual(response.status_code, 201,
                         "Unexpected response %s: %s" % (response.status_code, response.content))
        self.assert_asset_has(asset, "pdf_capture")

        # Test image upload.
        response, asset = upload_file('test.jpg')
        self.assertEqual(response.status_code, 201,
                         "Unexpected response %s: %s" % (response.status_code, response.content))
        self.assert_asset_has(asset, "image_capture")

        # Test bad file upload.
        response, asset = upload_file('test.html')
        self.assertEqual(response.status_code, 400)


    def test_link_browsing(self):
        test_link = Link.objects.get(guid='7CF8-SS4G')

        # helpers
        def get_folder_by_slug(folder_slug):
            return Folder.objects.get(owned_by__email='test_vesting_member@example.com', slug=folder_slug)

        def submit_to_folder(folder, *args, **kwargs):
            kwargs['reverse_kwargs'] = {'args':[folder.pk]}
            return self.submit_form('folder_contents', *args, **kwargs)

        # Create some folders.
        submit_to_folder(self.logged_in_user.root_folder, {'action': 'new_folder', 'name': 'test'})
        folder1 = get_folder_by_slug('test')
        submit_to_folder(self.logged_in_user.root_folder, {'action': 'new_folder', 'name': 'test2'})
        folder2 = get_folder_by_slug('test2')

        # Move stuff to folder1.
        submit_to_folder(folder1, {'action': 'move_items', 'links': [test_link.pk], 'folders': [folder2.pk]})

        # List folder1
        response = submit_to_folder(folder1)
        self.assertTrue(test_link in response.context['links'])
        self.assertTrue(folder2 in set(folder1.children.all()))

        # Search for link guid -- should work
        response = self.client.get(reverse('folder_contents', args=[folder1.pk]) + "?q=" + test_link.guid)
        self.assertTrue(test_link in response.context['links'])

        # Search folder1 for non-matching string
        response = self.client.get(reverse('folder_contents', args=[folder1.pk]) + "?q=does_not_exist")
        self.assertTrue(len(response.context['links']) == 0)

        # Try to delete folder1 -- shouldn't work because there's stuff in it
        response = submit_to_folder(folder1, {'action': 'delete_folder'})
        self.assertTrue(response.status_code == 400 and 'empty' in response.content)

        # Move stuff back out.
        response = submit_to_folder(self.logged_in_user.root_folder, {'action': 'move_items', 'links': [test_link.pk], 'folders': [folder2.pk]})

        # Now delete it.
        response = submit_to_folder(folder1, {'action': 'delete_folder'})
        self.assertFalse(Folder.objects.filter(pk=folder1.pk).exists())

        # Rename folder2
        response = submit_to_folder(folder2, {'action': 'rename_folder', 'name':'test'})
        self.assertTrue(Folder.objects.get(pk=folder2.pk).name == 'test')

        # Edit link notes.
        self.submit_form('link_browser', {'action': 'save_link_attribute', 'link_id': test_link.pk, 'name': 'notes', 'value': 'test'})
        self.assertTrue(Link.objects.get(pk=test_link.pk).notes == 'test')

        # Edit link title.
        self.submit_form('link_browser', {'action': 'save_link_attribute', 'link_id': test_link.pk, 'name': 'submitted_title', 'value': 'test edit'})
        self.assertTrue(Link.objects.get(pk=test_link.pk).submitted_title == 'test edit')


    def test_vest_link(self):
        # setup -- log in as registrar to trigger vesting org selection code path
        self.log_in_user('test_registrar_member@example.com')
        test_link = Link.objects.get(guid='7CF8-SS4G')

        # first submit should show us a dropdown of vesting orgs (since there are more than one for this registrar)
        response = self.post('vest_link', reverse_kwargs={'args': [test_link.guid]})
        vesting_org_id = response.context['vesting_orgs'][0].pk

        # second submit should show us a dropdown of folders to save vested link to
        response = self.post('vest_link', {'vesting_org': vesting_org_id}, reverse_kwargs={'args': [test_link.guid]})
        folder_id = response.context['folder_tree'][0].pk

        # third submit uses folder_id to actually vest, and should forward
        self.post('vest_link', {'folder': folder_id, 'vesting_org': vesting_org_id}, reverse_kwargs={'args': [test_link.guid]}, require_status_code=302)


    def test_dark_archive_link(self):
        test_link = Link.objects.get(guid='7CF8-SS4G')
        self.post('dark_archive_link', reverse_kwargs={'args': [test_link.guid]}, require_status_code=302)
