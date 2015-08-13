from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse

from perma.urls import urlpatterns

from .utils import PermaTestCase

class CommonViewsTestCase(PermaTestCase):

    def test_public_views(self):
        # test static template views
        for urlpattern in urlpatterns:
            if urlpattern.callback.func_name == 'DirectTemplateView':
                resp = self.get(urlpattern.name)

    def test_misformatted_nonexistent_links_404(self):
        response = self.client.get(reverse('single_linky', kwargs={'guid': 'JJ99--JJJJ'}))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('single_linky', kwargs={'guid': '988-JJJJ=JJJJ'}))
        self.assertEqual(response.status_code, 404)

    def test_properly_formatted_nonexistent_links_404(self):
        response = self.client.get(reverse('single_linky', kwargs={'guid': 'JJ99-JJJJ'}))
        self.assertEqual(response.status_code, 404)

        # Test the original ID style. We shouldn't get a redirect.
        response = self.client.get(reverse('single_linky', kwargs={'guid': '0J6pkzDeQwT'}))
        self.assertEqual(response.status_code, 404)

    def test_contact(self):
        # Does our contact form behave reasonably?

        # The form should be fine will all fields
        message_body = 'Just some message here'
        from_email = 'example@example.com'
        self.submit_form('contact', data={
                            'email': from_email,
                            'message': message_body},
                       success_url=reverse('contact_thanks'))

        # check contents of sent email
        message = mail.outbox[0]
        self.assertIn(message_body, message.body)
        self.assertEqual(message.subject, 'New message from Perma contact form')
        self.assertEqual(message.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(message.recipients(), [settings.DEFAULT_FROM_EMAIL])
        self.assertDictEqual(message.extra_headers, {'Reply-To': from_email})

        # We should fail if we don't get a from email
        response = self.client.post(reverse('contact'), data={
                            'email': '',
                            'message': message_body})
        self.assertEqual(response.request['PATH_INFO'], reverse('contact'))

        # We need at least a message. We should get the contact page back
        # instead of the thanks page.
        response = self.client.post(reverse('contact'), data={
                            'email': from_email,
                            'message': ''})
        self.assertEqual(response.request['PATH_INFO'], reverse('contact'))