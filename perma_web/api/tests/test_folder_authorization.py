import unittest
from .utils import ApiResourceTestCase
from api.resources import FolderResource
from perma.models import Folder, LinkUser


class FolderAuthorizationTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/api_keys.json']

    def setUp(self):
        super(FolderAuthorizationTestCase, self).setUp()

        self.registry_member = LinkUser.objects.get(pk=1)
        self.registrar_member = LinkUser.objects.get(pk=2)
        self.vesting_member = LinkUser.objects.get(pk=3)
        self.regular_user = LinkUser.objects.get(pk=4)
        self.vesting_manager = LinkUser.objects.get(pk=5)

        self.list_url = "{0}/{1}/".format(self.url_base, FolderResource.Meta.resource_name)

    ############
    # Creating #
    ############

    def test_should_allow_any_logged_in_user_to_create(self):
        count = Folder.objects.count()
        parent = self.regular_user.folders.first()

        self.assertHttpCreated(
            self.api_client.post(self.list_url + str(parent.id) + '/folders/',
                                 data={'name': 'Test Folder'},
                                 authentication=self.get_credentials(self.regular_user)))

        self.assertEqual(Folder.objects.count(), count+1)

    def test_should_reject_create_from_logged_out_user(self):
        count = Folder.objects.count()
        parent = Folder.objects.first()

        self.assertHttpUnauthorized(
            self.api_client.post(self.list_url + str(parent.id) + '/folders/',
                                 data={'name': 'Test Folder'}))

        self.assertEqual(Folder.objects.count(), count)

    ###########
    # Viewing #
    ###########

    @unittest.skip("Pending")
    def test_should_allow_folder_owner_to_view(self):
        pass

    @unittest.skip("Pending")
    def test_should_allow_member_of_folders_registrar_to_view(self):
        pass

    @unittest.skip("Pending")
    def test_should_allow_member_of_folders_vesting_org_to_view(self):
        pass

    @unittest.skip("Pending")
    def test_should_reject_view_from_user_lacking_owner_and_registrar_and_vesting_org_access(self):
        pass

    ###########
    # Editing #
    ###########

    @unittest.skip("Pending")
    def test_should_allow_folder_owner_to_patch_name_and_parent_folder(self):
        pass

    @unittest.skip("Pending")
    def test_should_allow_member_of_folders_registrar_to_patch_name_and_parent_folder(self):
        pass

    @unittest.skip("Pending")
    def test_should_allow_member_of_folders_vesting_org_to_patch_name_and_parent_folder(self):
        pass

    @unittest.skip("Pending")
    def test_should_reject_patch_from_user_lacking_owner_and_registrar_and_vesting_org_access(self):
        pass

    ############
    # Deleting #
    ############

    @unittest.skip("Pending")
    def test_should_allow_folder_owner_to_delete(self):
        pass

    @unittest.skip("Pending")
    def test_should_allow_member_of_folders_registrar_to_delete(self):
        pass

    @unittest.skip("Pending")
    def test_should_allow_member_of_folders_vesting_org_to_delete(self):
        pass

    @unittest.skip("Pending")
    def test_should_reject_delete_from_user_lacking_owner_and_registrar_and_vesting_org_access(self):
        pass
