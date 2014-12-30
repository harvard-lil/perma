import unittest
from .utils import ApiResourceTestCase
from api.resources import FolderResource
from perma.models import Folder, LinkUser


class FolderAuthorizationTestCase(ApiResourceTestCase):

    ############
    # Creating #
    ############

    @unittest.skip("Pending")
    def test_should_allow_any_logged_in_user_to_create(self):
        pass

    @unittest.skip("Pending")
    def test_should_reject_create_from_logged_out_user(self):
        pass

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
