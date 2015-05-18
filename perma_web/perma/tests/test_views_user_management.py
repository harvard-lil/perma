from django.core.urlresolvers import reverse

from perma.models import *
from perma.urls import urlpatterns

from .utils import PermaTestCase


class UserManagementViewsTestCase(PermaTestCase):

    def test_management_views(self):
        self.log_in_user('test_registry_member@example.com')

        # manage_registrar
        self.submit_form('user_management_manage_registrar', {
                'a-name':'test_views_registrar',
                'a-email':'test@test.com',
                'a-website':'http://test.com'},
            success_url=reverse('user_management_manage_registrar'),
            success_query=Registrar.objects.filter(name='test_views_registrar'))

        # manage_single_registrar
        self.submit_form('user_management_manage_single_registrar', reverse_kwargs={'args':[1]},
                       data={
                            'a-name': 'test_views_registrar2',
                            'a-email': 'test@test.com2',
                            'a-website': 'http://test.com2'},
                       success_url=reverse('user_management_manage_registrar'),
                       success_query=Registrar.objects.filter(name='test_views_registrar2'))

        # manage_vesting_org
        self.submit_form('user_management_manage_vesting_org',
                       data={
                           'a-name': 'test_views_vesting_org',
                           'a-registrar': 1},
                       success_url=reverse('user_management_manage_vesting_org'),
                       success_query=VestingOrg.objects.filter(name='test_views_vesting_org'))
        self.log_in_user('test_registrar_member@example.com')
        self.submit_form('user_management_manage_vesting_org',
                       data={
                           'a-name': 'test_views_vesting_org2'},
                       success_url=reverse('user_management_manage_vesting_org'),
                       success_query=VestingOrg.objects.filter(name='test_views_vesting_org2'))
        

        # manage user views
        self.submit_form('user_management_manage_single_vesting_org', reverse_kwargs={'args':[1]},
                       data={
                           'a-name': 'test_views_vesting_org3'},
                       success_url=reverse('user_management_manage_vesting_org'),
                       success_query=VestingOrg.objects.filter(name='test_views_vesting_org3'))
        self.log_in_user('test_registry_member@example.com')
        self.submit_form('user_management_manage_single_vesting_org', reverse_kwargs={'args':[1]},
                       data={
                           'a-name': 'test_views_vesting_org3',
                           'a-registrar': 1},
                       success_url=reverse('user_management_manage_vesting_org'),
                       success_query=VestingOrg.objects.filter(name='test_views_vesting_org3'))

        base_user = {
            'a-first_name':'First',
            'a-last_name':'Last',
        }
        email = 'test_views_test@test.com'

        for view_name, form_extras in [
            ['registrar_user', {'a-registrar': 1}],
            ['user', {}],
        ]:
            # create user
            email += '1'
            self.submit_form('user_management_manage_' + view_name,
                           data=dict(base_user.items() + form_extras.items() + [['a-email', email]]),
                           success_url=reverse('user_management_manage_' + view_name),
                           success_query=LinkUser.objects.filter(email=email))
            new_user = LinkUser.objects.get(email=email)

            # delete user (deactivate)
            new_user.is_confirmed = True
            new_user.save()
            self.submit_form('user_management_manage_single_' + view_name + '_delete',
                           reverse_kwargs={'args': [new_user.pk]},
                           success_url=reverse('user_management_manage_' + view_name))

            # reactivate user
            self.submit_form('user_management_manage_single_' + view_name + '_reactivate',
                           reverse_kwargs={'args': [new_user.pk]},
                           success_url=reverse('user_management_manage_' + view_name))

            # delete user (really delete)
            new_user.is_confirmed = False
            new_user.save()
            self.submit_form('user_management_manage_single_' + view_name + '_delete',
                           reverse_kwargs={'args': [new_user.pk]},
                           success_url=reverse('user_management_manage_' + view_name))

        # manage_account
        self.submit_form('user_management_settings_profile',
                       data={
                           'a-first_name': 'First',
                           'a-last_name': 'Last',
                           'a-email': 'test_registry_member@example.com'
                       },
                       success_url=reverse('user_management_settings_profile'))

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

