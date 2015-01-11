from .utils import ApiResourceTestCase

from perma.models import LinkUser


class CurrentUserAuthorizationTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/api_keys.json']

    def setUp(self):
        super(CurrentUserAuthorizationTestCase, self).setUp()
        self.vesting_member = LinkUser.objects.get(pk=3)
        self.regular_user = LinkUser.objects.get(pk=4)
        self.detail_url = self.url_base+'/user/'

    def test_should_allow_user_to_get_self(self):
        self.successful_get(self.detail_url, self.vesting_member)

    def test_get_reject_request_from_unauthenticated_visitor(self):
        self.assertHttpUnauthorized(self.api_client.get(self.detail_url))

    def test_should_provide_different_detail_data_relative_to_user(self):
        vm_data = self.deserialize(
            self.api_client.get(self.detail_url,
                                authentication=self.get_credentials(self.vesting_member)))

        reg_data = self.deserialize(
            self.api_client.get(self.detail_url,
                                authentication=self.get_credentials(self.regular_user)))

        self.assertEqual(vm_data.keys(), reg_data.keys())
        self.assertNotEqual(vm_data, reg_data)

    def test_should_provide_different_list_data_relative_to_user(self):
        vm_data = self.deserialize(
            self.api_client.get(self.detail_url + 'folders/',
                                authentication=self.get_credentials(self.vesting_member)))

        reg_data = self.deserialize(
            self.api_client.get(self.detail_url + 'folders/',
                                authentication=self.get_credentials(self.regular_user)))

        self.assertEqual(vm_data.keys(), reg_data.keys())
        self.assertNotEqual(vm_data['objects'], reg_data['objects'])
