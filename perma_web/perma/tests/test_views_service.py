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
        self.assertNotEquals(settings.DEFAULT_FROM_EMAIL, '')

        # TODO: write emails to files and then validate that file
        response = self.client.post(reverse('service_email_confirm'), data={'email_address': 'test@example.com',
            'link_url': 'http://weshouldactuallytestthis.org'})
        self.assertEqual(response.status_code, 200)

        # The service needs an email address and a link. If we don't send both we should fail
        response = self.client.post(reverse('service_email_confirm'), data={'email_address': '0J6pkzDeQwT'})
        self.assertEqual(response.status_code, 400)

    def test_email_confirm(self):
        """
        A user can email a link through the web front end. The variables
        are link and email address.
        """

        # We send from this email. Verify it's in our settings.
        self.assertNotEquals(settings.DEFAULT_FROM_EMAIL, '')

        data = {'visited_page': 'http://perma.cc/something',
                'feedback_text': 'something about example.com',
                'broken_link': 'http://example.com'}

        # TODO: write emails to files and then validate that file
        response = self.client.post(reverse('service_receive_feedback'), data=data)
        self.assertEqual(response.status_code, 201)