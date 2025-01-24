from bs4 import BeautifulSoup
from random import random, getrandbits

from django.core import mail
from django.conf import settings
from django.db import IntegrityError
from django.test import override_settings
from django.urls import reverse

from perma.models import LinkUser, Registrar
from perma.tests.utils import PermaTestCase

class UserManagementViewsTestCase(PermaTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.registrar_user = LinkUser.objects.get(pk=2)
        cls.registrar = cls.registrar_user.registrar

    ### Libraries ###

    def new_lib(self):
        rand = random()
        return { 'email': 'library{}@university.org'.format(rand),
                 'name': 'University Library {}'.format(rand),
                 'website': 'http://website{}.org'.format(rand),
                 'address': '{} Main St., Boston MA 02144'.format(rand)}

    def new_lib_user(self):
        rand = random()
        email = self.randomize_capitalization('user{}@university.org'.format(rand))
        return { 'raw_email': email,
                 'normalized_email': email.lower(),
                 'first': 'Joe',
                 'last': 'Yacobówski' }

    def check_library_labels(self, soup):
        name_label = soup.find('label', {'for': 'id_b-name'})
        self.assertEqual(name_label.text, "Library name")
        email_label = soup.find('label', {'for': 'id_b-email'})
        self.assertEqual(email_label.text, "Library email")
        website_label = soup.find('label', {'for': 'id_b-website'})
        self.assertEqual(website_label.text, "Library website")

    def check_lib_user_labels(self, soup):
        email_label = soup.find('label', {'for': 'id_a-e-address'})
        self.assertEqual(email_label.text, "Your email")

    def check_lib_email(self, message, new_lib, user):
        our_address = settings.DEFAULT_FROM_EMAIL

        self.assertIn(new_lib['name'], message.body)
        self.assertIn(new_lib['email'], message.body)

        self.assertIn(user['raw_email'], message.body)

        id = Registrar.objects.get(email=new_lib['email']).id
        approve_url = "http://testserver{}".format(reverse('user_sign_up_approve_pending_registrar', args=[id]))
        self.assertIn(approve_url, message.body)
        self.assertEqual(message.subject, "Perma.cc new library registrar account request")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': user['raw_email']})

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_library_render(self):
        '''
           Does the library signup form display as expected?
        '''

        # NOT LOGGED IN

        # Registrar and user forms are displayed,
        # inputs are blank, and labels are customized as expected
        response = self.get('sign_up_libraries').content
        soup = BeautifulSoup(response, 'html.parser')
        self.check_library_labels(soup)
        self.check_lib_user_labels(soup)
        inputs = soup.select('input')
        self.assertEqual(len(inputs), 9)
        for input in inputs:
            if input['name'] in ['csrfmiddlewaretoken', 'telephone']:
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))

        # If request_data is present in session, registrar form is prepopulated,
        # and labels are still customized as expected
        session = self.client.session
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        session['request_data'] = { 'b-email': new_lib['email'],
                                    'b-website': new_lib['website'],
                                    'b-name': new_lib['name'],
                                    'b-address': new_lib['address'],
                                    'a-e-address': new_lib_user['raw_email'],
                                    'a-first_name': new_lib_user['first'],
                                    'a-last_name': new_lib_user['last'],
                                    'csrfmiddlewaretoken': '11YY3S2DgOw2DHoWVEbBArnBMdEA2svu' }
        session.save()
        response = self.get('sign_up_libraries').content
        soup = BeautifulSoup(response, 'html.parser')
        self.check_library_labels(soup)
        self.check_lib_user_labels(soup)
        inputs = soup.select('input')
        self.assertEqual(len(inputs), 9)
        for input in inputs:
            if input['name'] in ['csrfmiddlewaretoken', 'telephone']:
                self.assertTrue(input.get('value', ''))
            elif input['name'][:2] == "b-":
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))

        # If there's an unsuccessful submission, field labels are still as expected.
        response = self.post('sign_up_libraries').content
        soup = BeautifulSoup(response, 'html.parser')
        self.check_library_labels(soup)
        self.check_lib_user_labels(soup)

        # LOGGED IN

        # Registrar form is displayed, but user form is not,
        # inputs are blank, and labels are still customized as expected
        response = self.get('sign_up_libraries', user="test_user@example.com").content
        soup = BeautifulSoup(response, 'html.parser')
        self.check_library_labels(soup)
        inputs = soup.select('input')
        self.assertEqual(len(inputs), 6) # 6 because csrf is here and in the logout form
        for input in inputs:
            self.assertIn(input['name'],['csrfmiddlewaretoken', 'b-name', 'b-email', 'b-website', 'b-address'])
            if input['name'] == 'csrfmiddlewaretoken':
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_library_submit_success(self):
        '''
           Does the library signup form submit as expected? Success cases.
        '''
        expected_emails_sent = 0

        # Not logged in, submit all fields sans first and last name
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        self.submit_form('sign_up_libraries',
                          data = { 'b-email': new_lib['email'],
                                   'b-website': new_lib['website'],
                                   'b-name': new_lib['name'],
                                   'a-e-address': new_lib_user['raw_email'] },
                          success_url=reverse('register_library_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_lib_email(mail.outbox[expected_emails_sent - 2], new_lib, new_lib_user)
        self.check_new_activation_email(mail.outbox[expected_emails_sent - 1], new_lib_user['raw_email'])

        # Not logged in, submit all fields including first and last name
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        self.submit_form('sign_up_libraries',
                          data = { 'b-email': new_lib['email'],
                                   'b-website': new_lib['website'],
                                   'b-name': new_lib['name'],
                                   'a-e-address': new_lib_user['raw_email'],
                                   'a-first_name': new_lib_user['first'],
                                   'a-last_name': new_lib_user['last']},
                          success_url=reverse('register_library_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_lib_email(mail.outbox[expected_emails_sent - 2], new_lib, new_lib_user)
        self.check_new_activation_email(mail.outbox[expected_emails_sent - 1], new_lib_user['raw_email'])

        # Logged in
        new_lib = self.new_lib()
        existing_lib_user = {
            'raw_email': 'test_user@example.com',
            'normalized_email': 'test_user@example.com',
        }
        self.submit_form('sign_up_libraries',
                          data = { 'b-email': new_lib['email'],
                                   'b-website': new_lib['website'],
                                   'b-name': new_lib['name'] },
                          success_url=reverse('settings_affiliations'),
                          user=existing_lib_user['raw_email'])
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_lib_email(mail.outbox[expected_emails_sent - 1], new_lib, existing_lib_user)

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_library_form_honeypot(self):
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        self.submit_form('sign_up_libraries',
                          data = { 'b-email': new_lib['email'],
                                   'b-website': new_lib['website'],
                                   'b-name': new_lib['name'],
                                   'a-e-address': new_lib_user['raw_email'],
                                   'a-first_name': new_lib_user['first'],
                                   'a-last_name': new_lib_user['last'],
                                   'a-telephone': "I'm a bot."},
                          success_url=reverse('register_library_instructions'))
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(Registrar.objects.filter(name=new_lib['name']).exists())

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_library_submit_failure(self):
        '''
           Does the library signup form submit as expected? Failures.
        '''
        new_lib = self.new_lib()
        existing_lib_user = { 'email': 'test_user@example.com'}

        # Not logged in, blank submission reports correct fields required
        # ('email' catches both registrar and user email errors, unavoidably,
        # so test with just that missing separately)
        self.submit_form('sign_up_libraries',
                          data = {},
                          form_keys = ['registrar_form', 'user_form'],
                          error_keys = ['website', 'name', 'email'])
        self.assertEqual(len(mail.outbox), 0)

        # (checking user email missing separately)
        self.submit_form('sign_up_libraries',
                          data = {'b-email': new_lib['email'],
                                  'b-website': new_lib['website'],
                                  'b-name': new_lib['name']},
                          form_keys = ['registrar_form', 'user_form'],
                          error_keys = ['email'])
        self.assertEqual(len(mail.outbox), 0)

        # Not logged in, user appears to have already registered
        data = {'b-email': new_lib['email'],
                'b-website': new_lib['website'],
                'b-name': new_lib['name'],
                'a-e-address': self.randomize_capitalization(existing_lib_user['email'])}
        self.submit_form('sign_up_libraries',
                          data = data,
                          form_keys = ['registrar_form', 'user_form'],
                          success_url = '/login?next=/libraries/')
        self.assertDictEqual(self.client.session['request_data'], data)
        self.assertEqual(len(mail.outbox), 0)

        # Not logged in, registrar appears to exist already
        # (actually, this doesn't currently fail)

        # Logged in, blank submission reports all fields required
        self.submit_form('sign_up_libraries',
                          data = {},
                          user = existing_lib_user['email'],
                          error_keys = ['website', 'name', 'email'])
        self.assertEqual(len(mail.outbox), 0)

        # Logged in, registrar appears to exist already
        # (actually, this doesn't currently fail)

    ### Courts ###

    def new_court(self):
        rand = random()
        return { 'requested_account_note': 'Court {}'.format(rand) }

    def new_court_user(self):
        rand = random()
        email = self.randomize_capitalization('user{}@university.org'.format(rand))
        return { 'raw_email': email,
                 'normalized_email': email.lower(),
                 'first': 'Joe',
                 'last': 'Yacobówski' }

    def check_court_email(self, message, court_email):
        our_address = settings.DEFAULT_FROM_EMAIL

        # Doesn't check email contents yet; too many variations possible presently
        self.assertEqual(message.subject, "Perma.cc new library court account information request")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': court_email})

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_court_success(self):
        '''
            Does the court signup form submit as expected? Success cases.
        '''
        new_court = self.new_court()
        new_user = self.new_court_user()
        existing_user = { 'email': 'test_user@example.com'}
        another_existing_user = { 'email': 'another_library_user@example.com'}
        expected_emails_sent = 0

        # NOT LOGGED IN

        # Existing user's email address, no court info
        # (currently succeeds, should probably fail; see issue 1746)
        self.submit_form('sign_up_courts',
                          data = { 'e-address': self.randomize_capitalization(existing_user['email'])},
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

        # Existing user's email address + court info
        self.submit_form('sign_up_courts',
                          data = { 'e-address': self.randomize_capitalization(existing_user['email']),
                                   'requested_account_note': new_court['requested_account_note']},
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

        # New user email address, don't create account
        self.submit_form('sign_up_courts',
                          data = { 'e-address': new_user['raw_email'],
                                   'requested_account_note': new_court['requested_account_note']},
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], new_user['raw_email'])

        # New user email address, create account
        self.submit_form('sign_up_courts',
                          data = { 'e-address': new_user['raw_email'],
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True },
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_new_activation_email(mail.outbox[expected_emails_sent - 2], new_user['raw_email'])
        self.check_court_email(mail.outbox[expected_emails_sent - 1], new_user['raw_email'])

        # LOGGED IN

        # New user email address
        # (This succeeds and creates a new account; see issue 1749)
        new_user = self.new_court_user()
        self.submit_form('sign_up_courts',
                          data = { 'e-address': new_user['raw_email'],
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True },
                          user = existing_user['email'],
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_new_activation_email(mail.outbox[expected_emails_sent - 2], new_user['raw_email'])
        self.check_court_email(mail.outbox[expected_emails_sent - 1], new_user['raw_email'])

        # Existing user's email address, not that of the user logged in.
        # (This is odd; see issue 1749)
        self.submit_form('sign_up_courts',
                          data = { 'e-address': self.randomize_capitalization(existing_user['email']),
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True },
                          user = another_existing_user['email'],
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_court_form_honeypot(self):
        new_court = self.new_court()
        new_user = self.new_court_user()
        self.submit_form('sign_up_courts',
                          data = { 'e-address': new_user['raw_email'],
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True,
                                   'telephone': "I'm a bot." },
                          success_url = reverse('register_email_instructions'))
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(LinkUser.objects.filter(email__iexact=new_user['raw_email']).exists())

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_court_failure(self):
        '''
            Does the court signup form submit as expected? Failure cases.
        '''
        # Not logged in, blank submission reports correct fields required
        self.submit_form('sign_up_courts',
                          data = {},
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)

        # Logged in, blank submission reports same fields required
        # (This is odd; see issue 1749)
        self.submit_form('sign_up_courts',
                          data = {},
                          user = 'test_user@example.com',
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)


    ### Firms ###

    def create_firm_registrar_form(self):
        return {
            'name': f'Firm {random()}',
            'email': 'test-firm@example.com',
            'website': 'https://www.example.com',
        }

    def create_firm_usage_form(self):
        return {
            'estimated_number_of_accounts': '10 - 50',
            'estimated_perma_links_per_month': '100+',
        }

    def create_firm_user_form(self):
        email = self.randomize_capitalization(f'user{random()}@university.org')
        return {
            'raw_email': email,
            'normalized_email': email.lower(),
            'first': 'Joe',
            'last': 'Yacobówski',
            'registrar_user_candidate': bool(getrandbits(1)),
        }

    def check_firm_email(self, message: str, firm_email: str):
        perma_admin_email = settings.DEFAULT_FROM_EMAIL

        self.assertEqual(message.subject, 'Perma.cc new paid registrar account request')
        self.assertEqual(message.from_email, perma_admin_email)
        self.assertEqual(message.to, [firm_email.lower()])
        self.assertEqual(message.cc, [perma_admin_email])
        self.assertEqual(message.reply_to, [perma_admin_email])

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_firm_success(self):
        firm_registrar_form = self.create_firm_registrar_form()
        firm_usage_form = self.create_firm_usage_form()
        firm_user_form = self.create_firm_user_form()
        existing_user = {'email': 'test_user@example.com'}
        expected_emails_sent = 0

        # NOT LOGGED IN

        # Existing user's email address, no firm info (should not succeed due to missing values)
        self.submit_form(
            'sign_up_firms',
            data={'a-e-address': self.randomize_capitalization(existing_user['email'])},
        )
        expected_emails_sent += 0
        self.assertEqual(len(mail.outbox), expected_emails_sent)

        # Existing user's email address + firm info
        self.submit_form(
            'sign_up_firms',
            data={
                'a-e-address': self.randomize_capitalization(existing_user['email']),
                'a-registrar_user_candidate': firm_user_form['registrar_user_candidate'],
                **firm_registrar_form,
                **firm_usage_form,
            },
            success_url=reverse('firm_request_response'),
        )
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

        # New user email address, don't create account
        self.submit_form(
            'sign_up_firms',
            data={
                'a-e-address': firm_user_form['raw_email'],
                'a-registrar_user_candidate': firm_user_form['registrar_user_candidate'],
                **firm_registrar_form,
                **firm_usage_form,
            },
            success_url=reverse('firm_request_response'),
        )
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], firm_user_form['raw_email'])

        # New user email address, create account
        self.submit_form(
            'sign_up_firms',
            data={
                'a-e-address': firm_user_form['raw_email'],
                'a-registrar_user_candidate': firm_user_form['registrar_user_candidate'],
                **firm_registrar_form,
                **firm_usage_form,
                'create_account': True,
            },
            success_url=reverse('register_email_instructions'),
        )
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_firm_email(mail.outbox[expected_emails_sent - 2], firm_user_form['raw_email'])
        self.check_new_activation_email(
            mail.outbox[expected_emails_sent - 1], firm_user_form['raw_email']
        )

        # LOGGED IN

        # Existing user
        self.submit_form(
            'sign_up_firms',
            data={
                'a-e-address': existing_user['email'],
                'a-registrar_user_candidate': firm_user_form['registrar_user_candidate'],
                **firm_registrar_form,
                **firm_usage_form,
            },
            user=existing_user['email'],
            success_url=reverse('firm_request_response'),
        )
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_firm_form_honeypot(self):
        firm_registrar_form = self.create_firm_registrar_form()
        firm_usage_form = self.create_firm_usage_form()
        firm_user_form = self.create_firm_user_form()
        self.submit_form(
            'sign_up_firms',
            data={
                'a-e-address': firm_user_form['raw_email'],
                'create_account': True,
                'a-telephone': "I'm a bot.",
                **firm_registrar_form,
                **firm_usage_form,
                'a-registrar_user_candidate': True,
            },
            success_url=reverse('register_email_instructions'),
        )
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(
            LinkUser.objects.filter(email__iexact=firm_user_form['raw_email']).exists()
        )

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_firm_failure(self):
        '''
            Does the firm signup form submit as expected? Failure cases.
        '''
        error_keys = [
            'email',
            'website',
            'estimated_number_of_accounts',
            'estimated_perma_links_per_month',
            'name',
            'registrar_user_candidate',
        ]

        # Not logged in, blank submission reports correct fields required
        self.submit_form(
            'sign_up_firms',
            data={},
            form_keys=['registrar_form', 'usage_form', 'user_form'],
            error_keys=error_keys,
        )
        self.assertEqual(len(mail.outbox), 0)

        # Logged in, blank submission reports same fields required
        # (This is odd; see issue 1749)
        self.submit_form(
            'sign_up_firms',
            data={},
            form_keys=['registrar_form', 'usage_form', 'user_form'],
            user='test_user@example.com',
            error_keys=error_keys,
        )
        self.assertEqual(len(mail.outbox), 0)

    ### Individual Users ###

    def check_new_activation_email(self, message, user_email):
        self.assertEqual(message.subject, "A Perma.cc account has been created for you")
        self.assertEqual(message.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(message.recipients(), [user_email])

        activation_url = next(
            line for line in message.body.rstrip().split('\n') if line.strip().startswith('http')
        )
        return activation_url

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_account_creation_views(self):
        # user registration
        new_user_raw_email = self.randomize_capitalization("new_email@test.com")
        new_user_normalized_email = new_user_raw_email.lower()
        self.submit_form('sign_up', {'e-address': new_user_raw_email, 'first_name': 'Test', 'last_name': 'Test'},
                         success_url=reverse('register_email_instructions'),
                         success_query=LinkUser.objects.filter(
                             email=new_user_normalized_email,
                             raw_email=new_user_raw_email
                         ))

        # email sent
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        activation_url = self.check_new_activation_email(message, new_user_raw_email)

        # the new user is created, but is unactivated
        user = LinkUser.objects.get(email=new_user_normalized_email)
        self.assertEqual(user.raw_email, new_user_raw_email)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_confirmed)

        # if you tamper with the code, it is rejected
        response = self.client.get(activation_url[:-1]+'wrong/', secure=True)
        self.assertContains(response, 'This activation/reset link is invalid')

        # reg confirm - non-matching passwords
        response = self.client.get(activation_url, follow=True, secure=True)
        post_url = response.redirect_chain[0][0]
        self.assertTemplateUsed(response, 'registration/password_reset_confirm.html')
        response = self.client.post(post_url, {'new_password1': 'Anewpass1', 'new_password2': 'Anewpass2'}, follow=True, secure=True)
        self.assertNotContains(response, 'Your password has been set')
        self.assertContains(response, "The two password fields didn’t match")
        # reg confirm - correct
        response = self.client.post(post_url, {'new_password1': 'Anewpass1', 'new_password2': 'Anewpass1'}, follow=True, secure=True)
        self.assertContains(response, 'Your password has been set')

        # Doesn't work twice.
        response = self.client.post(post_url, {'new_password1': 'Anotherpass1', 'new_password2': 'Anotherpass1'}, follow=True, secure=True)
        self.assertContains(response, 'This activation/reset link is invalid')

        # the new user is now activated and can log in
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_confirmed)
        response = self.client.post(reverse('user_management_limited_login'), {'username': new_user_raw_email, 'password': 'Anewpass1'}, follow=True, secure=True)
        self.assertEqual(response.redirect_chain[0][0], '/manage/create/')

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_suggested_registrars(self):
        # Register user
        _, registrar_domain = self.registrar.email.split('@')
        new_user_email = f'new_user@{registrar_domain}'
        self.submit_form(
            'sign_up',
            {'e-address': new_user_email, 'first_name': 'Test', 'last_name': 'Test'},
            success_url=reverse('register_email_instructions'),
            success_query=LinkUser.objects.filter(email=new_user_email),
        )
        self.assertEqual(len(mail.outbox), 1)

        # Obtain suggested registrar(s) from activation email message
        message = mail.outbox[0]
        lines = message.body.splitlines()
        captures = []
        for line in lines:
            if line.lstrip().startswith('- '):
                captures.append(line.strip('- '))

        # Validate suggested registrar(s)
        self.assertEqual(len(captures), 1)
        self.assertEqual(captures[0], f'{self.registrar.name}: {self.registrar.email}')

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_signup_with_existing_email_rejected(self):
        self.assertEqual(LinkUser.objects.filter(email__iexact=self.registrar_user.email).count(), 1)
        self.submit_form('sign_up',
                         {'e-address': self.registrar_user.email, 'first_name': 'Test', 'last_name': 'Test'},
                         error_keys=['email'])
        self.submit_form('sign_up',
                 {'e-address': self.randomize_capitalization(self.registrar_user.email), 'first_name': 'Test', 'last_name': 'Test'},
                 error_keys=['email'])
        self.assertEqual(LinkUser.objects.filter(email__iexact=self.registrar_user.email).count(), 1)

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_user_form_honeypot(self):
        new_user_email = "new_email@test.com"
        self.submit_form('sign_up',
                          data = { 'e-address': new_user_email,
                                   'telephone': "I'm a bot." },
                          success_url = reverse('register_email_instructions'))
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(LinkUser.objects.filter(email__iexact=new_user_email).exists())

    def test_manual_user_creation_rejects_duplicative_emails(self):
        email = 'test_user@example.com'
        self.assertTrue(LinkUser.objects.filter(email=email).exists())
        new_user = LinkUser(email=self.randomize_capitalization(email))
        self.assertRaises(IntegrityError, new_user.save)

    def test_get_new_activation_code(self):
        self.submit_form('user_management_not_active',
                          user = 'unactivated_faculty_user@example.com',
                          data = {},
                          success_url=reverse('user_management_limited_login'))
        self.assertEqual(len(mail.outbox), 1)
        self.check_new_activation_email(mail.outbox[0], 'unactivated_faculty_user@example.com')


    ### PASSWORD RESETS ###

    def test_password_reset_is_case_insensitive(self):
        email = 'test_user@example.com'
        not_a_user = 'doesnotexist@example.com'
        self.assertEqual(LinkUser.objects.filter(email__iexact=email).count(), 1)
        self.assertFalse(LinkUser.objects.filter(email=not_a_user).exists())

        self.submit_form('password_reset', data={})
        self.submit_form('password_reset', data={'email': not_a_user})
        self.assertEqual(len(mail.outbox), 0)

        self.submit_form('password_reset', data={'email': email})
        self.assertEqual(len(mail.outbox), 1)

        self.submit_form('password_reset', data={'email': self.randomize_capitalization(email)})
        self.assertEqual(len(mail.outbox), 2)


