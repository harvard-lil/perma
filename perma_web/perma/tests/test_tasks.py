from mock import patch
import requests

from django.core import mail

from django.test import TestCase, override_settings
from perma.tasks import update_stats, upload_all_to_internet_archive, upload_to_internet_archive, delete_from_internet_archive, send_js_errors, verify_webrecorder_api_available
from perma.models import Link, UncaughtError

@override_settings(CELERY_ALWAYS_EAGER=True, UPLOAD_TO_INTERNET_ARCHIVE=True)
class TaskTestCase(TestCase):

    def testUpdateStats(self):
        # this tests only that the task runs,
        # not anything about the task itself
        self.assertTrue(update_stats.delay())

    def testUploadAllToInternetArchive(self):
        # this tests only that the task runs,
        # not anything about the task itself
        self.assertTrue(upload_all_to_internet_archive.delay())

    def testUploadToInternetArchive(self):
        # test when GUID does not exist
        with self.assertRaises(Link.DoesNotExist):
            upload_to_internet_archive.delay('ZZZZ-ZZZZ')

    def testDeleteFromInternetArchive(self):
        # test when GUID does not exist
        with self.assertRaises(Link.DoesNotExist):
            delete_from_internet_archive.delay('ZZZZ-ZZZZ')

    def test_send_js_errors(self):
        response = send_js_errors()
        self.assertFalse(response)
        self.assertEqual(len(mail.outbox), 0)
        unruly_stack_trace = u'[{"function": "getNextContents", "column": 6, "line": 304, "file": "static/bundles/create.js"}, {"function": "showFolderContents", "column": 4, "line": 335, "file": "static/bundles/create.js"}]'
        err = UncaughtError.objects.create(
            message="oh no!",
            current_url="perma.cc/about",
            stack=unruly_stack_trace)
        err.save()

        response = send_js_errors()
        self.assertTrue(response)

        message = mail.outbox[0]
        message_parts = message.body.split('\n')
        self.assertIn('URL: %s' % err.current_url, message_parts)
        self.assertIn('Message: %s' % err.message, message_parts)
        self.assertIn('Function: getNextContents', message_parts)
        self.assertIn('File: static/bundles/create.js', message_parts)
        self.assertNotIn('showFolderContents', message_parts)

    def test_verify_webrecorder_api_available(self):
        # this test really verifies that Webrecorder is available in the test environment,
        # as well as testing the task
        self.assertTrue(verify_webrecorder_api_available.delay())

    @patch('perma.tasks.requests.get')
    def test_verify_webrecorder_api_available_fails(self, mocked_get):
        response = requests.Response()
        for code in [400, 404, 500, 502]:
            response.status_code = code
            mocked_get.return_value = response
            with self.assertRaises(requests.exceptions.RequestException):
                self.assertFalse(verify_webrecorder_api_available.delay())
