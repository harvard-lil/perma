from mock import patch
from datetime import datetime

from django.conf import settings
from django.core import mail

from django.test import TestCase, override_settings
from perma.tasks import update_stats, upload_all_to_internet_archive, upload_to_internet_archive, delete_from_internet_archive, cm_sync, send_js_errors
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
        self.assertTrue(upload_to_internet_archive.delay('ZZZZ-ZZZZ'))

    def testDeleteFromInternetArchive(self):
        # test when GUID does not exist
        with self.assertRaises(Link.DoesNotExist):
            delete_from_internet_archive.delay('ZZZZ-ZZZZ')

    @patch('perma.tasks.logger')
    @patch('perma.tasks.sync_cm_list', autospec=True)
    def test_cm_sync(self, mock_fun, mock_logger):
        mock_fun.return_value = { "import": { "new_subscribers": 10,
                                              "existing_subscribers": 20,
                                              "duplicates_in_import_list": 30,
                                              "uniques_in_import_list": 40 },
                                  "unsubscribe": [] }

        response = cm_sync()

        # check if the data is returned, in one format or another
        self.assertIn('10', response)
        self.assertIn('20', response)
        self.assertIn('30', response)
        self.assertIn('40', response)

        # check that developers are warned about duplicates
        mock_logger.error.assert_called_with("Duplicate reigstrar users sent to Campaign Monitor. Check sync logic.")

        # check contents of sent email
        our_address = settings.DEFAULT_FROM_EMAIL

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "Registrar Users Synced to Campaign Monitor")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [our_address])
        self.assertIn("10", message.body)
        self.assertIn("20", message.body)
        # 30 skipped on purpose: duplicates not in email, on purpose!
        self.assertIn("40", message.body)

    def test_send_js_errors(self):
        response = send_js_errors()
        self.assertFalse(response)
        self.assertEqual(len(mail.outbox), 0)
        unruly_stack_trace = u'[{"function": "getNextContents", "column": 6, "line": 304, "file": "static/bundles/create.js"}, {"function": "showFolderContents", "column": 4, "line": 335, "file": "static/bundles/create.js"}]'
        err = UncaughtError.objects.create(
            message="oh no!",
            current_url="perma.cc/about",
            created_at=datetime.now(),
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
