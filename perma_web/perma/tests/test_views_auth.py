from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from perma.models import LinkUser

class AuthViewsTestCase(TestCase):
    fixtures = ['fixtures/groups.json','fixtures/users.json']

    def setUp(self):
        self.client = Client()

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


    def test_logout(self):
        """
        Test our logout link
        """

        self.assertNotIn('_auth_user_id', self.client.session)
            
        # Login with our client and logout with our view
        self.client.login(username='test_user@example.com', password='pass')
        self.assertIn('_auth_user_id', self.client.session)
        self.client.get(reverse('logout'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_password_change(self):
        """
        Let's make sure we can login and chagne our password
        """

        self.client.login(username='test_user@example.com', password='pass')
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('password_change'), 
            {'old_password':'pass', 'new_password1':'changed-password', 
            'new_password2':'changed-password'})
                
        self.client.logout()
        
        # Try to login with our old password
        self.client.login(username='test_user@example.com', password='pass')
        self.assertNotIn('_auth_user_id', self.client.session)

        self.client.logout()
        
        # Try to login with our old password
        self.client.login(username='test_user@example.com', password='changed-password')
        self.assertIn('_auth_user_id', self.client.session)