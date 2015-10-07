from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse

from perma.urls import urlpatterns

from .utils import PermaTestCase

class CommonViewsTestCase(PermaTestCase):

    def setUp(self):
        self.users = ['test_user@example.com', 'test_org_user@example.com', 'test_registrar_member@example.com', 'test_registry_member@example.com']

    def test_public_views(self):
        # test static template views
        for urlpattern in urlpatterns:
            if urlpattern.callback.func_name == 'DirectTemplateView':
                resp = self.get(urlpattern.name)

    # Record page

    def assert_can_view_capture(self, guid):
        response = self.get('single_linky', reverse_kwargs={'kwargs':{'guid': guid}})
        self.assertIn("<iframe ", response.content)

    def test_regular_archive(self):
        self.assert_can_view_capture('7CF8-SS4G')
        for user in self.users:
            self.log_in_user(user)
            self.assert_can_view_capture('7CF8-SS4G')

    def test_dark_archive(self):
        response = self.get('single_linky', reverse_kwargs={'kwargs':{'guid': 'ABCD-0001'}})
        self.assertIn("Dark Archive and cannot be displayed.", response.content)
        for user in self.users:
            self.log_in_user(user)
            response = self.get('single_linky', reverse_kwargs={'kwargs': {'guid': 'ABCD-0001'}})
            self.assertIn("only visible to libraries and your Archiving Organization.", response.content)

    def test_dark_archive_robots_txt_blocked(self):
        response = self.get('single_linky', reverse_kwargs={'kwargs': {'guid': 'ABCD-0002'}})
        self.assertIn("Dark Archive and cannot be displayed.", response.content)
        for user in self.users:
            self.log_in_user(user)
            response = self.get('single_linky', reverse_kwargs={'kwargs': {'guid': 'ABCD-0002'}})
            self.assertIn("only visible to libraries and your Archiving Organization.", response.content)

    def test_deleted(self):
        response = self.get('single_linky', reverse_kwargs={'kwargs': {'guid': 'ABCD-0003'}})
        self.assertIn("This record has been deleted.", response.content)

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

    # Misc

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