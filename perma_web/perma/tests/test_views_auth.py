from axes.models import AccessAttempt
from axes.utils import reset as reset_login_attempts
import datetime
from time import sleep

from django.conf import settings
from django.core import mail
from django.test.utils import override_settings
from django.urls import reverse

from .utils import PermaTestCase


class AuthViewsTestCase(PermaTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.login_url = reverse('user_management_limited_login')
        cls.email = 'test_user@example.com'
        cls.password = 'pass'
        cls.wrong_password = 'wrongpass'
        cls.new_password = 'Anewpass1'

    def setUp(self):
        reset_login_attempts(username=self.email)

    def make_bad_attempt(self):
        response = self.client.post(self.login_url, {'username': self.email, 'password': self.wrong_password}, secure=True)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertFalse(response.cookies.get(settings.CACHE_BYPASS_COOKIE_NAME).value)
        return response

    def test_login(self):
        """
        Test the login form
        We should get redirected to the create page
        """

        # Login through our form and make sure we get redirected to our create page
        response = self.client.post(self.login_url, {'username': self.email, 'password': self.password}, secure=True)
        create_url = 'login' not in response['Location']
        self.assertEqual(create_url, True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertTrue(response.cookies.get(settings.CACHE_BYPASS_COOKIE_NAME).value)


    def test_deactived_user_login(self):
        response = self.submit_form('user_management_limited_login',
                          data = {'username': 'deactivated_registrar_user@example.com',
                                  'password': 'pass'},
                          success_url=reverse('user_management_account_is_deactivated'))
        self.assertFalse(response.cookies.get(settings.CACHE_BYPASS_COOKIE_NAME).value)


    def test_unactived_user_login(self):
        response = self.submit_form('user_management_limited_login',
                          data = {'username': 'unactivated_faculty_user@example.com',
                                  'password': 'pass'},
                          success_url=reverse('user_management_not_active'))
        self.assertFalse(response.cookies.get(settings.CACHE_BYPASS_COOKIE_NAME).value)

    def test_logout(self):
        """
        Test our logout link
        """

        # Login with our client and logout with our view
        self.log_in_user(user='test_user@example.com', password='pass')
        self.assertIn('_auth_user_id', self.client.session)
        self.get('logout')
        response = self.submit_form('logout')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertFalse(response.cookies.get(settings.CACHE_BYPASS_COOKIE_NAME).value)

    def test_password_change(self):
        """
        Let's make sure we can login and change our password
        """

        self.log_in_user(user='test_user@example.com', password='pass')
        self.assertIn('_auth_user_id', self.client.session)

        self.client.post(reverse('password_change'),
            {'old_password':'pass', 'new_password1':'Changed-password1',
            'new_password2':'Changed-password1'},
            secure=True)

        self.client.logout()

        # Try to login with our old password
        self.log_in_user(user='test_user@example.com', password='pass')
        self.assertNotIn('_auth_user_id', self.client.session)

        self.client.logout()

        # Try to login with our new password
        self.log_in_user(user='test_user@example.com', password='Changed-password1')
        self.assertIn('_auth_user_id', self.client.session)

    @override_settings(AXES_FAILURE_LIMIT=2)
    def test_locked_out_after_limit(self):
        response = self.make_bad_attempt()
        self.assertContains(response, 'class="field-error"', status_code=200)

        response = self.make_bad_attempt()
        self.assertContains(response, 'Too Many Attempts', status_code=403)

        response = self.log_in_user(user=self.email, password=self.new_password)
        self.assertContains(response, 'Too Many Attempts', status_code=403)
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(AXES_FAILURE_LIMIT=1)
    @override_settings(AXES_COOLOFF_TIME=datetime.timedelta(seconds=2))
    def test_lockout_expires_after_cooloff(self):
        response = self.make_bad_attempt()
        self.assertContains(response, 'Too Many Attempts', status_code=403)
        sleep(2)
        response = self.log_in_user(user=self.email, password=self.password)
        self.assertIn('_auth_user_id', self.client.session)

    @override_settings(AXES_FAILURE_LIMIT=2)
    def test_login_attempts_reset(self):
        # lock the user out
        self.make_bad_attempt()
        response = self.make_bad_attempt()
        self.assertContains(response, 'Too Many Attempts', status_code=403)
        self.assertContains(response, 'Reset my password', status_code=403)
        aa = AccessAttempt.objects.get(username=self.email)
        self.assertEqual(aa.failures_since_start, 2)

        # get the reset password email/link
        self.client.post(reverse('password_reset'), {"email": self.email}, secure=True)
        message = mail.outbox[0]
        reset_url = next(line for line in message.body.rstrip().split("\n") if line.startswith('http'))

        # go through with the reset
        response = self.client.get(reset_url, follow=True, secure=True)
        post_url = response.redirect_chain[0][0]
        response = self.client.post(post_url, {'new_password1': self.new_password, 'new_password2': self.new_password}, follow=True, secure=True)
        self.assertContains(response, 'Your password has been set')
        self.assertFalse(AccessAttempt.objects.filter(username=self.email).exists())

        # verify you get the normal form errors, not the lockout page,
        # if you fail again
        response = self.make_bad_attempt()
        self.assertContains(response, 'class="field-error"', status_code=200)

        # verify you CAN login with the new password
        self.log_in_user(user=self.email, password=self.new_password)
