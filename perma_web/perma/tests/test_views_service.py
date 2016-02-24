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
