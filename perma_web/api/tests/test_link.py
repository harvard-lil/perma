import unittest
import os
from django.test.utils import override_settings
from .utils import ApiResourceTestCase
from api.resources import LinkResource
from perma.models import Link, LinkUser

from django.conf import settings
from django.core.files.storage import default_storage

TEST_ASSETS_DIR = os.path.join(settings.PROJECT_ROOT, "perma/tests/assets")


@override_settings(BANNED_IP_RANGES=[])
class LinkResourceTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/archive.json',
                'fixtures/api_keys.json']

    serve_files = [os.path.join(TEST_ASSETS_DIR, 'target_capture_files/test.html'),
                   os.path.join(TEST_ASSETS_DIR, 'target_capture_files/test.pdf')]

    def setUp(self):
        super(LinkResourceTestCase, self).setUp()

        self.user = LinkUser.objects.get(email='test_vesting_member@example.com')
        self.user_2 = LinkUser.objects.get(email='test_registrar_member@example.com')
        self.link_1 = Link.objects.get(pk='7CF8-SS4G')

        self.list_url = "{0}/{1}/".format(self.url_base, LinkResource.Meta.resource_name)
        self.detail_url = "{0}{1}/".format(self.list_url, self.link_1.pk)

        self.get_data = {
            'vested': False,
            'vested_timestamp': None,
            'notes': '',
            'title': 'arxiv.org',
            'created_by': {'first_name': 'Vesting', 'last_name': 'Member', 'id': 3, 'resource_uri': ''},
            'url': 'http://arxiv.org/pdf/1406.3611.pdf',
            'dark_archived_robots_txt_blocked': False,
            'dark_archived': False,
            'vested_by_editor': None,
            'guid': str(self.link_1.guid),
            'creation_timestamp': '2014-06-16T15:23:24',
            'vesting_org': None,
            'resource_uri': self.detail_url
        }

        self.post_data = {
            'url': self.server_url + "/test.html",
            'title': 'This is a test page'
        }

    def assertHasAsset(self, link, capture_type):
        """
            Make sure capture of given type was created on disk and stored with this asset.
        """
        asset = link.assets.first()
        self.assertTrue(
            default_storage.exists(os.path.join(asset.base_storage_path, getattr(asset, capture_type))),
            "Failed to create %s for %s." % (capture_type, link.submitted_url))

    def get_credentials(self, user=None):
        user = user or self.user
        return self.create_apikey(username=user.email, api_key=user.api_key.key)

    def test_get_list_json(self):
        resp = self.api_client.get(self.list_url, format='json')
        self.assertValidJSONResponse(resp)

        objs = self.deserialize(resp)['objects']
        self.assertEqual(len(objs), 2)
        self.assertKeys(objs[0], self.get_data.keys())

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)
        self.assertKeys(self.deserialize(resp), self.get_data.keys())

    def test_post_list_unauthenticated(self):
        self.assertHttpUnauthorized(self.api_client.post(self.list_url, format='json', data=self.post_data))

    def test_should_create_archive_from_url(self):
        count = Link.objects.count()
        self.assertHttpCreated(self.api_client.post(self.list_url, format='json', data=self.post_data, authentication=self.get_credentials()))
        self.assertEqual(Link.objects.count(), count+1)

        link = Link.objects.latest('creation_timestamp')
        self.assertHasAsset(link, "image_capture")
        self.assertHasAsset(link, "warc_capture")
        self.assertFalse(link.dark_archived_robots_txt_blocked)
        self.assertEqual(link.submitted_title, "Test title.")

    def test_should_create_archive_from_pdf_file(self):
        count = Link.objects.count()
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.pdf')) as test_file:
            data = dict(self.post_data.copy(), file=test_file)
            self.assertHttpCreated(self.api_client.post(self.list_url, format='multipart', data=data, authentication=self.get_credentials()))
            self.assertEqual(Link.objects.count(), count+1)

            link = Link.objects.latest('creation_timestamp')
            self.assertHasAsset(link, "pdf_capture")

    def test_should_create_archive_from_jpg_file(self):
        count = Link.objects.count()
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.jpg')) as test_file:
            data = dict(self.post_data.copy(), file=test_file)
            self.assertHttpCreated(self.api_client.post(self.list_url, format='multipart', data=data, authentication=self.get_credentials()))
            self.assertEqual(Link.objects.count(), count+1)

    def test_should_reject_invalid_file(self):
        count = Link.objects.count()
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.html')) as test_file:
            data = dict(self.post_data.copy(), file=test_file)
            self.assertHttpBadRequest(self.api_client.post(self.list_url, format='multipart', data=data, authentication=self.get_credentials()))
            self.assertEqual(Link.objects.count(), count)

    def test_should_add_http_to_url(self):
        count = Link.objects.count()
        self.assertHttpCreated(self.api_client.post(self.list_url, format='json', data={'url': 'example.com'}, authentication=self.get_credentials()))
        self.assertEqual(Link.objects.count(), count+1)

    def test_should_reject_invalid_ip(self):
        # Confirm that local IP captures are banned by default, then unban for testing.
        with self.settings(BANNED_IP_RANGES=["0.0.0.0/8", "127.0.0.0/8"]):
            count = Link.objects.count()
            self.assertHttpBadRequest(self.api_client.post(self.list_url, format='json', data={'url': 'httpexamplecom'}, authentication=self.get_credentials()))
            self.assertEqual(Link.objects.count(), count)

    def test_should_reject_malformed_url(self):
        count = Link.objects.count()
        self.assertHttpBadRequest(self.api_client.post(self.list_url, format='json', data={'url': 'httpexamplecom'}, authentication=self.get_credentials()))
        self.assertEqual(Link.objects.count(), count)

    def test_should_reject_unresolvable_domain_url(self):
        count = Link.objects.count()
        self.assertHttpBadRequest(self.api_client.post(self.list_url, format='json', data={'url': 'http://this-is-not-a-functioning-url.com'}, authentication=self.get_credentials()))
        self.assertEqual(Link.objects.count(), count)

    @unittest.expectedFailure
    def test_should_reject_unloadable_url(self):
        count = Link.objects.count()
        self.assertHttpBadRequest(self.api_client.post(self.list_url, format='json', data={'url': 'http://www.google.com/this-should-404'}, authentication=self.get_credentials()))
        self.assertEqual(Link.objects.count(), count)

    def test_should_reject_large_url(self):
        count = Link.objects.count()
        self.assertHttpBadRequest(self.api_client.post(self.list_url, format='json', data={'url': 'http://upload.wikimedia.org/wikipedia/commons/9/9e/Balaton_Hungary_Landscape.jpg'}, authentication=self.get_credentials()))
        self.assertEqual(Link.objects.count(), count)

    def test_patch_detail_unauthenticated(self):
        self.assertHttpUnauthorized(self.api_client.patch(self.detail_url, format='json', data={}))

    def test_patch_detail(self):
        # Grab the current data & modify it slightly.
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)
        old_data = self.deserialize(resp)
        new_data = dict(old_data,
                        vested=True,
                        notes='These are test notes',
                        dark_archived=True)

        count = Link.objects.count()
        self.assertHttpAccepted(self.api_client.patch(self.detail_url, format='json', data=new_data, authentication=self.get_credentials()))
        # Make sure the count hasn't changed & we did an update.
        self.assertEqual(Link.objects.count(), count)

        link = Link.objects.get(pk=self.link_1.pk)
        for attr in ['dark_archived', 'vested', 'notes']:
            self.assertNotEqual(getattr(link, attr), old_data[attr])
            self.assertEqual(getattr(link, attr), new_data[attr])

    def test_should_limit_patch_to_link_owner(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)
        old_data = self.deserialize(resp)
        new_data = dict(old_data,
                        vested=True,
                        notes='These are test notes',
                        dark_archived=True)

        self.assertHttpUnauthorized(self.api_client.patch(self.detail_url, format='json', data=new_data, authentication=self.get_credentials(self.user_2)))
        self.assertEqual(self.deserialize(self.api_client.get(self.detail_url, format='json')), old_data)

    @unittest.expectedFailure
    def test_should_allow_registrar_user_of_link_vesting_org_registrar_to_dark_archive(self):
        self.fail()

    @unittest.expectedFailure
    def test_should_allow_vesting_user_of_link_vesting_org_to_dark_archive(self):
        self.fail()

    def test_delete_detail_unauthenticated(self):
        self.assertHttpUnauthorized(self.api_client.delete(self.detail_url, format='json'))

    def test_delete_detail(self):
        self.assertHttpOK(self.api_client.get(self.detail_url, format='json'))
        self.assertHttpAccepted(self.api_client.delete(self.detail_url, format='json', authentication=self.get_credentials()))
        self.assertHttpNotFound(self.api_client.get(self.detail_url, format='json'))

    def test_should_limit_delete_to_link_owner(self):
        self.assertHttpOK(self.api_client.get(self.detail_url, format='json'))
        self.assertHttpUnauthorized(self.api_client.delete(self.detail_url, format='json', authentication=self.get_credentials(self.user_2)))
        # confirm that the link wasn't deleted
        self.assertHttpOK(self.api_client.get(self.detail_url, format='json'))
