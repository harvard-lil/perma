from axes.utils import reset as reset_login_attempts
import datetime
from time import sleep

from django.test.utils import override_settings
from django.urls import reverse

from perma.models import LinkUser
from .utils import PermaTestCase

def setUp():
    reset_login_attempts(username='test_user@example.com')


def attempt_login(perma_client, username, password, expect_success=True):
    assert '_auth_user_id' not in perma_client.session

    response = perma_client.post(reverse('user_management_limited_login'),
                                 {'username': username,
                                  'password': password})
    if expect_success:
        breakpoint()
        assert response.status_code == 302
        assert 'login' not in response['Location']
        assert '_auth_user_id' in perma_client.session
    else:
        assert '_auth_user_id' not in perma_client.session
    return response

def test_login(perma_client, link_user, randomize_capitalization):
    """
    Test the login form
    We should get redirected to the create page
    """
    # Login through our form and make sure we get redirected to our create page,
    # no matter how the email address is capitalized
    assert LinkUser.objects.filter(email__iexact=link_user.email).count() == 1

    attempt_login(perma_client, link_user.email, link_user.password)

    perma_client.logout()
    attempt_login(link_user.email.upper(), link_user.password)
    perma_client.logout()
    attempt_login(link_user.email.title(), link_user.password)
    perma_client.logout()
    attempt_login(randomize_capitalization(link_user.email), link_user.password)


class AuthViewsTestCase(PermaTestCase):

    # @classmethod
    # def setUpTestData(cls):
    #     cls.login_url = reverse('user_management_limited_login')
    #     cls.email = 'test_user@example.com'
    #     cls.password = 'pass'
    #     cls.wrong_password = 'wrongpass'
    #     cls.new_password = 'Anewpass1'

    # def setUp(self):
    #     reset_login_attempts(username=self.email)

    # def attempt_login(self, username, password, expect_success=True):
    #     self.assertNotIn('_auth_user_id', self.client.session)
    #     breakpoint()
    #     response = self.client.post(self.login_url, {'username': username, 'password': password}, secure=True)

    #     if expect_success:
    #         self.assertEqual(response.status_code, 302)
    #         self.assertFalse('login' in response['Location'])
    #         self.assertIn('_auth_user_id', self.client.session)
    #     else:
    #         self.assertNotIn('_auth_user_id', self.client.session)

    #     return response

    # def test_login(self):
    #     """
    #     Test the login form
    #     We should get redirected to the create page
    #     """
    #     # Login through our form and make sure we get redirected to our create page,
    #     # no matter how the email address is capitalized
    #     self.assertEqual(LinkUser.objects.filter(email__iexact=self.email).count(), 1)

    #     self.attempt_login(self.email, self.password)
    #     self.client.logout()
    #     self.attempt_login(self.email.upper(), self.password)
    #     self.client.logout()
    #     self.attempt_login(self.email.title(), self.password)
    #     self.client.logout()
    #     self.attempt_login(self.randomize_capitalization(self.email), self.password)

    def test_deactived_user_login(self):
        self.submit_form('user_management_limited_login',
                          data = {'username': 'deactivated_registrar_user@example.com',
                                  'password': 'pass'},
                          success_url=reverse('user_management_account_is_deactivated'))
        self.assertNotIn('_auth_user_id', self.client.session)


    def test_unactived_user_login(self):
        self.submit_form('user_management_limited_login',
                          data = {'username': 'unactivated_faculty_user@example.com',
                                  'password': 'pass'},
                          success_url=reverse('user_management_not_active'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout(self):
        """
        Test our logout link
        """

        # Login with our client and logout with our view
        self.log_in_user(user='test_user@example.com', password='pass')
        self.assertIn('_auth_user_id', self.client.session)
        self.get('logout')
        self.submit_form('logout')
        self.assertNotIn('_auth_user_id', self.client.session)

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
        response = self.attempt_login(self.email, self.wrong_password, expect_success=False)
        self.assertContains(response, 'class="field-error"', status_code=200)

        response = self.attempt_login(self.email, self.wrong_password, expect_success=False)
        self.assertContains(response, 'Too Many Attempts', status_code=403)

        response = self.log_in_user(user=self.email, password=self.new_password)
        self.assertContains(response, 'Too Many Attempts', status_code=403)
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(AXES_FAILURE_LIMIT=1)
    @override_settings(AXES_COOLOFF_TIME=datetime.timedelta(seconds=2))
    def test_lockout_expires_after_cooloff(self):
        response = self.attempt_login(self.email, self.wrong_password, expect_success=False)
        self.assertContains(response, 'Too Many Attempts', status_code=403)
        sleep(2)
        self.log_in_user(user=self.email, password=self.password)
        self.assertIn('_auth_user_id', self.client.session)

    # @override_settings(AXES_FAILURE_LIMIT=2)
    # def test_login_attempts_reset(self):
    #     # lock the user out
    #     self.attempt_login(self.email, self.wrong_password, expect_success=False)
    #     response = self.attempt_login(self.email, self.wrong_password, expect_success=False)
    #     self.assertContains(response, 'Too Many Attempts', status_code=403)
    #     self.assertContains(response, 'Reset my password', status_code=403)
    #     aa = AccessAttempt.objects.get(username=self.email)
    #     self.assertEqual(aa.failures_since_start, 2)

    #     # get the reset password email/link
    #     self.client.post(reverse('password_reset'), {"email": self.email}, secure=True)
    #     message = mail.outbox[0]
    #     reset_url = next(line for line in message.body.rstrip().split("\n") if line.startswith('http'))

    #     # go through with the reset
    #     response = self.client.get(reset_url, follow=True, secure=True)
    #     post_url = response.redirect_chain[0][0]
    #     response = self.client.post(post_url, {'new_password1': self.new_password, 'new_password2': self.new_password}, follow=True, secure=True)
    #     self.assertContains(response, 'Your password has been set')
    #     self.assertFalse(AccessAttempt.objects.filter(username=self.email).exists())

    #     # verify you get the normal form errors, not the lockout page,
    #     # if you fail again
    #     response = self.attempt_login(self.email, self.wrong_password, expect_success=False)
    #     self.assertContains(response, 'class="field-error"', status_code=200)

    #     # verify you CAN login with the new password
    #     self.log_in_user(user=self.email, password=self.new_password)
