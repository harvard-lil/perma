from mock import patch

from django.conf import settings
from django.core import mail

from .utils import PermaTestCase


class ServiceViewTestCase(PermaTestCase):

    def test_cm_sync_get_forbidden(self):
        self.get('service_cm_sync', require_status_code=405)

    def test_cm_sync_post_no_key(self):
        self.post('service_cm_sync', require_status_code=403)

    def test_cm_sync_post_wrong_key(self):
        self.post('service_cm_sync', data={"key": "not_the_key"}, require_status_code=403)

    @patch('perma.views.service.logger')
    @patch('perma.views.service.sync_cm_list', autospec=True)
    def test_cm_sync(self, mock_fun, mock_logger):
        mock_fun.return_value = { "import": { "new_subscribers": 10,
                                              "existing_subscribers": 20,
                                              "duplicates_in_import_list": 30,
                                              "uniques_in_import_list": 40 },
                                  "unsubscribe": [] }
        response = self.post('service_cm_sync', data={"key": settings.INTERNAL_SERVICES_KEY}).content

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

