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
        user_logins = [
            None,
            {'username':'test_registry_member@example.com','password':'pass'},
        ]

        for user_login in user_logins:

            # user login
            if user_login:
                user_obj = LinkUser.objects.get(email=user_login['username'])
                resp = self.client.post(reverse('user_management_limited_login'),user_login)
                # TODO: check resp to see if login worked
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