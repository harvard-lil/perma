from .utils import ApiResourceTestCase

from perma.models import LinkUser


class CurrentUserResourceTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/api_keys.json',
                'fixtures/archive.json']

    def setUp(self):
        super(CurrentUserResourceTestCase, self).setUp()
        self.vesting_member = LinkUser.objects.get(pk=3)
        self.detail_url = self.url_base+'/user/'
        self.fields = [
            'id',
            'first_name',
            'last_name',
            'short_name',
            'full_name',
            'groups'
        ]

    def test_get_self_detail_json(self):
        resp = self.api_client.get(self.detail_url,
                                   authentication=self.get_credentials(self.vesting_member))
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)
        self.assertKeys(obj, self.fields)

    def test_get_archives_json(self):
        resp = self.api_client.get(self.detail_url + 'archives/',
                                   authentication=self.get_credentials(self.vesting_member))
        self.assertValidJSONResponse(resp)
        data = self.deserialize(resp)
        self.assertEqual(len(data['objects']), 1)

    def test_get_folders_json(self):
        resp = self.api_client.get(self.detail_url + 'folders/',
                                   authentication=self.get_credentials(self.vesting_member))
        self.assertValidJSONResponse(resp)
        data = self.deserialize(resp)
        self.assertEqual(len(data['objects']), 2)

    def test_get_vesting_orgs_json(self):
        resp = self.api_client.get(self.detail_url + 'vesting_orgs/',
                                   authentication=self.get_credentials(self.vesting_member))
        self.assertValidJSONResponse(resp)
        data = self.deserialize(resp)
        self.assertEqual(len(data['objects']), 1)
