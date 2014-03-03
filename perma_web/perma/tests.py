from django.core.urlresolvers import reverse
from django.test import TestCase
from .models import *
from .urls import urlpatterns

# to run tests:
# python manage.py test perma

class ViewsTestCase(TestCase):
    """ Test views. """

    fixtures = ['fixtures/groups.json','fixtures/users.json']

    def setUp(self):
        pass

    def log_in_user(self, username, password='pass'):
        user_obj = LinkUser.objects.get(email=username)
        resp = self.client.post(reverse('user_management_limited_login'), {'username':username,'password':password})
        # TODO: check resp to see if login worked

    def test_public_views(self):
        # test static template views
        for urlpattern in urlpatterns:
            if urlpattern.callback.func_name == 'DirectTemplateView':
                url = reverse(urlpattern.name)
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200)

    def test_permissions(self):
        """Test who can log into restricted pages."""
        views = [
            {
                'urls': (
                    reverse('user_management_manage_registrar'),
                    reverse('user_management_manage_single_registrar', kwargs={'registrar_id': 1}),
                    reverse('user_management_manage_registrar_member'),
                    reverse('user_management_manage_single_registrar_member', kwargs={'user_id': 2}),
                    reverse('user_management_manage_single_registrar_member_delete', kwargs={'user_id': 2}),
                    reverse('user_management_manage_single_registrar_member_reactivate', kwargs={'user_id': 2}),
                    reverse('user_management_manage_user'),
                    reverse('user_management_manage_single_user', kwargs={'user_id': 4}),
                    reverse('user_management_manage_single_user_delete', kwargs={'user_id': 4}),
                    reverse('user_management_manage_single_user_reactivate', kwargs={'user_id': 4}),

                ),
                'allowed': ('test_registry_member@example.com',),
                'denied': (
                    'test_registrar_member@example.com', 'test_vesting_member@example.com', 'test_user@example.com',
                    'test_vesting_manager@example.com')
            },
            {
                'urls': (
                    reverse('user_management_manage_vesting_manager'),
                    reverse('user_management_manage_single_vesting_manager', kwargs={'user_id': 5}),
                    reverse('user_management_manage_single_vesting_manager_delete', kwargs={'user_id': 5}),
                    reverse('user_management_manage_single_vesting_manager_reactivate', kwargs={'user_id': 5}),
                ),
                'allowed': ('test_registry_member@example.com', 'test_registrar_member@example.com',),
                'denied': (
                    'test_vesting_member@example.com', 'test_user@example.com', 'test_vesting_manager@example.com')
            },
            {
                'urls': (
                    reverse('user_management_manage_vesting_member'),
                    reverse('user_management_manage_single_vesting_member', kwargs={'user_id': 3}),
                    reverse('user_management_manage_single_vesting_member_delete', kwargs={'user_id': 3}),
                    reverse('user_management_manage_single_vesting_member_reactivate', kwargs={'user_id': 3}),
                ),
                'allowed': ('test_registry_member@example.com', 'test_registrar_member@example.com',
                            'test_vesting_manager@example.com'
                ),
                'denied': ('test_vesting_member@example.com', 'test_user@example.com',)
            },
            {
                'urls': (
                    reverse('user_management_vested_links'),
                ),
                'allowed': ('test_registry_member@example.com', 'test_registrar_member@example.com',
                            'test_vesting_manager@example.com', 'test_vesting_member@example.com',
                ),
                'denied': ('test_user@example.com',)
            },
        ]

        for view in views:
            for url in view['urls']:
                # try while logged out
                self.client.logout()
                resp = self.client.get(url)
                self.assertRedirects(resp, settings.LOGIN_URL+"?next="+url)

                # try with valid users
                for user in view['allowed']:
                    self.log_in_user(user)
                    resp = self.client.get(url)
                    self.assertEqual(resp.status_code, 200)

                # try with invalid users
                for user in view['denied']:
                    self.log_in_user(user)
                    resp = self.client.get(url)
                    self.assertRedirects(resp, settings.LOGIN_REDIRECT_URL)
