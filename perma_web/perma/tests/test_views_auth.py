from django.core.urlresolvers import reverse
from django.test import override_settings

from .utils import PermaTestCase

from perma.models import LinkUser


class AuthViewsTestCase(PermaTestCase):

    def test_login(self):
        """
        Test the login form
        We should get redirected to the create page
        """

        # Login through our form and make sure we get redirected to our create page
        response = self.client.post(reverse('user_management_limited_login'),
            {'username':'test_user@example.com', 'password':'pass'})
        create_url = 'login' not in response['Location']
        self.assertEqual(create_url, True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

    @override_settings(VALIDATE_ALL_PASSWORDS=True)
    def test_all_passwords_validated_with_setting(self):
        # Login through our form and make sure we get asked to change our password
        response = self.client.post(
            reverse('user_management_limited_login'),
            {'username':'test_user@example.com', 'password':'pass'})
        self.assertEqual(response.status_code, '200')
        self.assertIn('Your Password Has Expired', response.content)
        self.assertNotIn('_auth_user_id', self.client.session)


    def test_deactived_user_login(self):
        self.submit_form('user_management_limited_login',
                          data = {'username': 'deactivated_registrar_user@example.com',
                                  'password': 'pass'},
                          success_url=reverse('user_management_account_is_deactivated'))

    def test_unactived_user_login(self):
        self.submit_form('user_management_limited_login',
                          data = {'username': 'unactivated_faculty_user@example.com',
                                  'password': 'pass'},
                          success_url=reverse('user_management_not_active'))

    def test_logout(self):
        """
        Test our logout link
        """

        # Login with our client and logout with our view
        self.client.login(username='test_user@example.com', password='pass')
        self.assertIn('_auth_user_id', self.client.session)
        self.get('logout')
        self.submit_form('logout')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_password_change(self):
        """
        Let's make sure we can login and change our password
        """

        self.client.login(username='test_user@example.com', password='pass')
        self.assertIn('_auth_user_id', self.client.session)

        self.client.post(reverse('password_change'),
            {'old_password':'pass', 'new_password1':'changed-password1',
            'new_password2':'changed-password1'})

        self.client.logout()

        # Try to login with our old password
        self.client.login(username='test_user@example.com', password='pass')
        self.assertNotIn('_auth_user_id', self.client.session)

        self.client.logout()

        # Try to login with our new password
        self.client.login(username='test_user@example.com', password='changed-password1')
        self.assertIn('_auth_user_id', self.client.session)

    @override_settings(VALIDATE_ALL_PASSWORDS=True)
    def test_password_update(self):
        user = LinkUser.objects.get(email='test_user@example.com')
        user.save_new_confirmation_code()
        response = self.client.post(reverse('password_update'), {
            'confirmation_code':user.confirmation_code,
            'new_password1':'changed-password1',
            'new_password2':'changed-password1'
        })
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

        # Try to login with our old password
        self.client.login(username='test_user@example.com', password='pass')
        self.assertNotIn('_auth_user_id', self.client.session)

        # Try to login with our new password
        self.client.login(username='test_user@example.com', password='changed-password1')
        self.assertIn('_auth_user_id', self.client.session)
