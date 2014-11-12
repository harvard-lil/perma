import datetime
from django.test.utils import override_settings
from .utils import ApiResourceTestCase
from api.resources import LinkResource
from perma.models import Link, LinkUser

class LinkResourceTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/archive.json',
                'fixtures/api_keys.json']

    def setUp(self):
        super(LinkResourceTestCase, self).setUp()

        self.user = LinkUser.objects.get(email='test_registry_member@example.com')
        self.link_1 = Link.objects.get(pk='7CF8-SS4G')

        self.list_url = "{0}/{1}/".format(self.url_base, LinkResource.Meta.resource_name)
        self.detail_url = "{0}{1}/".format(self.list_url, self.link_1.pk)

        self.get_data = {
            'vested': False,
            'vested_timestamp': None,
            'notes': '',
            'submitted_title': 'arxiv.org',
            'created_by': {'first_name': 'Vesting', 'last_name': 'Member', 'id': 3, 'resource_uri': ''},
            'submitted_url': 'http://arxiv.org/pdf/1406.3611.pdf',
            'dark_archived_robots_txt_blocked': False,
            'dark_archived': False,
            'vested_by_editor': None,
            'guid': str(self.link_1.guid),
            'creation_timestamp': '2014-06-16T15:23:24',
            'vesting_org': None,
            'resource_uri': self.detail_url
        }
        
        self.post_data = {
            'url': 'http://example.com',
            'title': 'This is a test page'
        }

    def get_credentials(self):
        return self.create_apikey(username=self.user.email, api_key=self.user.api_key.key)

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

    def test_post_list(self):
        # Check how many are there first.
        self.assertEqual(Link.objects.count(), 2)
        self.assertHttpCreated(self.api_client.post(self.list_url, format='json', data=self.post_data, authentication=self.get_credentials()))
        # Verify a new one has been added.
        self.assertEqual(Link.objects.count(), 3)

    def test_put_detail_unauthenticated(self):
        self.assertHttpUnauthorized(self.api_client.put(self.detail_url, format='json', data={}))

    def test_put_detail(self):
        # Grab the current data & modify it slightly.
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)
        original_data = self.deserialize(resp)
        new_data = original_data.copy()
        new_data['url'] = 'Updated: First Post'
        new_data['title'] = '2012-05-01T20:06:12'

        self.assertEqual(Link.objects.count(), 2)
        self.assertHttpAccepted(self.api_client.put(self.detail_url, format='json', data=new_data, authentication=self.get_credentials()))
        # Make sure the count hasn't changed & we did an update.
        self.assertEqual(Link.objects.count(), 2)
        # Check for updated data.
        self.assertEqual(Link.objects.get(pk=25).title, 'Updated: First Post')
        self.assertEqual(Link.objects.get(pk=25).slug, 'first-post')
        self.assertEqual(Link.objects.get(pk=25).created, datetime.datetime(2012, 3, 1, 13, 6, 12))

    def test_delete_detail_unauthenticated(self):
        self.assertHttpUnauthorized(self.api_client.delete(self.detail_url, format='json'))

    def test_delete_detail(self):
        self.assertHttpOK(self.api_client.get(self.detail_url, format='json'))
        self.assertHttpAccepted(self.api_client.delete(self.detail_url, format='json', authentication=self.get_credentials()))
        self.assertHttpNotFound(self.api_client.get(self.detail_url, format='json'))
