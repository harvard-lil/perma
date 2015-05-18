from django.core.urlresolvers import reverse

from perma.models import *
from perma.urls import urlpatterns

from .utils import PermaTestCase


class UserManagementViewsTestCase(PermaTestCase):

    def test_account_creation_views(self):
        # user registration
        new_user_email = "new_email@test.com"
        self.submit_form('register', {'email': new_user_email, 'first_name': 'Test', 'last_name': 'Test'},
                       success_url=reverse('register_email_instructions'),
                       success_query=LinkUser.objects.filter(email=new_user_email))

        confirmation_code = LinkUser.objects.get(email=new_user_email).confirmation_code

        # check duplicate email
        self.submit_form('register', {'email': new_user_email, 'first_name': 'Test', 'last_name': 'Test'},
                              error_keys=['email'])

        # reg confirm - bad confirmation code
        response = self.submit_form('register_password', reverse_kwargs={'args':['bad_confirmation_code']})
        self.assertTrue('no_code' in response.context)

        # reg confirm - non-matching passwords
        response = self.submit_form('register_password', reverse_kwargs={'args': [confirmation_code]},
                                    data={'new_password1':'a', 'new_password2':'b'},
                                    error_keys=['new_password2'])

        # reg confirm - correct
        response = self.submit_form('register_password', reverse_kwargs={'args': [confirmation_code]},
                                    data={'new_password1': 'a', 'new_password2': 'a'},
                                    success_url=reverse('user_management_limited_login'))

