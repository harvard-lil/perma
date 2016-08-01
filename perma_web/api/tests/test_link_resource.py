from glob import glob

import os
import dateutil.parser
from django.conf import settings
from surt import surt

from .utils import ApiResourceTransactionTestCase, TEST_ASSETS_DIR
from api.resources import LinkResource, CurrentUserLinkResource, PublicLinkResource
from perma.models import Link, LinkUser, CDXLine


# Use a TransactionTestCase here because archive capture is threaded
class LinkResourceTestCase(ApiResourceTransactionTestCase):

    resource = LinkResource
    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/archive.json',
                'fixtures/api_keys.json']

    serve_files = glob(os.path.join(settings.PROJECT_ROOT, TEST_ASSETS_DIR, 'target_capture_files/*')) + [
        ['target_capture_files/test.html', 'test page.html'],
        ['target_capture_files/test.html', 'subdir/test.html'],

        ['target_capture_files/test.wav', 'test2.wav'],
        ['target_capture_files/test.mp4', 'test2.mp4'],
        ['target_capture_files/test.swf', 'test2.swf'],
        ['target_capture_files/test.swf', 'test3.swf'],
    ]

    rejected_status_code = 400  # Bad Request

    def setUp(self):
        super(LinkResourceTestCase, self).setUp()

        self.org_user = LinkUser.objects.get(pk=3)
        self.regular_user = LinkUser.objects.get(pk=4)

        self.unrelated_link = Link.objects.get(pk="7CF8-SS4G")
        self.link = Link.objects.get(pk="3SLN-JHX9")

        self.list_url = "{0}/{1}".format(self.url_base, LinkResource.Meta.resource_name)
        self.unrelated_link_detail_url = "{0}/{1}".format(self.list_url, self.unrelated_link.pk)
        self.link_detail_url = "{0}/{1}".format(self.list_url, self.link.pk)

        self.logged_in_list_url = "{0}/{1}".format(self.url_base, CurrentUserLinkResource.Meta.resource_name)
        self.logged_in_unrelated_link_detail_url = "{0}/{1}".format(self.logged_in_list_url, self.unrelated_link.pk)

        self.public_list_url = "{0}/{1}".format(self.url_base, PublicLinkResource.Meta.resource_name)
        self.public_link_detail_url = "{0}/{1}".format(self.public_list_url, self.link.pk)

        self.logged_out_fields = [
            'title',
            'url',
            'guid',
            'creation_timestamp',
            'captures',
            'view_count',
            'warc_size',
        ]
        self.logged_in_fields = self.logged_out_fields + [
            'organization',
            'notes',
            'created_by',
            'archive_timestamp',
            'is_private',
            'private_reason',
        ]

        self.post_data = {
            'url': self.server_url + "/test.html",
            'title': 'This is a test page'
        }

    def assertValidCapture(self, capture):
        """
            Make sure capture matches WARC contents.
        """
        self.assertEqual(capture.status, 'success')
        headers, data = capture.link.replay_url(capture.url)
        self.assertTrue(capture.content_type, "Capture is missing a content type.")
        self.assertEqual(capture.content_type.split(';',1)[0], capture.read_content_type().split(';',1)[0])
        data = "".join(data)
        self.assertTrue(data, "Capture data is missing.")

    #######
    # GET #
    #######

    def test_get_schema_json(self):
        self.successful_get(self.list_url + '/schema', user=self.org_user)

    def test_get_public_schema_json(self):
        self.successful_get(self.public_list_url + '/schema', user=self.org_user)

    def test_get_list_json(self):
        self.successful_get(self.public_list_url, count=2)

    def test_get_detail_json(self):
        self.successful_get(self.public_link_detail_url, fields=self.logged_out_fields)

    ########################
    # URL Archive Creation #
    ########################

    def test_should_create_archive_from_html_url(self):
        target_folder = self.org_user.root_folder
        obj = self.successful_post(self.list_url,
                                   data={
                                       'url': self.server_url + "/test.html",
                                       'folder': target_folder.pk,
                                   },
                                   user=self.org_user)

        link = Link.objects.get(guid=obj['guid'])
        cdxlines = CDXLine.objects.filter(link_id=obj['guid'])
        self.assertValidCapture(link.screenshot_capture)
        self.assertValidCapture(link.primary_capture)

        # test favicon captured via meta tag
        self.assertIn("favicon_meta.ico", link.favicon_capture.url)

        self.assertTrue(len(cdxlines) > 0)
        self.assertFalse(link.is_private)
        self.assertEqual(link.submitted_title, "Test title.")

        # check folder
        self.assertTrue(link.folders.filter(pk=target_folder.pk).exists())

    def test_should_create_archive_from_pdf_url(self):
        target_org = self.org_user.organizations.first()
        obj = self.successful_post(self.list_url,
                                   data={
                                       'url': self.server_url + "/test.pdf",
                                       'folder': target_org.shared_folder.pk,
                                   },
                                   user=self.org_user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertValidCapture(link.primary_capture)

        # check folder
        self.assertTrue(link.folders.filter(pk=target_org.shared_folder.pk).exists())
        self.assertEqual(link.organization, target_org)

    def test_should_add_http_to_url(self):
        self.successful_post(self.list_url,
                             data={'url': self.server_url.split("//")[1] + "/test.html"},
                             user=self.org_user)

    def test_should_dark_archive_when_noarchive_in_html(self):
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/noarchive.html"},
                                   user=self.org_user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertTrue(link.is_private)
        self.assertEqual(link.private_reason, "policy")

        # test favicon captured via favicon.ico well-known URL
        self.assertIn("favicon.ico", link.favicon_capture.url)

    def test_should_dark_archive_when_disallowed_in_robots_txt(self):
        with self.serve_file('target_capture_files/robots.txt'):
            obj = self.successful_post(self.list_url,
                                       data={'url': self.server_url + "/subdir/test.html"},
                                       user=self.org_user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertTrue(link.is_private)
        self.assertEqual(link.private_reason, "policy")

    def test_should_accept_spaces_in_url(self):
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/test page.html?a b=c d#e f"},
                                   user=self.org_user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertValidCapture(link.primary_capture)

    def test_should_capture_nested_audio_file(self):
        target_folder = self.org_user.root_folder
        obj = self.successful_post(self.list_url,
                                   data={
                                       'url': self.server_url + "/test_wav_outer.html",
                                       'folder': target_folder.pk,
                                   },
                                   user=self.org_user)

        # verify that embedded /test.* files in iframe were found and captured
        expected_captures = ("test.wav", "test2.wav", "test.mp4", "test2.mp4", "test.swf", "test2.swf", "test3.swf")
        for expected_capture in expected_captures:
            self.assertEqual('200', CDXLine.objects.get(urlkey=surt(self.server_url + "/" + expected_capture), link_id=obj['guid']).parsed['status'])

    #########################
    # File Archive Creation #
    #########################

    def test_should_create_archive_from_pdf_file(self):
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.pdf')) as test_file:
            obj = self.successful_post(self.list_url,
                                       format='multipart',
                                       data=dict(self.post_data.copy(), file=test_file),
                                       user=self.org_user)

            link = Link.objects.get(guid=obj['guid'])
            self.assertValidCapture(link.primary_capture)
            self.assertEqual(link.primary_capture.user_upload, True)

    def test_should_create_archive_from_jpg_file(self):
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.jpg')) as test_file:
            obj = self.successful_post(self.list_url,
                                       format='multipart',
                                       data=dict(self.post_data.copy(), file=test_file),
                                       user=self.org_user)

            link = Link.objects.get(guid=obj['guid'])
            self.assertValidCapture(link.primary_capture)
            self.assertEqual(link.primary_capture.user_upload, True)

    def test_should_reject_invalid_file(self):
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.html')) as test_file:
            obj = self.rejected_post(self.list_url,
                                     format='multipart',
                                     data=dict(self.post_data.copy(), file=test_file),
                                     user=self.org_user)
            self.assertIn('Invalid file', obj.content)

    ############
    # Updating #
    ############

    def test_patch_detail(self):
        self.successful_patch(self.unrelated_link_detail_url,
                              user=self.unrelated_link.created_by,
                              data={'notes': 'These are new notes',
                                    'title': 'This is a new title'})

    def test_should_reject_updates_to_disallowed_fields(self):
        result = self.rejected_patch(self.unrelated_link_detail_url,
                                     user=self.unrelated_link.created_by,
                                     data={'nonexistent_field':'foo'})
        self.assertIn("Only updates on these fields are allowed", result.content)

        result = self.rejected_patch(self.unrelated_link_detail_url,
                                     user=self.unrelated_link.created_by,
                                     data={'url': 'foo'})
        self.assertIn("Only updates on these fields are allowed", result.content)

    ##################
    # Private/public #
    ##################

    def test_dark_archive(self):
        self.successful_patch(self.unrelated_link_detail_url,
                              user=self.unrelated_link.created_by,
                              data={'is_private': True, 'private_reason':'user'})

    ##########
    # Moving #
    ##########

    def test_moving(self):
        folder = self.org_user.organizations.first().folders.first()
        folder_url = "{0}/folders/{1}".format(self.url_base, folder.pk)

        self.successful_put("{0}/archives/{1}".format(folder_url, self.unrelated_link.pk),
                            user=self.org_user)

        # Make sure it's listed in the folder
        obj = self.successful_get(self.unrelated_link_detail_url, user=self.org_user)
        data = self.successful_get(folder_url+"/archives", user=self.org_user)
        self.assertIn(obj, data['objects'])

    ############
    # Deleting #
    ############

    def test_delete_detail(self):
        with self.serve_file('target_capture_files/robots.txt'):
            obj = self.successful_post(self.list_url,
                                       data={'url': self.server_url + "/subdir/test.html"},
                                       user=self.org_user)

            new_link = Link.objects.get(guid=obj['guid'])
            new_link_url = "{0}/{1}".format(self.list_url, new_link.pk)
            self.successful_delete(new_link_url, user=self.org_user)

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
