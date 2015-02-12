from .utils import ApiResourceTestCase

from perma.models import LinkUser


class CurrentUserAuthorizationTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/api_keys.json',
                'fixtures/archive.json']

    def setUp(self):
        super(CurrentUserAuthorizationTestCase, self).setUp()
        self.vesting_member = LinkUser.objects.get(pk=3)
        self.regular_user = LinkUser.objects.get(pk=4)
        self.detail_url = self.url_base+'/user/'

    def test_should_allow_user_to_get_self(self):
        self.successful_get(self.detail_url, user=self.vesting_member)

    def test_get_reject_request_from_unauthenticated_visitor(self):
        self.assertHttpUnauthorized(self.api_client.get(self.detail_url))

    def test_should_provide_different_detail_data_relative_to_user(self):
        vm_data = self.successful_get(self.detail_url, user=self.vesting_member)
        reg_data = self.successful_get(self.detail_url, user=self.regular_user)

        self.assertEqual(vm_data.keys(), reg_data.keys())
        self.assertNotEqual(vm_data, reg_data)

    def test_should_provide_different_folder_data_relative_to_user(self):
        vm_data = self.successful_get(self.detail_url + 'folders/', user=self.vesting_member)
        reg_data = self.successful_get(self.detail_url + 'folders/', user=self.regular_user)

        self.assertEqual(vm_data.keys(), reg_data.keys())
        self.assertNotEqual(vm_data['objects'], reg_data['objects'])

    def test_should_provide_different_archive_data_relative_to_user(self):
        vm_data = self.successful_get(self.detail_url + 'archives/', user=self.vesting_member)
        reg_data = self.successful_get(self.detail_url + 'archives/', user=self.regular_user)

        self.assertEqual(vm_data.keys(), reg_data.keys())
        self.assertNotEqual(vm_data['objects'], reg_data['objects'])

    def test_should_provide_different_vesting_org_data_relative_to_user(self):
        vm_data = self.successful_get(self.detail_url + 'vesting_orgs/', user=self.vesting_member)
        reg_data = self.successful_get(self.detail_url + 'vesting_orgs/', user=self.regular_user)

        self.assertEqual(vm_data.keys(), reg_data.keys())
        self.assertNotEqual(vm_data['objects'], reg_data['objects'])