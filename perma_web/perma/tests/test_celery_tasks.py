from django.core import mail

from django.test import TestCase, override_settings
from perma.celery_tasks import update_stats, send_js_errors
from perma.models import UncaughtError

@override_settings(CELERY_ALWAYS_EAGER=True)
class TaskTestCase(TestCase):

    def testUpdateStats(self):
        # this tests only that the task runs,
        # not anything about the task itself
        self.assertTrue(update_stats.delay())

    def test_send_js_errors(self):
        response = send_js_errors()
        self.assertFalse(response)
        self.assertEqual(len(mail.outbox), 0)
        unruly_stack_trace = '[{"function": "getNextContents", "column": 6, "line": 304, "file": "static/bundles/create.js"}, {"function": "showFolderContents", "column": 4, "line": 335, "file": "static/bundles/create.js"}]'
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
