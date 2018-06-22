from glob import glob

import os
import dateutil.parser
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import StreamingHttpResponse
from io import StringIO
from surt import surt
import json
import urllib.request, urllib.parse, urllib.error
from mock import patch

from .utils import ApiResourceTransactionTestCase, TEST_ASSETS_DIR
from perma.models import Link, LinkUser, CDXLine, Folder


# Use a TransactionTestCase here because archive capture is threaded
class LinkResourceTestCase(ApiResourceTransactionTestCase):

    resource_url = '/archives'
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
        self.firm_user = LinkUser.objects.get(email="case_one_lawyer@firm.com")
        self.firm_folder = Folder.objects.get(name="Some Case")

        self.unrelated_link = Link.objects.get(pk="7CF8-SS4G")
        self.unrelated_private_link = Link.objects.get(pk="ABCD-0001")
        self.link = Link.objects.get(pk="3SLN-JHX9")

        self.unrelated_link_detail_url = "{0}/{1}".format(self.list_url, self.unrelated_link.pk)
        self.link_detail_url = "{0}/{1}".format(self.list_url, self.link.pk)

        self.logged_in_list_url = self.list_url
        self.logged_in_unrelated_link_detail_url = reverse('api:archives', args=[self.unrelated_link.pk])
        self.logged_in_private_link_download_url = reverse('api:archives_download', args=[self.unrelated_private_link.pk])

        self.public_list_url = reverse('api:public_archives')
        self.public_link_detail_url = reverse('api:public_archives', args=[self.link.pk])
        self.public_link_download_url = reverse('api:public_archives_download', args=[self.link.pk])
        self.public_link_download_url_for_private_link = reverse('api:public_archives_download', args=[self.unrelated_private_link.pk])

        self.logged_out_fields = [
            'title',
            'description',
            'url',
            'guid',
            'creation_timestamp',
            'captures',
            'warc_size',
            'warc_download_url',
            'queue_time',
            'capture_time',
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
            'title': 'This is a test page',
            'description': 'This is a test description'
        }

    def assertValidCapture(self, capture):
        """
            Make sure capture matches WARC contents.
        """
        self.assertEqual(capture.status, 'success')
        replay_response = capture.replay()
        self.assertTrue(capture.content_type, "Capture is missing a content type.")
        self.assertEqual(capture.content_type.split(';',1)[0], replay_response.headers.get('content-type', '').split(';',1)[0])
        self.assertTrue(replay_response.data, "Capture data is missing.")

    #######
    # GET #
    #######

    def test_get_list_json(self):
        self.successful_get(self.public_list_url, count=4)

    def test_get_detail_json(self):
        self.successful_get(self.public_link_detail_url, fields=self.logged_out_fields)

    @patch('api.views.stream_warc', autospec=True)
    def test_public_download(self, stream):
        stream.return_value = StreamingHttpResponse(StringIO("warc placeholder"))
        resp = self.api_client.get(self.public_link_download_url)
        self.assertHttpOK(resp)
        self.assertEqual(stream.call_count, 1)

    def test_private_download_at_public_url(self):
        self.rejected_get(self.public_link_download_url_for_private_link, expected_status_code=404)

    def test_private_download_unauthenticated(self):
        self.rejected_get(self.logged_in_private_link_download_url, expected_status_code=401)

    def test_private_download_unauthorized(self):
        self.rejected_get(
            self.logged_in_private_link_download_url,
            expected_status_code=403,
            user=self.firm_user
        )

    @patch('perma.utils.stream_warc', autospec=True)
    def test_private_download(self, stream):
        stream.return_value = StreamingHttpResponse(StringIO("warc placeholder"))
        self.api_client.force_authenticate(user=self.regular_user)
        resp = self.api_client.get(
            self.logged_in_private_link_download_url,
        )
        self.assertHttpOK(resp)
        self.assertEqual(stream.call_count, 1)

    ########################
    # URL Archive Creation #
    ########################

    # This doesn't really belong here. Try to readdress.
    @patch('perma.models.Registrar.link_creation_allowed', autospec=True)
    def test_should_permit_create_if_folder_registrar_good_standing(self, allowed):
        allowed.return_value = True
        self.rejected_post(
            self.list_url,
            expected_status_code=201,
            user=self.firm_user,
            data=dict(self.post_data,
                      folder=self.firm_folder.pk)
        )
        allowed.assert_called_once_with(self.firm_folder.organization.registrar)


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

        self.assertEqual(link.submitted_description, "Test description.")

        # check folder
        self.assertTrue(link.folders.filter(pk=target_folder.pk).exists())


    @patch('perma.models.Registrar.link_creation_allowed', autospec=True)
    def test_should_create_archive_from_pdf_url(self, allowed):
        target_org = self.org_user.organizations.first()
        allowed.return_value = True
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
        allowed.assert_called_once_with(target_org.shared_folder.organization.registrar)


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
        with self.serve_file('extra_capture_files/robots.txt'):
            obj = self.successful_post(self.list_url,
                                       data={'url': self.server_url + "/subdir/test.html"},
                                       user=self.org_user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertTrue(link.is_private)
        self.assertEqual(link.private_reason, "policy")

    def test_should_dark_archive_when_disallowed_in_xrobots_simple(self):
        headers = urllib.parse.quote(json.dumps([("x-robots-tag", "noarchive")]))
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/test.html?response_headers=" + headers},
                                   user=self.org_user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertTrue(link.is_private)
        self.assertEqual(link.private_reason, "policy")

    def test_should_dark_archive_when_disallowed_in_xrobots_perma(self):
        headers = urllib.parse.quote(json.dumps([("x-robots-tag", "perma: noarchive")]))
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/test.html?response_headers=" + headers},
                                   user=self.org_user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertTrue(link.is_private)
        self.assertEqual(link.private_reason, "policy")

    def test_should_dark_archive_when_disallowed_in_xrobots_multi(self):
        headers = urllib.parse.quote(json.dumps([
            ("x-robots-tag", "noindex"),
            ("x-robots-tag", "perma: noarchive"),
            ("x-robots-tag", "noindex"),
        ]))
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/test.html?response_headers=" + headers},
                                   user=self.org_user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertTrue(link.is_private)
        self.assertEqual(link.private_reason, "policy")

    def test_should_dark_archive_when_disallowed_in_xrobots_malformed(self):
        headers = urllib.parse.quote(json.dumps([
            ("x-robots-tag", "noindex"),
            ("x-robots-tag", "google: perma: noarchive"),
            ("x-robots-tag", "noindex"),
        ]))
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/test.html?response_headers=" + headers},
                                   user=self.org_user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertTrue(link.is_private)
        self.assertEqual(link.private_reason, "policy")

    def test_should_not_dark_archive_when_allowed_in_xrobots(self):
        headers = urllib.parse.quote(json.dumps([
            ("x-robots-tag", "noindex"),
            ("x-robots-tag", "perma: noindex"),
            ("x-robots-tag", "noindex"),
        ]))
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/test.html?response_headers=" + headers},
                                   user=self.org_user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertFalse(link.is_private)

    def test_should_not_dark_archive_when_allowed_in_xrobots_complex(self):
        headers = urllib.parse.quote(json.dumps([
            ("x-robots-tag", "noindex"),
            ("x-robots-tag", "perma: noindex"),
            ("x-robots-tag", "google: noarchive"),
        ]))
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/test.html?response_headers=" + headers},
                                   user=self.org_user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertFalse(link.is_private)

    def test_should_accept_spaces_in_url(self):
        obj = self.successful_post(self.list_url,
                                   data={'url': self.server_url + "/test page.html?a b=c d#e f"},
                                   user=self.org_user)

        link = Link.objects.get(guid=obj['guid'])
        self.assertValidCapture(link.primary_capture)

    def test_media_capture_in_iframes(self):
        settings.ENABLE_AV_CAPTURE = True
        target_folder = self.org_user.root_folder
        obj = self.successful_post(self.list_url,
                                   data={
                                       'url': self.server_url + "/test_media_outer.html",
                                       'folder': target_folder.pk,
                                   },
                                   user=self.org_user)

        # verify that all images in src and srcset were found and captured
        expected_captures = (
            # test_media_a.html
            "test.wav", "test2.wav",
            # test_media_b.html
            "test.mp4", "test2.mp4",
            # test_media_c.html
            "test.swf", "test2.swf", "test3.swf",
            "test1.jpg", "test2.png", "test_fallback.jpg",
            "wide1.png", "wide2.png", "narrow.png"
        )
        failures = []
        for expected_capture in expected_captures:
            try:
                cdxline = CDXLine.objects.get(urlkey=surt(self.server_url + "/" + expected_capture), link_id=obj['guid'])
                if cdxline.parsed['status'] != '200':
                    failures.append("%s returned HTTP status %s." % (expected_capture, cdxline.parsed['status']))
            except CDXLine.DoesNotExist:
                failures.append("%s not captured." % expected_capture)
        self.assertFalse(bool(failures), "Failures in fetching media from iframes: %s" % failures)

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
                                    'title': 'This is a new title',
                                    'description': 'This is a new description'})

    def test_should_reject_updates_to_disallowed_fields(self):
        result = self.rejected_patch(self.unrelated_link_detail_url,
                                     user=self.unrelated_link.created_by,
                                     data={'url':'foo'})
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
        with self.serve_file('extra_capture_files/robots.txt'):
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

        self.assertEqual(len(objs), 2)
        self.assertEqual(objs[0]['url'], 'http://metafilter.com')

    def test_should_allow_filtering_title_by_query_string(self):
        data = self.successful_get(self.logged_in_list_url, data={'q': 'Community Weblog'}, user=self.regular_user)
        objs = data['objects']

        self.assertEqual(len(objs), 2)
        self.assertEqual(objs[0]['title'], 'MetaFilter | Community Weblog')

    def test_should_allow_filtering_notes_by_query_string(self):
        data = self.successful_get(self.logged_in_list_url, data={'q': 'all cool things'}, user=self.regular_user)
        objs = data['objects']

        self.assertEqual(len(objs), 2)
        self.assertEqual(objs[1]['notes'], 'Maybe the source of all cool things on the internet.')

    def test_should_allow_filtering_url(self):
        data = self.successful_get(self.logged_in_list_url, data={'url': 'metafilter'}, user=self.regular_user)
        objs = data['objects']

        self.assertEqual(len(objs), 2)
        self.assertEqual(objs[0]['title'], 'MetaFilter | Community Weblog')

    def test_should_allow_filtering_by_date_and_query(self):
        data = self.successful_get(self.logged_in_list_url, data={'url': 'metafilter','date':"2016-12-07T18:55:37Z"}, user=self.regular_user)
        objs = data['objects']

        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['title'], 'MetaFilter | Community Weblog')
        self.assertEqual(objs[0]['notes'], 'Maybe the source of all cool things on the internet. Second instance.')

    def test_should_allow_filtering_by_date_range_and_query(self):
        data = self.successful_get(self.logged_in_list_url, data={
            'url': 'metafilter',
            'min_date':"2016-12-06T18:55:37Z",
            'max_date':"2016-12-08T18:55:37Z",
        }, user=self.regular_user)
        objs = data['objects']

        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['title'], 'MetaFilter | Community Weblog')
        self.assertEqual(objs[0]['notes'], 'Maybe the source of all cool things on the internet. Second instance.')
