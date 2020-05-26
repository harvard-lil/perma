from .utils import ApiResourceTestCase
from perma.models import LinkUser, Folder


class FolderAuthorizationTestCase(ApiResourceTestCase):

    resource_url = '/folders'

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = LinkUser.objects.get(pk=1)
        cls.registrar_user = LinkUser.objects.get(pk=2)
        cls.org_user = LinkUser.objects.get(pk=3)
        cls.regular_user = LinkUser.objects.get(pk=4)
        cls.sponsored_user = LinkUser.objects.get(pk=20)
        cls.inactive_sponsored_user = LinkUser.objects.get(pk=22)

        cls.empty_root_folder = Folder.objects.get(pk=22)
        cls.nonempty_root_folder = Folder.objects.get(pk=25)
        cls.regular_user_empty_child_folder = Folder.objects.get(pk=29)
        cls.regular_user_nonempty_child_folder = Folder.objects.get(pk=30)

        cls.third_journal_shared_folder = Folder.objects.get(pk=31)

        cls.test_journal_shared_folder = Folder.objects.get(pk=27)
        cls.test_journal_subfolder_with_link_a = Folder.objects.get(pk=34)
        cls.test_journal_subfolder_with_link_b = Folder.objects.get(pk=35)

        cls.sponsored_folder = Folder.objects.get(pk=60)
        cls.sponsored_subfolder = Folder.objects.get(pk=61)
        cls.sponsored_subsubfolder = Folder.objects.get(pk=64)
        cls.inactive_sponsored_folder = Folder.objects.get(pk=63)
        cls.inactive_sponsored_subfolder = Folder.objects.get(pk=65)

    # helpers

    def nested_url(self, obj):
        return self.detail_url(obj)+"/folders"

    ############
    # Creating #
    ############

    def test_should_allow_logged_in_user_to_create(self):
        self.successful_post(self.nested_url(self.regular_user.root_folder),
                             user=self.regular_user,
                             data={'name': 'Test Folder'})

    def test_should_reject_folder_create_without_parent(self):
        self.rejected_post(self.list_url,
                           user=self.regular_user,
                           expected_status_code=400,
                           data={'name': 'Test Folder'})

    def test_should_reject_create_from_logged_out_user(self):
        self.rejected_post(self.nested_url(self.regular_user.root_folder),
                           data={'name': 'Test Folder'})


    def test_should_reject_create_from_user_without_access_to_parent(self):
        self.rejected_post(self.nested_url(self.regular_user.root_folder),
                           user=self.org_user,
                           expected_status_code=403,
                           data={'name': 'Test Folder'})

    ###########
    # Viewing #
    ###########

    def test_should_allow_folder_owner_to_view(self):
        self.successful_get(self.detail_url(self.nonempty_root_folder), user=self.regular_user)

    def test_should_allow_member_of_folders_registrar_to_view(self):
        self.successful_get(self.detail_url(self.test_journal_shared_folder), user=self.registrar_user)

    def test_should_allow_member_of_folders_org_to_view(self):
        self.successful_get(self.detail_url(self.test_journal_shared_folder), user=self.org_user)

    def test_should_reject_view_from_user_lacking_owner_and_registrar_and_org_access(self):
        self.rejected_get(self.detail_url(self.test_journal_shared_folder),
                          user=self.regular_user,
                          expected_status_code=403)

    ############
    # Renaming #
    ############

    def test_should_allow_nonshared_nonroot_folder_owner_to_rename(self):
        self.successful_patch(self.detail_url(self.regular_user_nonempty_child_folder),
                              user=self.regular_user_nonempty_child_folder.created_by,
                              data={'name': 'A new name'})

    def test_should_reject_rename_from_user_lacking_owner_access(self):
        self.rejected_patch(self.detail_url(self.regular_user_nonempty_child_folder),
                            user=self.registrar_user,
                            expected_status_code=403,
                            data={'name': 'A new name'})

    def test_should_reject_rename_of_shared_folder_from_all_users(self):
        data = {'name': 'A new name'}
        url = self.detail_url(self.test_journal_shared_folder)

        self.rejected_patch(url, user=self.admin_user, data=data, expected_status_code=400)
        self.rejected_patch(url, user=self.registrar_user, data=data, expected_status_code=400)

    def test_should_reject_rename_of_root_folder_from_all_users(self):
        data = {'name': 'A new name'}
        self.rejected_patch(self.detail_url(self.admin_user.root_folder),
                            expected_status_code=400,
                            user=self.admin_user, data=data)

        self.rejected_patch(self.detail_url(self.registrar_user.root_folder),
                            expected_status_code=400,
                            user=self.registrar_user, data=data)

        self.rejected_patch(self.detail_url(self.regular_user.root_folder),
                            expected_status_code=400,
                            user=self.regular_user, data=data)

    def test_should_reject_rename_of_sponsored_root_folder_from_all_users(self):
        data = {'name': 'A new name'}
        self.rejected_patch(self.detail_url(self.sponsored_user.sponsored_root_folder),
                            expected_status_code=400,
                            user=self.admin_user, data=data)
        self.rejected_patch(self.detail_url(self.sponsored_user.sponsored_root_folder),
                            expected_status_code=400,
                            user=self.sponsored_user, data=data)
        self.rejected_patch(self.detail_url(self.sponsored_user.sponsored_root_folder),
                            expected_status_code=403,
                            user=self.registrar_user, data=data)
        self.rejected_patch(self.detail_url(self.sponsored_user.sponsored_root_folder),
                            expected_status_code=403,
                            user=self.regular_user, data=data)

    def test_should_reject_rename_of_sponsored_folder_from_all_users(self):
        data = {'name': 'A new name'}
        self.rejected_patch(self.detail_url(self.sponsored_folder),
                            expected_status_code=400,
                            user=self.admin_user, data=data)
        self.rejected_patch(self.detail_url(self.sponsored_folder),
                            expected_status_code=400,
                            user=self.sponsored_user, data=data)
        self.rejected_patch(self.detail_url(self.sponsored_folder),
                            expected_status_code=400,
                            user=self.registrar_user, data=data)
        self.rejected_patch(self.detail_url(self.sponsored_folder),
                            expected_status_code=403,
                            user=self.regular_user, data=data)

    def test_should_allow_renaming_of_sponsored_subfolder(self):
        self.successful_patch(self.detail_url(self.sponsored_subfolder),
                              expected_status_code=200,
                              user=self.admin_user, data={'name': 'A new name'})
        self.successful_patch(self.detail_url(self.sponsored_subfolder),
                              expected_status_code=200,
                              user=self.admin_user, data={'name': 'Another new name'})
        # is this appropriate?
        self.successful_patch(self.detail_url(self.sponsored_subfolder),
                              expected_status_code=200,
                              user=self.registrar_user, data={'name': 'Yet another new name'})
        self.rejected_patch(self.detail_url(self.sponsored_subfolder),
                            expected_status_code=403,
                            user=self.regular_user, data={'name': 'A new name'})


    ##########
    # Moving #
    ##########

    def successful_folder_move(self, user, parent_folder, child_folder):
        self.successful_put(
            "{0}/folders/{1}".format(self.detail_url(parent_folder), child_folder.pk),
            user=user
        )

        # Make sure move worked
        child_folder.refresh_from_db()
        self.assertEqual(child_folder.parent_id, parent_folder.id)

    def rejected_folder_move(self, user, parent_folder, child_folder, expected_status_code=401):
        original_parent_id = child_folder.parent_id

        self.rejected_put(
            "{0}/folders/{1}".format(self.detail_url(parent_folder), child_folder.pk),
            expected_status_code=expected_status_code,
            user=user
        )

        # Make sure move didn't work
        child_folder.refresh_from_db()
        self.assertEqual(child_folder.parent_id, original_parent_id)
        self.assertNotEqual(child_folder.parent_id, parent_folder.id)

    def test_should_allow_move_to_new_folder_via_put(self):
        # PUT /folders/:new_parent_id/folders/:id
        self.successful_folder_move(self.regular_user_empty_child_folder.owned_by, self.regular_user_nonempty_child_folder, self.regular_user_empty_child_folder)

    def test_should_allow_move_to_new_folder_via_patch(self):
        # PATCH /folders/:id {'parent': new_parent_id}
        child_folder = self.regular_user_empty_child_folder
        parent_folder = self.regular_user_nonempty_child_folder
        self.successful_patch(self.detail_url(child_folder),
                              data={"parent": parent_folder.pk},
                              user=child_folder.owned_by)
        child_folder.refresh_from_db()
        self.assertEqual(child_folder.parent_id, parent_folder.pk)

    def test_should_allow_member_of_folders_registrar_to_move_to_new_parent(self):
        self.successful_folder_move(self.registrar_user, self.registrar_user.root_folder, self.test_journal_subfolder_with_link_b)

    def test_should_allow_member_of_folders_org_to_move_to_new_parent(self):
        self.successful_folder_move(self.org_user, self.org_user.root_folder, self.test_journal_subfolder_with_link_b)

    def test_should_reject_move_of_folder_into_its_own_subfolder(self):
        # move A into B ...
        self.successful_patch(self.detail_url(self.test_journal_subfolder_with_link_a),
                              data={"parent": self.test_journal_subfolder_with_link_b.pk},
                              user=self.org_user)

        # ... then try to move B into A
        self.rejected_patch(self.detail_url(self.test_journal_subfolder_with_link_b),
                            data={"parent": self.test_journal_subfolder_with_link_a.pk},
                            expected_status_code=400,
                            expected_data={"parent": ["A node may not be made a child of any of its descendants."]},
                            user=self.org_user)

    def test_should_reject_move_of_folder_into_itself(self):
        self.rejected_patch(self.detail_url(self.test_journal_subfolder_with_link_b),
                            data={"parent": self.test_journal_subfolder_with_link_b.pk},
                            expected_status_code=400,
                            expected_data={"parent": ["A node may not be made a child of itself."]},
                            user=self.org_user)

    def test_should_reject_move_of_org_shared_folder(self):
        self.rejected_folder_move(self.registrar_user, self.registrar_user.root_folder,
                                  self.test_journal_shared_folder,
                                  expected_status_code=400)

    def test_should_reject_move_of_user_root_folder(self):
        self.rejected_folder_move(self.registrar_user, self.test_journal_shared_folder,
                                  self.registrar_user.root_folder,
                                  expected_status_code=400)

    def test_should_reject_move_to_blank_folder(self):
        self.rejected_patch(self.detail_url(self.regular_user_empty_child_folder),
                            user=self.regular_user_empty_child_folder.owned_by,
                            data={'parent':None},
                            expected_status_code=400,
                            expected_data={"parent": ["This field may not be null."]})

    def test_should_reject_move_of_sponsored_root_folder(self):
        for user in [self.admin_user, self.sponsored_user]:
            self.rejected_folder_move(user, self.sponsored_user.sponsored_root_folder,
                                      user.root_folder,
                                      expected_status_code=400)

    def test_should_reject_move_of_sponsored_root_folder_by_registrar(self):
        self.rejected_folder_move(self.registrar_user, self.sponsored_user.sponsored_root_folder,
                                  self.registrar_user.root_folder,
                                  expected_status_code=403)

    def test_should_reject_move_of_sponsored_folder(self):
        for user in [self.admin_user, self.registrar_user, self.sponsored_user]:
            self.rejected_folder_move(user, self.sponsored_folder,
                                      user.root_folder,
                                      expected_status_code=400)

    def move_sponsored_subfolder(self, user):
        # Move it to personal links...
        self.successful_folder_move(user, user.root_folder, self.sponsored_subfolder)
        self.sponsored_subfolder.refresh_from_db()
        self.sponsored_subsubfolder.refresh_from_db()
        for folder in [self.sponsored_subfolder, self.sponsored_subsubfolder]:
            self.assertFalse(folder.sponsored_by)
            self.assertEqual(folder.owned_by, user)
        # ... and back again
        self.successful_folder_move(user, self.sponsored_folder, self.sponsored_subfolder)
        self.sponsored_subfolder.refresh_from_db()
        self.sponsored_subsubfolder.refresh_from_db()
        for folder in [self.sponsored_subfolder, self.sponsored_subsubfolder]:
            self.assertEqual(folder.sponsored_by, self.sponsored_folder.sponsored_by)
            self.assertEqual(folder.owned_by, self.sponsored_folder.owned_by)

    def test_should_allow_owner_to_move_sponsored_subfolder(self):
        self.move_sponsored_subfolder(self.sponsored_user)

    def test_should_allow_admin_to_move_sponsored_subfolder(self):
        self.move_sponsored_subfolder(self.admin_user)

    def test_should_allow_registrar_to_move_sponsored_subfolder(self):
        # is this appropriate?
        self.move_sponsored_subfolder(self.registrar_user)

    def test_should_reject_other_move_of_sponsored_subfolder(self):
        self.rejected_folder_move(self.regular_user, self.regular_user.root_folder, self.sponsored_subfolder, expected_status_code=403)

    def test_readonly_when_moving_inactive_sposorship_subfolder(self):
        self.assertTrue(self.inactive_sponsored_subfolder.read_only)
        # Move it to personal links...
        self.successful_folder_move(self.inactive_sponsored_user, self.inactive_sponsored_user.root_folder, self.inactive_sponsored_subfolder)
        self.inactive_sponsored_subfolder.refresh_from_db()
        self.assertFalse(self.inactive_sponsored_subfolder.read_only)
        # Move it back...
        self.successful_folder_move(self.inactive_sponsored_user, self.inactive_sponsored_folder, self.inactive_sponsored_subfolder)
        self.inactive_sponsored_subfolder.refresh_from_db()
        self.assertTrue(self.inactive_sponsored_subfolder.read_only)

    # these need refreshing of certain in-memory cls-level fixtures
    def test_should_reject_move_from_user_lacking_owner_and_registrar_and_org_access(self):
        self.test_journal_subfolder_with_link_b.refresh_from_db()
        self.rejected_folder_move(self.regular_user,
                                  self.regular_user.root_folder,
                                  self.test_journal_subfolder_with_link_b,
                                  expected_status_code=403)

    def test_should_reject_move_to_parent_to_which_user_lacks_access(self):
        self.regular_user_empty_child_folder.refresh_from_db()
        self.rejected_folder_move(self.regular_user,
                                  self.org_user.root_folder,
                                  self.regular_user_empty_child_folder,
                                  expected_status_code=403)

    ############
    # Deleting #
    ############

    def test_should_allow_folder_owner_to_delete(self):
        self.successful_delete(self.detail_url(self.regular_user_empty_child_folder),
                               user=self.regular_user_empty_child_folder.created_by)

    def test_should_reject_delete_from_user_lacking_owner_and_registrar_and_org_access(self):
        self.rejected_delete(self.detail_url(self.regular_user_empty_child_folder),
                             expected_status_code=403,
                             user=self.org_user)

    def test_reject_delete_of_shared_folder(self):
        self.rejected_delete(self.detail_url(self.test_journal_shared_folder),
                             expected_status_code=400,
                             expected_data={"error": ["Top-level folders cannot be deleted."]},
                             user=self.org_user)

    def test_reject_delete_of_root_folder(self):
        self.rejected_delete(self.detail_url(self.org_user.root_folder),
                             expected_status_code=400,
                             expected_data={"error": ["Top-level folders cannot be deleted."]},
                             user=self.org_user)

    def test_reject_delete_of_nonempty_folder(self):
        self.rejected_delete(self.detail_url(self.test_journal_subfolder_with_link_b),
                             expected_status_code=400,
                             expected_data={"error": ["Folders can only be deleted if they are empty."]},
                             user=self.org_user)

