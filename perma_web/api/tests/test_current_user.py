from .utils import ApiResourceTestCase

from perma.models import LinkUser

class CurrentUserResourceTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/api_keys.json']

    def setUp(self):
        super(CurrentUserResourceTestCase, self).setUp()
        self.user = LinkUser.objects.get(email='test_vesting_member@example.com')
        self.detail_url = self.url_base+'/user/'

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url,
                                   format='json',
                                   authentication=self.get_credentials())
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)
        keys = ['id','first_name','last_name']
        self.assertKeys(obj, keys+['resource_uri'])
        for key in keys:
            self.assertEqual(obj[key], getattr(self.user, key))

    def test_get_detail_unauthenticated(self):
        self.assertHttpUnauthorized(self.api_client.get(self.detail_url, format='json'))
