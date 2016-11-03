from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse

from perma.urls import urlpatterns

from .utils import PermaTestCase

from bs4 import BeautifulSoup

class CommonViewsTestCase(PermaTestCase):

    def setUp(self):
        self.users = ['test_user@example.com', 'test_org_user@example.com', 'test_registrar_user@example.com', 'test_admin_user@example.com']

    def test_public_views(self):
        # test static template views
        for urlpattern in urlpatterns:
            if urlpattern.callback.func_name == 'DirectTemplateView':
                self.get(urlpattern.name)

    # Record page

    def assert_can_view_capture(self, guid):
        response = self.get('single_linky', reverse_kwargs={'kwargs':{'guid': guid}})
        self.assertIn("<iframe ", response.content)

    def test_regular_archive(self):
        self.assert_can_view_capture('3SLN-JHX9')
        for user in self.users:
            self.log_in_user(user)
            self.assert_can_view_capture('3SLN-JHX9')

    def test_dark_archive(self):
        response = self.get('single_linky', reverse_kwargs={'kwargs':{'guid': 'ABCD-0001'}})
        self.assertIn("This record is private and cannot be displayed.", response.content)

        # check that top bar is displayed to logged-in users
        for user in self.users:
            self.log_in_user(user)
            response = self.get('single_linky', reverse_kwargs={'kwargs': {'guid': 'ABCD-0001'}})
            self.assertIn("This record is private.", response.content)

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

    def test_replacement_link(self):
        response = self.client.get(reverse('single_linky', kwargs={'guid': 'ABCD-0006'}))
        self.assertRedirects(response, reverse('single_linky', kwargs={'guid': '3SLN-JHX9'}))

    # Contact Form

    def test_contact_render(self):
        '''
            Does the contact form render as expected?
        '''
        message = "Just a little message"
        subject = "A subject in the GET params"
        flag = "zzzz-zzzz"
        flag_message = "http://perma.cc/{} contains material that is inappropriate.".format(flag)
        flag_subject = "Reporting Inappropriate Content"

        ## check all fields are blank with normal access
        response = self.get('contact').content
        soup = BeautifulSoup(response, 'html.parser')
        inputs = soup.select('input')
        self.assertEqual(len(inputs), 4)
        for input in inputs:
            self.assertIn(input['name'],['csrfmiddlewaretoken', 'referer', 'email', 'subject'])
            if input['name'] == 'csrfmiddlewaretoken':
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))
        textareas = soup.select('textarea')
        self.assertEqual(len(textareas), 1)
        for textarea in textareas:
            self.assertIn(textarea['name'],['message'])
            self.assertEqual(textarea.text, "\r\n")

        ## check subject line, message, read in from GET params
        response = self.get('contact', query_params={ 'message': message,
                                                      'subject': subject }).content
        soup = BeautifulSoup(response, 'html.parser')
        subject_field = soup.find('input', {'name': 'subject'})
        self.assertEqual(subject_field.get('value', ''), subject)
        message_field = soup.find('textarea', {'name': 'message'})
        self.assertEqual(message_field.text, "\r\n" + message)

        ## check flag read in from GET params, and that it's subject/message override other GET params
        response = self.get('contact', query_params={ 'flag': flag,
                                                      'message': message,
                                                      'subject': subject }).content
        soup = BeautifulSoup(response, 'html.parser')
        subject_field = soup.find('input', {'name': 'subject'})
        self.assertEqual(subject_field.get('value', ''), flag_subject)
        message_field = soup.find('textarea', {'name': 'message'})
        self.assertEqual(message_field.text, "\r\n" + flag_message)


    def test_contact_submit(self):
        '''
            Does the contact form submit as expected?
        '''
        from_email = 'example@example.com'
        custom_subject = 'Just some subject here'
        message_text = 'Just some message here.'
        refering_page = 'http://elsewhere.com'

        our_address = settings.DEFAULT_FROM_EMAIL
        subject_prefix = '[perma-contact] '
        expected_emails_sent = 0

        ###
        ### Success expected
        ###

        ## All fields, including custom subject and referer
        # submit
        self.submit_form('contact',
                          data = { 'email': from_email,
                                   'message': message_text,
                                   'subject': custom_subject,
                                   'referer': refering_page },
                                    success_url=reverse('contact_thanks'))
        expected_emails_sent += 1

        # check contents of sent email
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        message = mail.outbox[expected_emails_sent - 1]
        self.assertIn(message_text, message.body)
        self.assertIn("Referring Page: " + refering_page, message.body)
        self.assertIn("Affiliations: (none)", message.body)
        self.assertEqual(message.subject, subject_prefix + custom_subject)
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': from_email})

        ## All fields except custom subject and referer
        # submit
        self.submit_form('contact',
                          data = { 'email': from_email,
                                   'message': message_text },
                          success_url=reverse('contact_thanks'))
        expected_emails_sent += 1

        # check contents of sent email
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        message = mail.outbox[expected_emails_sent - 1]
        self.assertIn(message_text, message.body)
        self.assertIn("Referring Page: ", message.body)
        self.assertIn("Affiliations: (none)", message.body)
        self.assertEqual(message.subject, subject_prefix + 'New message from Perma contact form')
        self.assertEqual(message.from_email, our_address )
        self.assertEqual(message.recipients(), [our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': from_email})

        ## Repeat while logged in as org user; verify email only differs by listing affiliations
        # submit
        self.submit_form('contact',
                          data = { 'email': from_email,
                                   'message': message_text },
                          success_url=reverse('contact_thanks'),
                          user='test_another_library_org_user@example.com')
        expected_emails_sent += 1

        # check contents of sent email
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        message = mail.outbox[expected_emails_sent -1]
        self.assertIn("Affiliations: Another Library&#39;s Journal (Another Library), A Third Journal (Test Library)", message.body)
        subbed = message.body.replace("Another Library&#39;s Journal (Another Library), A Third Journal (Test Library)", "(none)")
        self.assertEqual(subbed, mail.outbox[expected_emails_sent - 2].body)

        ## Repeat while logged in as registrar user; verify email only differs by listing affiliations
        # submit
        self.submit_form('contact',
                          data = { 'email': from_email,
                                   'message': message_text },
                          success_url=reverse('contact_thanks'),
                          user='test_registrar_user@example.com')
        expected_emails_sent += 1

        # check contents of sent email
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        message = mail.outbox[expected_emails_sent -1]
        self.assertIn("Affiliations: Test Library (Registrar)", message.body)
        subbed = message.body.replace("Test Library (Registrar)", "(none)")
        self.assertEqual(subbed, mail.outbox[expected_emails_sent - 3].body)

        ###
        ### Failure expected
        ###

        # Blank submission should fail and request email address and message.
        # We should get the contact page back.
        response = self.submit_form('contact',
                                     data = { 'email': '',
                                              'message': '' },
                                     error_keys = ['email', 'message'])
        self.assertEqual(response.request['PATH_INFO'], reverse('contact'))

    def test_about_partner_list(self):
        '''
            Is the partner list populated, and split evenly into 2 columns?
        '''
        response = self.get('about').content
        soup = BeautifulSoup(response, 'html.parser')
        partner_columns = soup.find('div', {'class':'partner-list'}).find_all('div', recursive=False)
        self.assertEqual(len(partner_columns), 2)
        first_partners = partner_columns[0].select('.perma-partner')
        self.assertTrue(partner.text for partner in first_partners)
        second_partners = partner_columns[1].select('.perma-partner')
        self.assertTrue(partner.text for partner in second_partners)
        first_partners = partner_columns[0].select('.perma-partner')
        self.assertTrue(len(first_partners) == len(second_partners) or
                        len(first_partners) == len(second_partners) + 1)
