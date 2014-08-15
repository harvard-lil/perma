import json

from .utils import PermaTestCase
from django.conf import settings
from django.core.urlresolvers import reverse

class ServiceViewsTestCase(PermaTestCase):


    def test_email_confirm(self):
        """
        A user can email a link through the web front end. The variables
        are link and email address.
        """

        # We send from this email. Verify it's in our settings.
        self.assertIn('@', settings.DEFAULT_FROM_EMAIL)

        # TODO: write emails to files and then validate that file
        response = self.client.post(reverse('service_email_confirm'), data={'email_address': 'test@example.com',
            'link_url': 'http://weshouldactuallytestthis.org'})
        self.assertEqual(response.status_code, 200)

        jsoned_response = json.loads(response.content)
        self.assertEqual(True, jsoned_response['sent'])

        # The service needs an email address and a link. If we don't send both we should fail
        response = self.client.post(reverse('service_email_confirm'), data={'email_address': 'test@example.com'})
        self.assertEqual(response.status_code, 400)

    def test_receive_feedback(self):
        """
        A user can email a link through the web front end. The variables
        are link and email address.
        """

        # We send from this email. Verify it's in our settings.
        self.assertIn('@', settings.DEFAULT_FROM_EMAIL)

        data = {'visited_page': 'http://perma.cc/something',
                'feedback_text': 'something about example.com',
                'broken_link': 'http://example.com'}

        # TODO: write emails to files and then validate that file
        response = self.client.post(reverse('service_receive_feedback'), data=data)
        self.assertEqual(response.status_code, 201)

        jsoned_response = json.loads(response.content)
        self.assertEqual('true', jsoned_response['submitted'])
        self.assertIsNotNone(jsoned_response['content'])

    def test_link_status(self):
        """During link creation we can poll the link for its status"""

        response = self.client.post(reverse('service_link_status', kwargs={'guid': 'JJ3S-2Q5N',}))
        self.assertEqual(response.status_code, 200)

        jsoned_response = json.loads(response.content)
        self.assertIsNotNone(jsoned_response['path'])
        self.assertIsNotNone(jsoned_response['source_capture'])
        self.assertIsNotNone(jsoned_response['image_capture'])
        self.assertIsNone(jsoned_response['pdf_capture'])
        self.assertEqual(False, jsoned_response['vested'])
        self.assertEqual(False, jsoned_response['dark_archived'])

        response = self.client.post(reverse('service_link_status', kwargs={'guid': '7CF8-SS4G',}))
        self.assertEqual(response.status_code, 200)

        jsoned_response = json.loads(response.content)
        self.assertIsNotNone(jsoned_response['path'])
        self.assertIsNone(jsoned_response['source_capture'])
        self.assertIsNone(jsoned_response['image_capture'])
        self.assertIsNotNone(jsoned_response['pdf_capture'])
        self.assertEqual(False, jsoned_response['vested'])
        self.assertEqual(False, jsoned_response['dark_archived'])

        response = self.client.post(reverse('service_link_status', kwargs={'guid': '7CF8-JJJJ',}))
        self.assertEqual(response.status_code, 404)