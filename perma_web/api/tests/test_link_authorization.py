import os

from django.urls import reverse

from .utils import TEST_ASSETS_DIR, ApiResourceTestCase, ApiResourceTransactionTestCase
from perma.models import Link, LinkUser, Folder, Capture
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from mock import patch


class LinkAuthorizationMixin():

    resource_url = '/archives'
    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/api_keys.json',
                'fixtures/archive.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()


    def setUp(self):
        super(LinkAuthorizationMixin, self).setUp()

        self.admin_user = LinkUser.objects.get(pk=1)
        self.registrar_user = LinkUser.objects.get(pk=2)
        self.org_user = LinkUser.objects.get(pk=3)
        self.regular_user = LinkUser.objects.get(pk=4)
        self.related_org_user = LinkUser.objects.get(pk=5) # belongs to the same org as the one that created the link
        self.unrelated_org_user = LinkUser.objects.get(pk=6)  # belongs to a different org than the one that created the link
        self.firm_registrar_user = LinkUser.objects.get(email="registrar_user@firm.com")
        self.firm_user = LinkUser.objects.get(email="case_one_lawyer@firm.com")
        self.sponsored_user = LinkUser.objects.get(email="test_sponsored_user@example.com")
        self.inactive_sponsored_user = LinkUser.objects.get(email="inactive_sponsored_user@example.com")
        self.over_limit_user = LinkUser.objects.get(email="over_limit_user@example.com")

        self.regular_user_empty_child_folder = Folder.objects.get(pk=29)
        self.firm_folder = Folder.objects.get(name="Some Case")

        self.link = Link.objects.get(pk="3SLN-JHX9")
        self.unrelated_link = Link.objects.get(pk="7CF8-SS4G")
        self.capture_view_link = Link.objects.get(pk="ABCD-0007")
        self.private_link_by_user = Link.objects.get(pk="ABCD-0001")
        self.private_link_by_takedown = Link.objects.get(pk="ABCD-0004")
        self.unlisted_link = Link.objects.get(pk="ABCD-0005")

        self.in_progress_link = Link.objects.get(pk="ABCD-0010")
        self.in_progress_link.archive_timestamp = timezone.now() + timedelta(1)
        self.in_progress_link.save()

        self.public_list_url = reverse('api:public_archives')

        self.list_url = reverse('api:archives')
        self.link_url = self.get_link_url(self.link)
        self.unrelated_link_url = self.get_link_url(self.unrelated_link)
        self.capture_view_link_url = self.get_link_url(self.capture_view_link)
        self.in_progress_link_url = self.get_link_url(self.in_progress_link)

        self.patch_data = {'notes': 'These are new notes',
                           'title': 'This is a new title',
                           'default_to_screenshot_view': True}

    def get_public_link_url(self, link):
        return "{0}/{1}".format(self.public_list_url, link.pk)

    def get_link_url(self, link):
        return "{0}/{1}".format(self.list_url, link.pk)


class LinkAuthorizationTestCase(LinkAuthorizationMixin, ApiResourceTestCase):

    #######
    # GET #
    #######

    def test_should_allow_logged_out_users_to_get_list(self):
        self.successful_get(self.public_list_url)

    def test_should_allow_logged_out_users_to_get_link_detail(self):
        self.successful_get(self.get_public_link_url(self.link))

    def test_should_reject_logged_out_users_getting_private_detail(self):
        self.rejected_get(self.get_public_link_url(self.private_link_by_user),
                          expected_status_code=404)

    def test_should_allow_logged_in_users_to_get_logged_in_list(self):
        self.successful_get(self.list_url, user=self.regular_user)

    def test_should_allow_logged_in_users_to_get_detail_of_own_links(self):
        self.successful_get(self.unrelated_link_url, user=self.org_user)

    def test_should_reject_logged_in_users_getting_detail_of_unowned_links(self):
        self.rejected_get(self.unrelated_link_url, user=self.regular_user,
                          expected_status_code=403)
        self.rejected_get(self.unrelated_link_url, user=self.registrar_user,
                          expected_status_code=403)

    def test_should_reject_logged_out_users_getting_logged_in_list(self):
        self.rejected_get(self.list_url)

    def test_should_reject_logged_out_users_getting_logged_in_detail(self):
        self.rejected_get(self.link_url)

    ###########
    # Editing #
    ###########

    def test_should_allow_link_owner_to_patch_notes_and_title_and_screenshot(self):
        self.successful_patch(self.unrelated_link_url, user=self.org_user, data=self.patch_data)

    def test_should_reject_patch_from_users_who_dont_own_unrelated_link(self):
        self.rejected_patch(self.unrelated_link_url, user=self.registrar_user, data=self.patch_data,
                            expected_status_code=403)
        self.rejected_patch(self.unrelated_link_url, user=self.related_org_user, data=self.patch_data,
                            expected_status_code=403)
        self.rejected_patch(self.unrelated_link_url, user=self.regular_user, data=self.patch_data,
                            expected_status_code=403)

    def test_should_allow_patch_from_staff(self):
        self.successful_patch(self.unrelated_link_url, user=self.admin_user, data=self.patch_data)

    def test_should_allow_link_creator_to_patch_notes_and_title_and_screenshot(self):
        self.successful_patch(self.link_url, user=self.link.created_by, data=self.patch_data)

    def test_should_allow_member_of_links_org_to_patch_notes_and_title(self):
        user = LinkUser.objects.filter(organizations=self.link.organization).first()
        self.successful_patch(self.link_url, user=user, data=self.patch_data)

    def test_should_allow_member_of_links_org_registrar_to_patch_notes_and_title(self):
        registrar = self.link.organization.registrar
        user = LinkUser.objects.filter(registrar=registrar.pk).first()
        self.successful_patch(self.link_url, user=user, data=self.patch_data)

    def test_should_reject_patch_from_user_lacking_owner_and_folder_access(self):
        self.rejected_patch(self.link_url, user=self.unrelated_org_user, data=self.patch_data,
                            expected_status_code=403)


    def test_should_allow_user_to_patch_with_file(self):
        # fix up our old-fashioned test fixture to suit this test:
        # - the archive_timestamp needs to be adjusted so that this link is in the patchable window
        # - warc_size and wacz_size need to be set, as would be the case if this "successful"
        #   capture were properly associated with actual web archive files, which is always
        #   the case outside of tests
        self.link.archive_timestamp = timezone.now() + timedelta(1)
        self.link.warc_size = 1
        self.link.wacz_size = 1
        self.link.save()

        # This link has a warc and a wacz
        self.link.refresh_from_db()
        self.assertTrue(self.link.warc_size)
        self.assertTrue(self.link.wacz_size)

        old_primary_capture = self.link.primary_capture

        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.pdf'), 'rb') as test_file:
            data=test_file.read()
            file_content = SimpleUploadedFile("test.pdf", data, content_type="application/pdf")
            self.successful_patch(self.link_url,
                                  user=self.registrar_user,
                                  format="multipart",
                                  data={'file':file_content})

        self.assertTrue(Capture.objects.filter(link_id=self.link.pk, role='primary').exclude(pk=old_primary_capture.pk).exists())

        # This link now only has a warc, but not a wacz
        self.link.refresh_from_db()
        self.assertTrue(self.link.warc_size)
        self.assertFalse(self.link.wacz_size)


    def test_should_reject_patch_with_file_for_out_of_window_link(self):
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.pdf'), 'rb') as test_file:
            data=test_file.read()
            file_content = SimpleUploadedFile("test.pdf", data, content_type="application/pdf")
            self.rejected_patch(self.link_url,
                                user=self.registrar_user,
                                format="multipart",
                                data={'file':file_content},
                                expected_status_code=400)
        self.successful_get(self.link_url, user=self.org_user)

    def test_should_reject_patch_with_capture_in_progress(self):
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.pdf'), 'rb') as test_file:
            data=test_file.read()
            file_content = SimpleUploadedFile("test.pdf", data, content_type="application/pdf")
            self.rejected_patch(self.in_progress_link_url,
                                user=self.registrar_user,
                                format="multipart",
                                data={'file':file_content},
                                expected_status_code=400)
            file_content.seek(0)
            self.in_progress_link.capture_job.status = 'failed'
            self.in_progress_link.capture_job.save()
            self.successful_patch(self.in_progress_link_url,
                                user=self.registrar_user,
                                format="multipart",
                                data={'file':file_content})


    ######################
    # Private / Unlisted #
    ######################

    def test_should_allow_link_owner_to_toggle_private(self):
        user = self.link.created_by
        self.successful_patch(self.link_url, user=user, data={'is_private': True, 'private_reason': 'user'})
        self.successful_patch(self.link_url, user=user, data={'is_private': False, 'private_reason': None})

    def test_should_allow_member_of_links_org_to_toggle_private(self):
        users_in_org = LinkUser.objects.filter(organizations=self.link.organization)
        self.successful_patch(self.link_url, user=users_in_org[0], data={'is_private': True, 'private_reason':'user'})
        self.successful_patch(self.link_url, user=users_in_org[0], data={'is_private': False, 'private_reason':None})

    def test_should_allow_member_of_links_org_registrar_to_toggle_private(self):
        user = self.link.organization.registrar.users.first()
        self.successful_patch(self.link_url, user=user, data={'is_private': True, 'private_reason': 'user'})
        self.successful_patch(self.link_url, user=user, data={'is_private': False, 'private_reason': None})

    def test_should_reject_private_toggle_from_user_lacking_owner_and_folder_access(self):
        self.rejected_patch(self.link_url, user=self.unrelated_org_user, data={'is_private': True, 'private_reason':'user'},
                            expected_status_code=403)
        self.rejected_patch(self.get_link_url(self.private_link_by_user), user=self.unrelated_org_user, data={'is_private': False, 'private_reason':None},
                            expected_status_code=403)

    def test_should_allow_admin_user_to_toggle_takedown(self):
        self.successful_patch(self.link_url, user=self.admin_user, data={'is_private': True, 'private_reason': 'takedown'})
        self.successful_patch(self.link_url, user=self.admin_user, data={'is_private': False, 'private_reason': None})

    def test_should_ignore_private_reason_from_nonadmin_user(self):
        user = self.link.organization.registrar.users.first()
        self.successful_patch(self.link_url, user=user, data={'is_private': True, 'private_reason': 'takedown'}, check_results=False)
        self.link.refresh_from_db()
        self.assertEqual(self.link.private_reason, 'user')

    def test_should_reject_takedown_toggle_from_nonadmin_user(self):
        user = self.link.organization.registrar.users.first()
        self.rejected_patch(self.get_link_url(self.private_link_by_takedown), user=user, data={'is_private': False, 'private_reason': None},
                            expected_status_code=400)

    ##########
    # Moving #
    ##########

    def successful_link_move(self, user, link, folder):
        archives_url = "{0}/folders/{1}/archives".format(self.url_base, folder.pk)
        self.successful_put("{0}/{1}".format(archives_url, link.pk), user=user)

        # Make sure it's listed in the folder
        obj = self.successful_get("{0}/{1}".format(self.list_url, link.pk), user=user)
        data = self.successful_get(archives_url, user=user)
        self.assertIn(obj['guid'], [obj['guid'] for obj in data['objects']])

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
        self.successful_link_move(self.org_user, self.link, self.link.organization.shared_folder.children.first())

    def test_should_reject_move_to_parent_to_which_user_lacks_access(self):
        self.rejected_link_move(self.regular_user, self.link, self.org_user.root_folder,
                                expected_status_code=403)

    def test_should_reject_move_from_user_lacking_link_owner_access(self):
        self.rejected_link_move(self.regular_user, self.unrelated_link, self.regular_user.root_folder,
                                expected_status_code=403)

    def test_should_reject_delete_for_out_of_window_link(self):
        self.rejected_delete(self.link_url, user=self.org_user,
                             expected_status_code=403)
        self.successful_get(self.link_url, user=self.org_user)

    def test_should_reject_delete_from_users_who_dont_own_link(self):
        self.rejected_delete(self.unrelated_link_url, user=self.regular_user,
                             expected_status_code=403)
        self.rejected_delete(self.unrelated_link_url, user=self.registrar_user,
                             expected_status_code=403)
        self.rejected_delete(self.unrelated_link_url, user=self.related_org_user,
                             expected_status_code=403)
        self.successful_get(self.link_url, user=self.org_user)

    def test_should_reject_delete_with_capture_in_progress(self):
        self.rejected_delete(self.in_progress_link_url, user=self.registrar_user,
                             expected_status_code=400)
        self.in_progress_link.capture_job.status = 'failed'
        self.in_progress_link.capture_job.save()
        self.successful_delete(self.in_progress_link_url, user=self.registrar_user)


class LinkAuthorizationTransactionTestCase(LinkAuthorizationMixin, ApiResourceTransactionTestCase):

    def setUp(self):
        super(LinkAuthorizationTransactionTestCase, self).setUp()
        self.post_data = {'url': self.server_url + "/test.html",
                          'title': 'This is a test page'}

    ############
    # Creating #
    ############

    def test_should_reject_create_to_inaccessible_folder(self):
        inaccessible_folder = self.admin_user.root_folder
        response = self.rejected_post(self.list_url, expected_status_code=400, user=self.regular_user, data=dict(self.post_data, folder=inaccessible_folder.pk))
        self.assertIn(b"Folder not found.", response.content)

    def test_should_reject_create_from_logged_out_user(self):
        self.rejected_post(self.list_url, data=self.post_data)

    @patch('perma.models.Registrar.link_creation_allowed', autospec=True)
    def test_should_reject_create_if_folder_registrar_bad_standing_registrar(self, allowed):
        allowed.return_value = False
        response = self.rejected_post(
            self.list_url,
            expected_status_code=400,
            user=self.firm_registrar_user,
            data=dict(self.post_data,
                      folder=self.firm_folder.pk)
        )
        allowed.assert_called_once_with(self.firm_folder.organization.registrar)
        self.assertIn(b"account needs attention", response.content)
        self.assertIn(b"See your Usage Plan", response.content)

    @patch('perma.models.Registrar.link_creation_allowed', autospec=True)
    def test_should_reject_create_if_folder_registrar_bad_standing_regular(self, allowed):
        allowed.return_value = False
        response = self.rejected_post(
            self.list_url,
            expected_status_code=400,
            user=self.firm_user,
            data=dict(self.post_data,
                      folder=self.firm_folder.pk)
        )
        allowed.assert_called_once_with(self.firm_folder.organization.registrar)
        self.assertIn(b"account needs attention", response.content)
        self.assertIn(b"For assistance, contact: registrar_user@firm.com", response.content)
  
    def test_should_reject_if_over_link_limit_regular(self):
        self.assertEqual(self.over_limit_user.link_limit, 0)
        self.assertFalse(self.over_limit_user.nonpaying)
        response = self.rejected_post(
            self.list_url,
            expected_status_code=400,
            user=self.over_limit_user,
            data=dict(self.post_data)
        )
        self.assertIn(b"Visit your Usage Plan page for information and plan options", response.content)

    @patch('perma.models.LinkUser.get_links_remaining', autospec=True)
    def test_should_reject_if_over_link_limit_nonpaying(self, remaining):
        # fix up the fixture (oh how i long for thee, pytest factoryboy!)
        self.assertEqual(self.over_limit_user.link_limit, 0)
        self.over_limit_user.nonpaying = True
        self.over_limit_user.save()
        self.over_limit_user.refresh_from_db()
        self.assertTrue(self.over_limit_user.nonpaying)
        # set the mock
        remaining.return_value = (0, 'monthly', 0)
        
        response = self.rejected_post(
            self.list_url,
            expected_status_code=400,
            user=self.over_limit_user,
            data=dict(self.post_data)
        )
        self.assertIn(b"Get in touch if you need more", response.content)

    @patch('perma.models.LinkUser.get_links_remaining', autospec=True)
    def test_should_reject_if_over_link_limit_subscription_on_hold(self, remaining):
        # fix up the fixture (oh how i long for thee, pytest factoryboy!)
        self.assertEqual(self.over_limit_user.link_limit, 0)
        self.over_limit_user.cached_subscription_status = 'Hold'
        self.over_limit_user.save()
        self.over_limit_user.refresh_from_db()
        self.assertEqual(self.over_limit_user.cached_subscription_status, 'Hold')
        # set the mock
        remaining.return_value = (0, 'monthly', 0)
        
        response = self.rejected_post(
            self.list_url,
            expected_status_code=400,
            user=self.over_limit_user,
            data=dict(self.post_data)
        )
        self.assertIn(b"Your account needs attention", response.content)

    def test_should_reject_create_if_sponsorship_deactivated(self):
        sponsored_folder = self.inactive_sponsored_user.sponsorships.first().folders.first()
        response = self.rejected_post(self.list_url, expected_status_code=400, user=self.inactive_sponsored_user, data=dict(self.post_data, folder=sponsored_folder.pk))
        self.assertIn(b"set this folder to read-only.", response.content)

    def test_should_reject_create_if_sponsored_root_folder(self):
        sponsored_root_folder = self.sponsored_user.sponsored_root_folder
        response = self.rejected_post(self.list_url, expected_status_code=400, user=self.sponsored_user, data=dict(self.post_data, folder=sponsored_root_folder.pk))
        self.assertIn(b"You can't make links directly in your Sponsored Links folder. Select a folder belonging to a sponsor", response.content)

    # tests for permitted creations in test_link_resource, where the
    # to-be-captured url is actually being served up.
    # this should be fixed.

    ############
    # Deleting #
    ############

    def test_should_allow_owner_to_delete_link(self):
        with self.serve_file('target_capture_files/test.html'):
            successful_response = self.successful_post(self.list_url, user=self.regular_user, data=self.post_data)
            new_link = Link.objects.get(pk=successful_response['guid'])
            new_link_url = "{0}/{1}".format(self.list_url, new_link.pk)
            count = Link.objects.count()
            captures = Capture.objects.filter(link_id=new_link.guid)
            self.assertGreaterEqual(len(captures), 1)
            self.successful_delete(new_link_url, user=self.regular_user)
            self.assertEqual(Link.objects.count(), count-1)
            new_captures = Capture.objects.filter(link_id=new_link.guid)
            self.assertEqual(len(new_captures), 0)
            self.rejected_get(new_link_url, user=self.regular_user, expected_status_code=404)

