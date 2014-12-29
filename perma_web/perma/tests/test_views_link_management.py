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
