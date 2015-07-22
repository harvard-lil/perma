import os
import dateutil.parser
from .utils import ApiResourceTransactionTestCase, TEST_ASSETS_DIR
from api.resources import LinkResource, CurrentUserLinkResource, PublicLinkResource
from perma.models import Link, LinkUser

from django.core.files.storage import default_storage


# Use a TransactionTestCase here because archive capture is threaded
class LinkResourceTestCase(ApiResourceTransactionTestCase):

    resource = LinkResource
    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/archive.json',
                'fixtures/api_keys.json']

    serve_files = [os.path.join(TEST_ASSETS_DIR, 'target_capture_files/test.html'),
                   os.path.join(TEST_ASSETS_DIR, 'target_capture_files/noarchive.html'),
                   os.path.join(TEST_ASSETS_DIR, 'target_capture_files/test.pdf')]

    rejected_status_code = 400  # Bad Request

    def setUp(self):
        super(LinkResourceTestCase, self).setUp()

        self.vesting_member = LinkUser.objects.get(pk=3)
        self.regular_user = LinkUser.objects.get(pk=4)

        self.unvested_link = Link.objects.get(pk="7CF8-SS4G")
        self.vested_link = Link.objects.get(pk="3SLN-JHX9")

        self.list_url = "{0}/{1}".format(self.url_base, LinkResource.Meta.resource_name)
        self.unvested_link_detail_url = "{0}/{1}".format(self.list_url, self.unvested_link.pk)
        self.vested_link_detail_url = "{0}/{1}".format(self.list_url, self.vested_link.pk)

        self.logged_in_list_url = "{0}/{1}".format(self.url_base, CurrentUserLinkResource.Meta.resource_name)
        self.logged_in_unvested_link_detail_url = "{0}/{1}".format(self.logged_in_list_url, self.unvested_link.pk)

        self.public_list_url = "{0}/{1}".format(self.url_base, PublicLinkResource.Meta.resource_name)
        self.public_vested_link_detail_url = "{0}/{1}".format(self.public_list_url, self.vested_link.pk)

        self.logged_out_fields = [
            'vested',
            'vested_timestamp',
            'title',
            'url',
            'dark_archived',
            'dark_archived_robots_txt_blocked',
            'guid',
            'creation_timestamp',
            'expiration_date',
            'organization',
            'assets',
            'view_count'
        ]
        self.logged_in_fields = self.logged_out_fields + [
            'notes',
            'created_by',
            'dark_archived_by',
            'vested_by_editor',
        ]

        self.post_data = {
            'url': self.server_url + "/test.html",
            'title': 'This is a test page'
        }

    def assertHasAsset(self, link, capture_type):
        """
            Make sure capture of given type was created on disk and stored with this asset.
        """
        asset = link.assets.first()
        self.assertTrue(
            default_storage.exists(os.path.join(asset.base_storage_path, getattr(asset, capture_type))),
            "Failed to create %s for %s." % (capture_type, link.submitted_url))

    #######
    # GET #
    #######

    def test_get_schema_json(self):
        self.successful_get(self.list_url + 'schema/', user=self.vesting_member)

    def test_get_public_schema_json(self):
        self.successful_get(self.public_list_url + 'schema/', user=self.vesting_member)

    def test_get_list_json(self):
        self.successful_get(self.public_list_url, count=2)

    def test_get_detail_json(self):
        self.successful_get(self.public_vested_link_detail_url, fields=self.logged_out_fields)

    ########################
    # URL Archive Creation #
    ########################

    def test_should_create_archive_from_html_url(self):
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/test.html"},
                                   user=self.vesting_member)

        link = Link.objects.get(guid=obj['guid'])
        self.assertHasAsset(link, "image_capture")
        self.assertHasAsset(link, "warc_capture")
        self.assertTrue(link.assets.first().cdx_lines.count() > 0)
        self.assertFalse(link.dark_archived_robots_txt_blocked)
        self.assertEqual(link.submitted_title, "Test title.")

    def test_should_create_archive_from_pdf_url(self):
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/test.pdf"},
                                   user=self.vesting_member)

        link = Link.objects.get(guid=obj['guid'])
        self.assertHasAsset(link, "pdf_capture")

    def test_should_add_http_to_url(self):
        self.successful_post(self.list_url,
                             data={'url': self.server_url.split("//")[1] + "/test.html"},
                             user=self.vesting_member)

    def test_should_dark_archive_when_noarchive_in_html(self):
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/noarchive.html"},
                                   user=self.vesting_member)

        link = Link.objects.get(guid=obj['guid'])
        self.assertTrue(link.dark_archived_robots_txt_blocked)

    def test_should_dark_archive_when_disallowed_in_robots_txt(self):
        with self.serve_file(os.path.join(TEST_ASSETS_DIR, 'target_capture_files/robots.txt')):
            obj = self.successful_post(self.list_url,
                                       data={'url': self.server_url + "/test.html"},
                                       user=self.vesting_member)

        link = Link.objects.get(guid=obj['guid'])
        self.assertTrue(link.dark_archived_robots_txt_blocked)

    #########################
    # File Archive Creation #
    #########################

    def test_should_create_archive_from_pdf_file(self):
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.pdf')) as test_file:
            obj = self.successful_post(self.list_url,
                                       format='multipart',
                                       data=dict(self.post_data.copy(), file=test_file),
                                       user=self.vesting_member)

            link = Link.objects.get(guid=obj['guid'])
            self.assertHasAsset(link, "pdf_capture")
            asset = link.assets.first()
            self.assertEqual(asset.user_upload, True)
            self.assertEqual(asset.user_upload_file_name, 'test.pdf')
            self.assertEqual(asset.pdf_capture, 'upload.pdf')

    def test_should_create_archive_from_jpg_file(self):
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.jpg')) as test_file:
            obj = self.successful_post(self.list_url,
                                       format='multipart',
                                       data=dict(self.post_data.copy(), file=test_file),
                                       user=self.vesting_member)

            link = Link.objects.get(guid=obj['guid'])
            self.assertHasAsset(link, "image_capture")
            asset = link.assets.first()
            self.assertEqual(asset.user_upload, True)
            self.assertEqual(asset.user_upload_file_name, 'test.jpg')
            self.assertEqual(asset.image_capture, 'upload.jpg')

    def test_should_reject_invalid_file(self):
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.html')) as test_file:
            obj = self.rejected_post(self.list_url,
                                     format='multipart',
                                     data=dict(self.post_data.copy(), file=test_file),
                                     user=self.vesting_member)
            self.assertIn('Invalid file', obj.content)

    ############
    # Updating #
    ############

    def test_patch_detail(self):
        self.successful_patch(self.unvested_link_detail_url,
                              user=self.unvested_link.created_by,
                              data={'notes': 'These are new notes',
                                    'title': 'This is a new title'})

    ##################
    # Dark Archiving #
    ##################

    def test_dark_archive(self):
        self.successful_patch(self.unvested_link_detail_url,
                              user=self.unvested_link.created_by,
                              data={'dark_archived': True})

    ###########
    # Vesting #
    ###########

    def test_vesting(self):
        folder = self.vesting_member.organizations.first().folders.first()
        folder_url = "{0}/folders/{1}".format(self.url_base, folder.pk)

        self.successful_put("{0}/archives/{1}".format(folder_url, self.unvested_link.pk),
                            user=self.vesting_member,
                            data={'vested': True})

        obj = self.successful_get(self.unvested_link_detail_url, user=self.vesting_member)
        self.assertTrue(obj['vested'])

        # Make sure it's listed in the folder
        data = self.successful_get(folder_url+"/archives", user=self.vesting_member)
        self.assertIn(obj, data['objects'])

    ##########
    # Moving #
    ##########

    def test_moving(self):
        folder = self.vesting_member.organizations.first().folders.first()
        folder_url = "{0}/folders/{1}".format(self.url_base, folder.pk)

        self.successful_put("{0}/archives/{1}".format(folder_url, self.unvested_link.pk),
                            user=self.vesting_member)

        # Make sure it's listed in the folder
        obj = self.successful_get(self.unvested_link_detail_url, user=self.vesting_member)
        data = self.successful_get(folder_url+"/archives", user=self.vesting_member)
        self.assertIn(obj, data['objects'])

    ############
    # Deleting #
    ############

    def test_delete_detail(self):
        self.successful_delete(self.unvested_link_detail_url, user=self.vesting_member)

    ############
    # Ordering #
    ############

    def test_should_be_ordered_by_creation_timestamp_desc_by_default(self):
        data = self.successful_get(self.logged_in_list_url, user=self.regular_user)
        objs = data['objects']
        for i, obj in enumerate(objs):
            if i > 0:
                self.assertGreaterEqual(dateutil.parser.parse(objs[i - 1]['creation_timestamp']),
                                   dateutil.parser.parse(obj['creation_timestamp']))

    #############
    # Filtering #
    #############

    def test_should_allow_filtering_guid_by_query_string(self):
        data = self.successful_get(self.logged_in_list_url, data={'q': '3SLN'}, user=self.regular_user)
        objs = data['objects']

        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['guid'], '3SLN-JHX9')

    def test_should_allow_filtering_url_by_query_string(self):
        data = self.successful_get(self.logged_in_list_url, data={'q': 'metafilter.com'}, user=self.regular_user)
        objs = data['objects']

        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['url'], 'http://metafilter.com')

    def test_should_allow_filtering_title_by_query_string(self):
        data = self.successful_get(self.logged_in_list_url, data={'q': 'Community Weblog'}, user=self.regular_user)
        objs = data['objects']

        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['title'], 'MetaFilter | Community Weblog')

    def test_should_allow_filtering_notes_by_query_string(self):
        data = self.successful_get(self.logged_in_list_url, data={'q': 'all cool things'}, user=self.regular_user)
        objs = data['objects']

        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['notes'], 'Maybe the source of all cool things on the internet.')
