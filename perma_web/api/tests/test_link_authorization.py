import unittest
import os
from .utils import ApiResourceTestCase
from api.resources import LinkResource
from perma.models import Link, LinkUser

from django.core.files.storage import default_storage


class LinkAuthorizationTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/archive.json',
                'fixtures/api_keys.json']

    def setUp(self):
        super(LinkAuthorizationTestCase, self).setUp()

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
        # if request.user.has_group('registrar_user') and not link.vesting_org.registrar == request.user.registrar:
        #     return HttpResponseRedirect(reverse('single_linky', args=[guid]))

    @unittest.expectedFailure
    def test_should_allow_vesting_user_of_link_vesting_org_to_dark_archive(self):
        self.fail()
        # if request.user.has_group('vesting_user') and not link.vesting_org == request.user.vesting_org:
        #     return HttpResponseRedirect(reverse('single_linky', args=[guid]))
