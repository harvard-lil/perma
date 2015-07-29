import os
from .utils import ApiResourceTestCase, TEST_ASSETS_DIR
from api.resources import LinkResource, PublicLinkResource
from perma.models import Link, LinkUser, Folder


class LinkAuthorizationTestCase(ApiResourceTestCase):

    resource = LinkResource

    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/api_keys.json',
                'fixtures/archive.json']

    def setUp(self):
        super(LinkAuthorizationTestCase, self).setUp()

        self.registry_member = LinkUser.objects.get(pk=1)
        self.registrar_member = LinkUser.objects.get(pk=2)
        self.vesting_member = LinkUser.objects.get(pk=3)
        self.regular_user = LinkUser.objects.get(pk=4)
        self.vesting_manager = LinkUser.objects.get(pk=5)
        self.unrelated_vesting_member = LinkUser.objects.get(pk=6)  # belongs to a different vesting org than the one vesting this link

        self.regular_user_empty_child_folder = Folder.objects.get(pk=29)

        self.vested_link = Link.objects.get(pk="3SLN-JHX9")
        self.unvested_link = Link.objects.get(pk="7CF8-SS4G")

        self.public_list_url = "{0}/{1}".format(self.url_base, PublicLinkResource.Meta.resource_name)
        self.public_vested_url = "{0}/{1}".format(self.public_list_url, self.vested_link.pk)
        self.public_unvested_url = "{0}/{1}".format(self.public_list_url, self.unvested_link.pk)

        self.list_url = "{0}/{1}".format(self.url_base, LinkResource.Meta.resource_name)
        self.vested_url = "{0}/{1}".format(self.list_url, self.vested_link.pk)
        self.unvested_url = "{0}/{1}".format(self.list_url, self.unvested_link.pk)

        self.post_data = {'url': self.server_url + "/test.html",
                          'title': 'This is a test page'}

        self.patch_data = {'notes': 'These are new notes',
                           'title': 'This is a new title'}


    #######
    # GET #
    #######

    def test_should_allow_logged_out_users_to_get_list(self):
        self.successful_get(self.public_list_url)

    def test_should_allow_logged_out_users_to_get_vested_detail(self):
        self.successful_get(self.public_vested_url)

    def test_should_reject_logged_out_users_getting_unvested_detail(self):
        self.rejected_get(self.public_unvested_url)

    def test_should_allow_logged_in_users_to_get_logged_in_list(self):
        self.successful_get(self.list_url, user=self.regular_user)

    def test_should_allow_logged_in_users_to_get_detail_of_own_links(self):
        self.successful_get(self.unvested_url, user=self.vesting_member)

    def test_should_reject_logged_in_users_getting_detail_of_unowned_links(self):
        self.rejected_get(self.unvested_url, user=self.regular_user)
        self.rejected_get(self.unvested_url, user=self.registrar_member)

    def test_should_reject_logged_out_users_getting_logged_in_list(self):
        self.rejected_get(self.list_url)

    def test_should_reject_logged_out_users_getting_logged_in_detail(self):
        self.rejected_get(self.vested_url)

    ############
    # Creating #
    ############

    def test_should_allow_logged_in_user_to_create(self):
        with self.serve_file(os.path.join(TEST_ASSETS_DIR, 'target_capture_files/test.html')):
            self.successful_post(self.list_url, user=self.regular_user, data=self.post_data)

    def test_should_reject_create_from_logged_out_user(self):
        self.rejected_post(self.list_url, data=self.post_data)

    ###########
    # Editing #
    ###########

    def test_should_allow_unvested_link_owner_to_patch_notes_and_title(self):
        self.successful_patch(self.unvested_url, user=self.vesting_member, data=self.patch_data)

    def test_should_reject_patch_from_users_who_dont_own_unvested_link(self):
        self.rejected_patch(self.unvested_url, user=self.registrar_member, data=self.patch_data)
        self.rejected_patch(self.unvested_url, user=self.vesting_manager, data=self.patch_data)
        self.rejected_patch(self.unvested_url, user=self.regular_user, data=self.patch_data)

    def test_should_allow_patch_from_staff(self):
        self.successful_patch(self.unvested_url, user=self.registry_member, data=self.patch_data)

    def test_should_allow_vested_link_owner_to_patch_notes_and_title(self):
        self.successful_patch(self.vested_url, user=self.vested_link.created_by, data=self.patch_data)

    def test_should_allow_member_of_links_org_to_patch_notes_and_title(self):
        user = LinkUser.objects.filter(organizations=self.vested_link.organization).first()
        self.successful_patch(self.vested_url, user=user, data=self.patch_data)

    def test_should_allow_member_of_links_vesting_registrar_to_patch_notes_and_title(self):
        registrar = self.vested_link.organization.registrar
        user = LinkUser.objects.filter(registrar=registrar.pk).first()
        self.successful_patch(self.vested_url, user=user, data=self.patch_data)

    def test_should_reject_patch_from_user_lacking_owner_and_folder_access(self):
        self.rejected_patch(self.vested_url, user=self.unrelated_vesting_member, data=self.patch_data)

    ###########
    # Vesting #
    ###########

    def test_should_allow_member_of_org_to_vest(self):
        self.successful_patch(self.unvested_url,
                              user=self.vesting_member,
                              data={'vested': True,
                                    'organization': 1,
                                    'folder': 27})

        data = self.successful_get(self.unvested_url, user=self.vesting_member)
        self.assertEqual(data['vested_by_editor']['id'], self.vesting_member.id)

    def test_should_allow_member_of_registrar_to_vest(self):
        self.successful_patch(self.unvested_url,
                              user=self.registrar_member,
                              check_results=False,  # Not checking results because registrar lacks permission to GET pre-patch state of link before it's vested.
                              data={'vested': True,
                                    'organization': 2,
                                    'folder': 28})

        data = self.successful_get(self.unvested_url, user=self.registrar_member)
        self.assertEqual(data['vested_by_editor']['id'], self.registrar_member.id)

    def test_should_allow_member_of_registry_to_vest(self):
        self.successful_patch(self.unvested_url,
                                     user=self.registry_member,
                                     data={'vested': True,
                                           'organization': 2,
                                           'folder': 28})

        data = self.successful_get(self.unvested_url, user=self.registry_member)
        self.assertEqual(data['vested_by_editor']['id'], self.registry_member.id)

    def test_should_reject_vest_from_user_lacking_vesting_privileges(self):
        self.rejected_patch(self.unvested_url,
                            user=self.regular_user,
                            data={'vested': True,
                                  'organization': 1,
                                  'folder': 27})

    def test_should_reject_vest_when_user_doesnt_belong_to_org(self):
        self.rejected_patch(self.unvested_url,
                            user=self.vesting_member,
                            data={'vested': True,
                                  'organization': 2,
                                  'folder': 28})

    ##################
    # Dark Archiving #
    ##################

    def test_should_allow_link_owner_to_dark_archive(self):
        user = self.vested_link.created_by
        self.successful_patch(self.vested_url, user=user, data={'dark_archived': True})
        data = self.successful_get(self.vested_url, user=user)
        self.assertEqual(data['dark_archived_by']['id'], user.id)

    def test_should_allow_member_of_links_org_to_dark_archive(self):
        users_in_org = LinkUser.objects.filter(organizations=self.vested_link.organization)
        self.successful_patch(self.vested_url, user=users_in_org[0], data={'dark_archived': True})
        data = self.successful_get(self.vested_url, user=users_in_org[1])
        self.assertEqual(data['dark_archived_by']['id'], users_in_org[0].id)

    def test_should_allow_member_of_links_vesting_registrar_to_dark_archive(self):
        user = self.vested_link.organization.registrar.users.first()
        self.successful_patch(self.vested_url, user=user, data={'dark_archived': True})
        data = self.successful_get(self.vested_url, user=user)
        self.assertEqual(data['dark_archived_by']['id'], user.id)

    def test_should_reject_dark_archive_from_user_lacking_owner_and_folder_access(self):
        self.rejected_patch(self.vested_url, user=self.unrelated_vesting_member, data={'dark_archived': True})

    ##########
    # Moving #
    ##########

    def successful_link_move(self, user, link, folder):
        archives_url = "{0}/folders/{1}/archives".format(self.url_base, folder.pk)
        self.successful_put("{0}/{1}".format(archives_url, link.pk), user=user)

        # Make sure it's listed in the folder
        obj = self.successful_get("{0}/{1}".format(self.list_url, link.pk), user=user)
        data = self.successful_get(archives_url, user=user)
        self.assertIn(obj, data['objects'])

    def rejected_link_move(self, user, link, folder, expected_status_code=401):
        folder_url = "{0}/folders/{1}".format(self.url_base, folder.pk)
        archives_url = "{0}/archives".format(folder_url)
        try:
            # if the user doesn't have access to the parent
            self.rejected_get(folder_url, user=user)
        except AssertionError:
            self.rejected_put("{0}/{1}".format(archives_url, link.pk), user=user, expected_status_code=expected_status_code)

            # Make sure it's not listed in the folder
            obj = self.successful_get("{0}/{1}".format(self.list_url, link.pk), user=link.created_by)
            data = self.successful_get(archives_url, user=folder.created_by)
            self.assertNotIn(obj, data['objects'])

    def test_should_allow_link_owner_to_move_to_new_folder(self):
        self.successful_link_move(self.vesting_member, self.vested_link, self.vested_link.organization.shared_folder.children.first())

    def test_should_reject_move_of_vested_link_outside_of_shared_folder(self):
        self.rejected_link_move(self.vesting_member, self.vested_link, self.vesting_member.root_folder, expected_status_code=400)

    def test_should_reject_move_to_parent_to_which_user_lacks_access(self):
        self.rejected_link_move(self.regular_user, self.vested_link, self.vesting_member.root_folder)

    def test_should_reject_move_from_user_lacking_link_owner_access(self):
        self.rejected_link_move(self.regular_user, self.unvested_link, self.regular_user.root_folder)

    ############
    # Deleting #
    ############

    def test_should_allow_owner_to_delete_link(self):
        count = Link.objects.count()
        self.successful_delete(self.unvested_url, user=self.vesting_member)
        self.assertEqual(Link.objects.count(), count-1)
        self.rejected_get(self.unvested_url, user=self.vesting_member, expected_status_code=404)

    def test_should_reject_delete_for_vested_link(self):
        self.rejected_delete(self.vested_url, user=self.vesting_member)
        self.successful_get(self.vested_url, user=self.vesting_member)

    def test_should_reject_delete_from_users_who_dont_own_link(self):
        self.rejected_delete(self.unvested_url, user=self.regular_user)
        self.rejected_delete(self.unvested_url, user=self.registrar_member)
        self.rejected_delete(self.unvested_url, user=self.vesting_manager)
        self.successful_get(self.vested_url, user=self.vesting_member)
