import os
import dateutil.parser
from .utils import ApiResourceTransactionTestCase, TEST_ASSETS_DIR
from api.resources import LinkResource
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

    def setUp(self):
        super(LinkResourceTestCase, self).setUp()

        self.user = LinkUser.objects.get(email='test_vesting_member@example.com')
        self.user_2 = LinkUser.objects.get(email='test_registrar_member@example.com')
        self.link_1 = Link.objects.get(pk='7CF8-SS4G')

        self.list_url = "{0}/{1}/".format(self.url_base, LinkResource.Meta.resource_name)
        self.detail_url = "{0}{1}/".format(self.list_url, self.link_1.pk)

        self.fields = [
            'vested',
            'vested_timestamp',
            'notes',
            'title',
            'created_by',
            'url',
            'dark_archived',
            'dark_archived_by',
            'dark_archived_robots_txt_blocked',
            'vested_by_editor',
            'guid',
            'creation_timestamp',
            'expiration_date',
            'vesting_org',
            'folders',
            'assets',
            'view_count'
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

    def test_get_list_json(self):
        self.successful_get(self.list_url, count=4)

    def test_get_detail_json(self):
        self.successful_get(self.detail_url, fields=self.fields)

    ########################
    # URL Archive Creation #
    ########################

    def test_should_create_archive_from_html_url(self):
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/test.html"},
                                   user=self.user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertHasAsset(link, "image_capture")
        self.assertHasAsset(link, "warc_capture")
        self.assertFalse(link.dark_archived_robots_txt_blocked)
        self.assertEqual(link.submitted_title, "Test title.")

    def test_should_create_archive_from_pdf_url(self):
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/test.pdf"},
                                   user=self.user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertHasAsset(link, "pdf_capture")

    def test_should_add_http_to_url(self):
        self.successful_post(self.list_url,
                             data={'url': self.server_url.split("//")[1] + "/test.html"},
                             user=self.user)

    def test_should_dark_archive_when_noarchive_in_html(self):
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/noarchive.html"},
                                   user=self.user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertTrue(link.dark_archived_robots_txt_blocked)

    def test_should_dark_archive_when_disallowed_in_robots_txt(self):
        with self.serve_file(os.path.join(TEST_ASSETS_DIR, 'target_capture_files/robots.txt')):
            obj = self.successful_post(self.list_url,
                                       data={'url': self.server_url + "/test.html"},
                                       user=self.user)

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
                                       user=self.user)

            link = Link.objects.get(guid=obj['guid'])
            self.assertHasAsset(link, "pdf_capture")

    def test_should_create_archive_from_jpg_file(self):
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.jpg')) as test_file:
            obj = self.successful_post(self.list_url,
                                       format='multipart',
                                       data=dict(self.post_data.copy(), file=test_file),
                                       user=self.user)

            link = Link.objects.get(guid=obj['guid'])
            self.assertHasAsset(link, "image_capture")

    ############
    # Updating #
    ############

    def test_patch_detail(self):
        self.successful_patch(self.detail_url,
                              user=self.link_1.created_by,
                              data={'notes': 'These are new notes',
                                    'title': 'This is a new title'})

    ############
    # Deleting #
    ############

    def test_delete_detail(self):
        self.successful_delete(self.detail_url, user=self.user)

    ############
    # Ordering #
    ############

    def test_should_be_ordered_by_creation_timestamp_desc_by_default(self):
        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)

        objs = self.deserialize(resp)['objects']

        for i, obj in enumerate(objs):
            if i > 0:
                self.assertGreater(dateutil.parser.parse(objs[i - 1]['creation_timestamp']),
                                   dateutil.parser.parse(obj['creation_timestamp']))

    #############
    # Filtering #
    #############

    def test_should_allow_filtering_guid_by_query_string(self):
        resp = self.api_client.get(self.list_url, data={'q': '3SLN'})
        self.assertValidJSONResponse(resp)

        objs = self.deserialize(resp)['objects']
        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['guid'], '3SLN-JHX9')

    def test_should_allow_filtering_url_by_query_string(self):
        resp = self.api_client.get(self.list_url, data={'q': '1406'})
        self.assertValidJSONResponse(resp)

        objs = self.deserialize(resp)['objects']
        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['url'], 'http://arxiv.org/pdf/1406.3611.pdf')

    def test_should_allow_filtering_title_by_query_string(self):
        resp = self.api_client.get(self.list_url, data={'q': 'Community Weblog'})
        self.assertValidJSONResponse(resp)

        objs = self.deserialize(resp)['objects']
        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['title'], 'MetaFilter | Community Weblog')

    def test_should_allow_filtering_notes_by_query_string(self):
        resp = self.api_client.get(self.list_url, data={'q': 'all cool things'})
        self.assertValidJSONResponse(resp)

        objs = self.deserialize(resp)['objects']
        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['notes'], 'Maybe the source of all cool things on the internet.')
