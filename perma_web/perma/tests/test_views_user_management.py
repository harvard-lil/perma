from django.core.urlresolvers import reverse

from perma.models import *
from perma.urls import urlpatterns

from .utils import PermaTestCase


class UserManagementViewsTestCase(PermaTestCase):

    def test_views(self):
        self.log_in_user('test_registry_member@example.com')

        # manage_registrar
        self.post_form('user_management_manage_registrar', {
                'a-name':'test_views_registrar',
                'a-email':'test@test.com',
                'a-website':'http://test.com'},
            success_url=reverse('user_management_manage_registrar'),
            success_query=Registrar.objects.filter(name='test_views_registrar'))

        # manage_single_registrar
        self.post_form('user_management_manage_single_registrar', reverse_kwargs={'args':[1]},
                       data={
                            'a-name': 'test_views_registrar2',
                            'a-email': 'test@test.com2',
                            'a-website': 'http://test.com2'},
                       success_url=reverse('user_management_manage_registrar'),
                       success_query=Registrar.objects.filter(name='test_views_registrar2'))

        # manage_vesting_org
        self.post_form('user_management_manage_vesting_org',
                       data={
                           'a-name': 'test_views_vesting_org',
                           'a-registrar': 1},
                       success_url=reverse('user_management_manage_vesting_org'),
                       success_query=VestingOrg.objects.filter(name='test_views_vesting_org'))
        self.log_in_user('test_registrar_member@example.com')
        self.post_form('user_management_manage_vesting_org',
                       data={
                           'a-name': 'test_views_vesting_org2'},
                       success_url=reverse('user_management_manage_vesting_org'),
                       success_query=VestingOrg.objects.filter(name='test_views_vesting_org2'))
        self.log_in_user('test_registry_member@example.com')

        # manage user views
        self.post_form('user_management_manage_single_vesting_org', reverse_kwargs={'args':[1]},
                       data={
                           'a-name': 'test_views_vesting_org3'},
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
            ['vesting_user', {'a-vesting_org': 1}],
        ]:
            # create user
            email += '1'
            self.post_form('user_management_manage_' + view_name,
                           data=dict(base_user.items() + form_extras.items() + [['a-email', email]]),
                           success_url=reverse('user_management_manage_' + view_name),
                           success_query=LinkUser.objects.filter(email=email))
            new_user = LinkUser.objects.get(email=email)

            # edit user
            email += '1'
            self.post_form('user_management_manage_single_' + view_name, reverse_kwargs={'args':[new_user.pk]},
                           data=dict(base_user.items() + form_extras.items() + [
                               ['a-email', email],
                               ['a-group',1],
                               ]),
                           success_url=reverse('user_management_manage_' + view_name),
                           success_query=LinkUser.objects.filter(email=email))


            # delete user (deactivate)
            new_user.is_confirmed = True
            new_user.save()
            self.post_form('user_management_manage_single_' + view_name + '_delete',
                           reverse_kwargs={'args': [new_user.pk]},
                           success_url=reverse('user_management_manage_' + view_name))

            # reactivate user
            self.post_form('user_management_manage_single_' + view_name + '_reactivate',
                           reverse_kwargs={'args': [new_user.pk]},
                           success_url=reverse('user_management_manage_' + view_name))

            # delete user (really delete)
            new_user.is_confirmed = False
            new_user.save()
            self.post_form('user_management_manage_single_' + view_name + '_delete',
                           reverse_kwargs={'args': [new_user.pk]},
                           success_url=reverse('user_management_manage_' + view_name))

        # user_add_registrar and user_add_vesting_org
        user = LinkUser.objects.get(email='test_user@example.com')
        session = self.client.session
        session['old_group'] = 'user'
        session.save()
        # - pick registrar
        self.post_form('user_management_user_add_registrar', reverse_kwargs={'args': [user.pk]},
                       data={'a-registrar': 1},
                       success_url=reverse('user_management_manage_user'))
        # - pick vesting org
        self.post_form('user_management_user_add_vesting_org', reverse_kwargs={'args': [user.pk]},
                       data={'a-vesting_org': 1},
                       success_url=reverse('user_management_manage_user'))

        # manage_account
        self.post_form('user_management_manage_account',
                       data={
                           'a-first_name': 'First',
                           'a-last_name': 'Last',
                           'a-email': 'test_registry_member@example.com'
                       },
                       success_url=reverse('user_management_manage_account'))
