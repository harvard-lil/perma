from django.core.urlresolvers import reverse
from django.test import TestCase
from models import *

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
        """Test all public, static views, both logged in and logged out."""

        # we're going to test each of these views. Format is [ url, expected template, expected context values ]
        views = [
            [reverse('landing'), 'landing.html', {'this_page': 'landing',}],
            [reverse('about'), 'about.html', {}],
            [reverse('faq'), 'faq.html', {}],
            [reverse('contact'), 'contact.html', {}],
            [reverse('copyright_policy'), 'copyright_policy.html', {}],
            [reverse('terms_of_service'), 'terms_of_service.html', {}],
            [reverse('privacy_policy'), 'privacy_policy.html', {}],
        ]

        # try each view while logged in as each of these users
        user_logins = [None, 'test_registry_member@example.com']

        for user_login in user_logins:

            # user login
            if user_login:
                self.log_in_user(user_login)
            else:
                user_obj = None

            # try each view
            for url, template, context in views:
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200) # check response status code
                self.assertTemplateUsed(template)       # check response template
                for key, val in context.items():        # check response context
                    self.assertEqual(resp.context[-1].get(key, None), val)
                if user_obj:                            # check that proper user object is included in context
                    self.assertEqual(resp.context[-1]['user'], user_obj)

            self.client.logout()

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
                    reverse('user_management_manage_journal_manager'),
                    reverse('user_management_manage_single_journal_manager', kwargs={'user_id': 5}),
                    reverse('user_management_manage_single_journal_manager_delete', kwargs={'user_id': 5}),
                    reverse('user_management_manage_single_journal_manager_reactivate', kwargs={'user_id': 5}),
                ),
                'allowed': ('test_registry_member@example.com', 'test_registrar_member@example.com',),
                'denied': (
                    'test_vesting_member@example.com', 'test_user@example.com', 'test_vesting_manager@example.com')
            },
            {
                'urls': (
                    reverse('user_management_manage_journal_member'),
                    reverse('user_management_manage_single_journal_member', kwargs={'user_id': 3}),
                    reverse('user_management_manage_single_journal_member_delete', kwargs={'user_id': 3}),
                    reverse('user_management_manage_single_journal_member_reactivate', kwargs={'user_id': 3}),
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
                    #import pdb; pdb.set_trace()
                    self.assertEqual(resp.status_code, 200)

                # try with invalid users
                for user in view['denied']:
                    self.log_in_user(user)
                    resp = self.client.get(url)
                    self.assertRedirects(resp, settings.LOGIN_REDIRECT_URL)
