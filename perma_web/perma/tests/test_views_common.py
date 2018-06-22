from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import override_settings, Client

from perma.urls import urlpatterns
from perma.models import Registrar, Link

from .utils import PermaTestCase

from bs4 import BeautifulSoup
from urllib.parse import urlencode

@override_settings(CONTACT_REGISTRARS=True)
class CommonViewsTestCase(PermaTestCase):

    def setUp(self):
        self.users = ['test_user@example.com', 'test_org_user@example.com', 'multi_registrar_org_user@example.com', 'test_registrar_user@example.com', 'test_admin_user@example.com']
        self.from_email = 'example@example.com'
        self.custom_subject = 'Just some subject here'
        self.message_text = 'Just some message here.'
        self.refering_page = 'http://elsewhere.com'
        self.our_address = settings.DEFAULT_FROM_EMAIL
        self.subject_prefix = '[perma-contact] '
        self.flag = "zzzz-zzzz"
        self.flag_message = "http://perma.cc/{} contains material that is inappropriate.".format(self.flag)
        self.flag_subject = "Reporting Inappropriate Content"

    def test_public_views(self):
        # test static template views
        for urlpattern in urlpatterns:
            if urlpattern.callback.__name__ == 'DirectTemplateView':
                self.get(urlpattern.name)

    # Record page

    def assert_can_view_capture(self, guid):
        response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': guid}})
        self.assertIn("<iframe ", response.content)

    def test_regular_archive(self):
        self.assert_can_view_capture('3SLN-JHX9')
        for user in self.users:
            self.log_in_user(user)
            self.assert_can_view_capture('3SLN-JHX9')

    def test_dark_archive(self):
        response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'ABCD-0001'}}, require_status_code=403)
        self.assertIn(b"This record is private and cannot be displayed.", response.content)

        # check that top bar is displayed to logged-in users
        for user in self.users:
            self.log_in_user(user)
            response = self.get('single_permalink', reverse_kwargs={'kwargs': {'guid': 'ABCD-0001'}})
            self.assertIn("This record is private.", response.content)

    def test_redirect_to_download(self):
        # Give user option to download to view pdf if on mobile
        link = Link.objects.get(pk='7CF8-SS4G')
        file_url = link.captures.filter(role='primary').get().playback_url_with_access_token()

        client = Client(HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 6_1_4 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10B350 Safari/8536.25')
        response = client.get(reverse('single_permalink', kwargs={'guid': link.guid}))
        self.assertIn("Perma.cc can\'t display this file type on mobile", response.content)
        # Make sure that we're including the archived capture url
        self.assertIn(file_url, response.content)

        # If not on mobile, display link as normal
        client = Client(HTTP_USER_AGENT='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/601.7.7 (KHTML, like Gecko) Version/9.1.2 Safari/601.7.7')
        response = client.get(reverse('single_permalink', kwargs={'guid': link.guid}))
        self.assertNotIn("Perma.cc can\'t display this file type on mobile", response.content)

    def test_deleted(self):
        response = self.get('single_permalink', reverse_kwargs={'kwargs': {'guid': 'ABCD-0003'}}, require_status_code=410)
        self.assertIn("This record has been deleted.", response.content)

    def test_misformatted_nonexistent_links_404(self):
        response = self.client.get(reverse('single_permalink', kwargs={'guid': 'JJ99--JJJJ'}))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('single_permalink', kwargs={'guid': '988-JJJJ=JJJJ'}))
        self.assertEqual(response.status_code, 404)

    def test_properly_formatted_nonexistent_links_404(self):
        response = self.client.get(reverse('single_permalink', kwargs={'guid': 'JJ99-JJJJ'}))
        self.assertEqual(response.status_code, 404)

        # Test the original ID style. We shouldn't get a redirect.
        response = self.client.get(reverse('single_permalink', kwargs={'guid': '0J6pkzDeQwT'}))
        self.assertEqual(response.status_code, 404)

    def test_replacement_link(self):
        response = self.client.get(reverse('single_permalink', kwargs={'guid': 'ABCD-0006'}))
        self.assertRedirects(response, reverse('single_permalink', kwargs={'guid': '3SLN-JHX9'}))


    ###
    ###   Does the contact form render as expected?
    ###

    def test_contact_blank_when_logged_out(self):
        '''
            Check correct fields are blank for logged out user
        '''
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
            self.assertEqual(textarea.text.strip(), "")

    def test_contact_blank_regular(self):
        '''
            Check correct fields are blank for regular user
        '''
        response = self.get('contact', user="test_user@example.com").content
        soup = BeautifulSoup(response, 'html.parser')
        inputs = soup.select('input')
        # Two csrf inputs: one by logout button, one in this form
        self.assertEqual(len(inputs), 4 + 1)
        for input in inputs:
            self.assertIn(input['name'],['csrfmiddlewaretoken', 'referer', 'email', 'subject'])
            if input['name'] in ['csrfmiddlewaretoken', 'email']:
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))
        textareas = soup.select('textarea')
        self.assertEqual(len(textareas), 1)
        for textarea in textareas:
            self.assertIn(textarea['name'],['message'])
            self.assertEqual(textarea.text.strip(), "")

    def test_contact_blank_registrar(self):
        '''
            Check correct fields are blank for registrar user
        '''
        response = self.get('contact', user="test_registrar_user@example.com").content
        soup = BeautifulSoup(response, 'html.parser')
        inputs = soup.select('input')
        # Two csrf inputs: one by logout button, one in this form
        self.assertEqual(len(inputs), 4 + 1)
        for input in inputs:
            self.assertIn(input['name'],['csrfmiddlewaretoken', 'referer', 'email', 'subject'])
            if input['name'] in ['csrfmiddlewaretoken', 'email']:
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))
        textareas = soup.select('textarea')
        self.assertEqual(len(textareas), 1)
        for textarea in textareas:
            self.assertIn(textarea['name'],['message'])
            self.assertEqual(textarea.text.strip(), "")

    def test_contact_blank_single_reg_org_user(self):
        '''
            Check correct fields are blank for a single-registrar org user
        '''
        response = self.get('contact', user="test_org_user@example.com").content
        soup = BeautifulSoup(response, 'html.parser')
        inputs = soup.select('input')
        # Two csrf inputs: one by logout button, one in this form
        self.assertEqual(len(inputs), 5 + 1)
        for input in inputs:
            self.assertIn(input['name'],['csrfmiddlewaretoken', 'referer', 'email', 'subject', 'registrar'])
            if input['name'] in ['csrfmiddlewaretoken', 'email', 'registrar']:
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))
        textareas = soup.select('textarea')
        self.assertEqual(len(textareas), 1)
        for textarea in textareas:
            self.assertIn(textarea['name'],['message'])
            self.assertEqual(textarea.text.strip(), "")

    def test_contact_blank_multi_reg_org_user(self):
        '''
            Check correct fields are blank for a multi-registrar org user
        '''
        response = self.get('contact', user="multi_registrar_org_user@example.com").content
        soup = BeautifulSoup(response, 'html.parser')
        inputs = soup.select('input')
        # Two csrf inputs: one by logout button, one in this form
        self.assertEqual(len(inputs), 4 + 1)
        for input in inputs:
            self.assertIn(input['name'],['csrfmiddlewaretoken', 'referer', 'email', 'subject'])
            if input['name'] in ['csrfmiddlewaretoken', 'email']:
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))
        textareas = soup.select('textarea')
        self.assertEqual(len(textareas), 1)
        for textarea in textareas:
            self.assertIn(textarea['name'],['message'])
            self.assertEqual(textarea.text.strip(), "")
        selects = soup.select('select')
        self.assertEqual(len(selects), 1)
        for select in selects:
            self.assertIn(select['name'],['registrar'])
            self.assertGreaterEqual(len(select.find_all("option")), 2)

    def check_contact_params(self, soup):
        subject_field = soup.find('input', {'name': 'subject'})
        self.assertEqual(subject_field.get('value', ''), self.custom_subject)
        message_field = soup.find('textarea', {'name': 'message'})
        self.assertEqual(message_field.text.strip(), self.message_text)

    def test_contact_params_regular(self):
        '''
            Check subject line, message, read in from GET params
        '''
        for user in self.users + [None]:
            response = self.get('contact', query_params={ 'message': self.message_text,
                                                          'subject': self.custom_subject, },
                                           user=user).content
            self.check_contact_params(BeautifulSoup(response, 'html.parser'))

    def check_contact_flags(self, soup):
        subject_field = soup.find('input', {'name': 'subject'})
        self.assertEqual(subject_field.get('value', ''), self.flag_subject)
        message_field = soup.find('textarea', {'name': 'message'})
        self.assertEqual(message_field.text.strip(), self.flag_message)

    def test_contact_flags(self):
        '''
            Check flag read in from GET params, and that its subject/message override other GET params
        '''
        for user in self.users + [None]:
            response = self.get('contact', query_params={ 'flag': self.flag,
                                                          'message': self.message_text,
                                                          'subject': self.custom_subject },
                                           user=user).content
            self.check_contact_flags(BeautifulSoup(response, 'html.parser'))


    ###
    ###   Does the contact form submit as expected?
    ###

    def test_contact_standard_submit_fail(self):
        '''
            Blank submission should fail and, for most users, request
            email address and message.
            We should get the contact page back.
        '''
        response = self.submit_form('contact',
                                     data = { 'email': '',
                                              'message': '' },
                                     error_keys = ['email', 'message'])
        self.assertEqual(response.request['PATH_INFO'], reverse('contact'))

    def test_contact_org_user_submit_fail(self):
        '''
            Org users are special. Blank submission should fail
            and request email address, message, and registrar.
            We should get the contact page back.
        '''
        response = self.submit_form('contact',
                                     data = { 'email': '',
                                              'message': '' },
                                     user='test_org_user@example.com',
                                     error_keys = ['email', 'message', 'registrar'])
        self.assertEqual(response.request['PATH_INFO'], reverse('contact'))

    def test_contact_standard_submit_required(self):
        '''
            All fields, including custom subject and referer
        '''
        self.submit_form('contact',
                          data = { 'email': self.from_email,
                                   'message': self.message_text,
                                   'subject': self.custom_subject,
                                   'referer': self.refering_page },
                          success_url=reverse('contact_thanks'))

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(self.message_text, message.body)
        self.assertIn("Referring Page: " + self.refering_page, message.body)
        self.assertIn("Affiliations: (none)", message.body)
        self.assertEqual(message.subject, self.subject_prefix + self.custom_subject)
        self.assertEqual(message.from_email, self.our_address)
        self.assertEqual(message.recipients(), [self.our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': self.from_email})

    def test_contact_standard_submit_no_optional(self):
        '''
            All fields except custom subject and referer
        '''
        self.submit_form('contact',
                          data = { 'email': self.from_email,
                                   'message': self.message_text },
                          success_url=reverse('contact_thanks'))
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(self.message_text, message.body)
        self.assertIn("Referring Page: ", message.body)
        self.assertIn("Affiliations: (none)", message.body)
        self.assertEqual(message.subject, self.subject_prefix + 'New message from Perma contact form')
        self.assertEqual(message.from_email, self.our_address )
        self.assertEqual(message.recipients(), [self.our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': self.from_email})

    def test_contact_org_user_submit_invalid(self):
        '''
            Org users get extra fields. Registrar must be a valid choice.
            We should get the contact page back.
        '''
        response = self.submit_form('contact',
                                     data = { 'email': self.from_email,
                                              'message': self.message_text,
                                              'registrar': 'not_a_licit_registrar_id'},
                                     user='test_org_user@example.com',
                                     error_keys = ['registrar'])
        self.assertEqual(response.request['PATH_INFO'], reverse('contact'))

    def test_contact_org_user_submit(self):
        '''
            Should be sent to registrar users.
        '''
        registrar = Registrar.objects.get(email='library@university.edu')
        registrar_users = registrar.active_registrar_users()
        success = reverse('contact_thanks') + "?{}".format(urlencode({'registrar': registrar.id}))
        expected_emails = 0
        for user in ['test_org_user@example.com', 'multi_registrar_org_user@example.com']:
            self.submit_form('contact',
                              data = { 'email': self.from_email,
                                       'message': self.message_text,
                                       'registrar': registrar.id },
                              user=user,
                              success_url=success)

            expected_emails +=1
            self.assertEqual(len(mail.outbox), expected_emails)
            message = mail.outbox[expected_emails -1]
            self.assertIn(self.message_text, message.body)
            self.assertEqual(message.from_email, self.our_address )
            self.assertEqual(message.to, [user.email for user in registrar_users])
            self.assertEqual(message.cc, [self.our_address, self.from_email] )
            self.assertEqual(message.reply_to, [self.from_email])

    def test_contact_org_user_affiliation_string(self):
        '''
            Verify org affiliations are printed correctly
        '''
        self.submit_form('contact',
                          data = { 'email': self.from_email,
                                   'message': self.message_text,
                                   'registrar': 2 },
                          user='test_another_library_org_user@example.com')
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn("Affiliations: Another Library's Journal (Another Library), A Third Journal (Test Library)", message.body)

    def test_contact_reg_user_affiliation_string(self):
        '''
            Verify registrar affiliations are printed correctly
        '''
        self.submit_form('contact',
                          data = { 'email': self.from_email,
                                   'message': self.message_text },
                          user='test_registrar_user@example.com')
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn("Affiliations: Test Library (Registrar)", message.body)

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
