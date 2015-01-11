import unittest
from .utils import ApiResourceTestCase
from api.resources import FolderResource
from perma.models import LinkUser, Folder


class FolderAuthorizationTestCase(ApiResourceTestCase):

    resource = FolderResource
    assertHttpRejected = ApiResourceTestCase.assertHttpUnauthorized

    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/archive.json',
                'fixtures/api_keys.json']

    def setUp(self):
        super(FolderAuthorizationTestCase, self).setUp()

        self.registry_member = LinkUser.objects.get(pk=1)
        self.registrar_member = LinkUser.objects.get(pk=2)
        self.vesting_member = LinkUser.objects.get(pk=3)
        self.regular_user = LinkUser.objects.get(pk=4)
        self.vesting_manager = LinkUser.objects.get(pk=5)

        self.empty_root_folder = Folder.objects.get(pk=22)
        self.nonempty_root_folder = Folder.objects.get(pk=25)
        self.empty_child_folder = Folder.objects.get(pk=29)
        self.nonempty_child_folder = Folder.objects.get(pk=30)
        self.empty_shared_folder = Folder.objects.get(pk=31)
        self.nonempty_shared_folder = Folder.objects.get(pk=27)

        self.list_url = "{0}/{1}/".format(self.url_base, FolderResource.Meta.resource_name)
        self.nested_url = "{0}folders/".format(self.detail_url(self.nonempty_root_folder))

    def detail_url(self, folder):
        return "{0}{1}/".format(self.list_url, folder.pk)

    ############
    # Creating #
    ############

    def test_should_allow_any_logged_in_user_to_create(self):
        self.assertHttpCreated(
            self.api_client.post(self.nested_url,
                                 data={'name': 'Test Folder'},
                                 authentication=self.get_credentials(self.regular_user)))

    def test_should_reject_create_from_logged_out_user(self):
        self.assertHttpUnauthorized(
            self.api_client.post(self.nested_url,
                                 data={'name': 'Test Folder'}))

    ###########
    # Viewing #
    ###########

    def test_should_allow_folder_owner_to_view(self):
        self.successful_get(self.detail_url(self.nonempty_root_folder), user=self.regular_user)

    def test_should_allow_member_of_folders_registrar_to_view(self):
        self.successful_get(self.detail_url(self.nonempty_shared_folder), user=self.registrar_member)

    def test_should_allow_member_of_folders_vesting_org_to_view(self):
        self.successful_get(self.detail_url(self.nonempty_shared_folder), user=self.vesting_member)

    def test_should_reject_view_from_user_lacking_owner_and_registrar_and_vesting_org_access(self):
        self.rejected_get(self.detail_url(self.nonempty_shared_folder), user=self.regular_user)

    ############
    # Renaming #
    ############

    def test_should_allow_nonshared_nonroot_folder_owner_to_renname(self):
        self.successful_patch(self.detail_url(self.nonempty_child_folder),
                              user=self.nonempty_child_folder.created_by,
                              data={'name': 'A new name'})

    def test_should_reject_rename_from_user_lacking_owner_access(self):
        self.rejected_patch(self.detail_url(self.nonempty_child_folder),
                            user=self.registrar_member,
                            data={'name': 'A new name'})

    def test_should_reject_rename_of_shared_folder_from_all_users(self):
        data = {'name': 'A new name'}
        url = self.detail_url(self.nonempty_shared_folder)

        self.rejected_patch(url, user=self.registry_member,  data=data)
        self.rejected_patch(url, user=self.registrar_member, data=data)
        self.rejected_patch(url, user=self.vesting_manager,  data=data)

    def test_should_reject_rename_of_root_folder_from_all_users(self):
        data = {'name': 'A new name'}
        self.rejected_patch(self.detail_url(self.registry_member.root_folder),
                            user=self.registry_member, data=data)

        self.rejected_patch(self.detail_url(self.registrar_member.root_folder),
                            user=self.registrar_member, data=data)

        self.rejected_patch(self.detail_url(self.vesting_manager.root_folder),
                            user=self.vesting_manager, data=data)

        self.rejected_patch(self.detail_url(self.regular_user.root_folder),
                            user=self.regular_user, data=data)

    ##########
    # Moving #
    ##########

    @unittest.skip("Pending")
    def test_should_allow_folder_owner_to_move_to_new_parent(self):
        pass

    @unittest.skip("Pending")
    def test_should_allow_member_of_folders_registrar_to_move_to_new_parent(self):
        pass

    @unittest.skip("Pending")
    def test_should_allow_member_of_folders_vesting_org_to_move_to_new_parent(self):
        pass

    @unittest.skip("Pending")
    def test_should_reject_move_from_user_lacking_owner_and_registrar_and_vesting_org_access(self):
        pass

    ############
    # Deleting #
    ############

    def test_should_allow_folder_owner_to_delete(self):
        self.successful_delete(self.detail_url(self.empty_child_folder),
                               user=self.empty_child_folder.created_by)

    def test_should_reject_delete_from_user_lacking_owner_and_registrar_and_vesting_org_access(self):
        self.rejected_delete(self.detail_url(self.empty_child_folder),
                             user=self.vesting_member)

    def test_reject_delete_of_shared_folder(self):
        self.rejected_delete(self.detail_url(self.empty_shared_folder),
                             user=self.empty_shared_folder.vesting_org.users.first())

    def test_reject_delete_of_root_folder(self):
        self.rejected_delete(self.detail_url(self.empty_root_folder),
                             user=self.empty_root_folder.created_by)

    def test_reject_delete_of_nonempty_folder(self):
        self.rejected_delete(self.detail_url(self.nonempty_child_folder),
                             user=self.nonempty_child_folder.created_by)
