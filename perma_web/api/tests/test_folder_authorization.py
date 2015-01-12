import unittest
from .utils import ApiResourceTestCase
from api.resources import FolderResource
from perma.models import LinkUser, Folder


class FolderAuthorizationTestCase(ApiResourceTestCase):

    resource = FolderResource
    assertHttpRejected = ApiResourceTestCase.assertHttpUnauthorized

    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/groups.json',
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

    ############
    # Creating #
    ############

    def test_should_allow_any_logged_in_user_to_create(self):
        self.successful_post(self.nested_url,
                             user=self.regular_user,
                             data={'name': 'Test Folder'})

    def test_should_reject_create_from_logged_out_user(self):
        self.rejected_post(self.nested_url,
                           data={'name': 'Test Folder'})

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

    def successful_folder_move(self, user, parent_folder, child_folder):
        self.successful_put(
            "{0}folders/{1}/".format(self.detail_url(parent_folder), child_folder.pk),
            user=user
        )

        # Make sure it's listed in the folder
        obj = self.successful_get(self.detail_url(child_folder), user=user)
        data = self.successful_get(self.detail_url(parent_folder)+"folders/", user=user)
        self.assertIn(obj, data['objects'])

    def rejected_folder_move(self, user, parent_folder, child_folder):
        try:
            # if the user doesn't have access to the parent
            self.rejected_get(self.detail_url(parent_folder), user=user)
        except AssertionError:
            self.rejected_put(
                "{0}folders/{1}/".format(self.detail_url(parent_folder), child_folder.pk),
                user=user
            )

            # Make sure it's not listed in the folder
            obj = self.successful_get(self.detail_url(child_folder), user=child_folder.created_by)
            data = self.successful_get(self.detail_url(parent_folder)+"folders/", user=parent_folder.created_by)
            self.assertNotIn(obj, data['objects'])

    def test_should_allow_folder_owner_to_move_to_new_parent(self):
        self.successful_folder_move(self.empty_child_folder.created_by, self.nonempty_child_folder, self.empty_child_folder)

    # This is failing on save with a tree_id None failure. Should it even be allowed?
    @unittest.expectedFailure
    def test_should_allow_member_of_folders_registrar_to_move_to_new_parent(self):
        self.successful_folder_move(self.registrar_member, self.nonempty_shared_folder, self.empty_shared_folder)

    @unittest.expectedFailure
    def test_should_allow_member_of_folders_vesting_org_to_move_to_new_parent(self):
        self.successful_folder_move(self.vesting_member, self.nonempty_shared_folder, self.empty_shared_folder)

    def test_should_reject_move_to_parent_to_which_user_lacks_access(self):
        self.rejected_folder_move(self.regular_user, self.vesting_member.folders.first(), self.regular_user.folders.first())

    def test_should_reject_move_from_user_lacking_owner_and_registrar_and_vesting_org_access(self):
        self.rejected_folder_move(self.regular_user, self.regular_user.folders.first(), self.vesting_member.folders.first())

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
