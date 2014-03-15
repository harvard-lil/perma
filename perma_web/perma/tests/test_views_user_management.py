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
            ['registrar_member', {'a-registrar': 1}],
            ['user', {}],
            ['vesting_manager', {'a-vesting_org': 1}],
            ['vesting_member', {'a-vesting_org': 1}],
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


    def test_permissions(self):
        """Test who can log into restricted pages."""
        all_users = {
            'test_registry_member@example.com',
            'test_registrar_member@example.com',
            'test_vesting_member@example.com',
            'test_user@example.com',
            'test_vesting_manager@example.com'
        }
        any_user_allowed = {
            'user_management_manage_account',
            'user_management_created_links',
            'user_management_create_link',
        }
        views = [
            {
                'urls': [
                    ['user_management_manage_registrar'],
                    ['user_management_manage_single_registrar', {'kwargs':{'registrar_id': 1}}],
                    ['user_management_manage_registrar_member'],
                    ['user_management_manage_single_registrar_member', {'kwargs':{'user_id': 2}}],
                    ['user_management_manage_single_registrar_member_delete', {'kwargs':{'user_id': 2}}],
                    ['user_management_manage_single_registrar_member_reactivate', {'kwargs':{'user_id': 2}}],
                    ['user_management_manage_user'],
                    ['user_management_user_add_registrar', {'kwargs': {'user_id': 4}}],
                    ['user_management_user_add_vesting_org', {'kwargs': {'user_id': 4}}],
                    ['user_management_manage_single_user', {'kwargs':{'user_id': 4}}],
                    ['user_management_manage_single_user_delete', {'kwargs':{'user_id': 4}}],
                    ['user_management_manage_single_user_reactivate', {'kwargs':{'user_id': 4}}],
                ],
                'allowed': {'test_registry_member@example.com'},
            },
            {
                'urls': [
                    ['user_management_manage_vesting_manager'],
                    ['user_management_manage_vesting_org'],
                    ['user_management_manage_single_vesting_org', {'kwargs':{'vesting_org_id':1}}],
                    ['user_management_manage_single_vesting_manager', {'kwargs':{'user_id': 5}}],
                    ['user_management_manage_single_vesting_manager_delete', {'kwargs':{'user_id': 5}}],
                    ['user_management_manage_single_vesting_manager_reactivate', {'kwargs':{'user_id': 5}}],
                ],
                'allowed': {'test_registry_member@example.com', 'test_registrar_member@example.com'},
            },
            {
                'urls': [
                    ['user_management_manage_vesting_member'],
                    ['user_management_manage_single_vesting_member', {'kwargs':{'user_id': 3}}],
                    ['user_management_manage_single_vesting_member_delete', {'kwargs':{'user_id': 3}}],
                    ['user_management_manage_single_vesting_member_reactivate', {'kwargs':{'user_id': 3}}],
                ],
                'allowed': {'test_registry_member@example.com', 'test_registrar_member@example.com',
                            'test_vesting_manager@example.com'}
            },
            {
                'urls': [
                    ['user_management_vested_links'],
                ],
                'allowed': {'test_registry_member@example.com', 'test_registrar_member@example.com',
                            'test_vesting_manager@example.com', 'test_vesting_member@example.com'}
            },
        ]

        views_tested = set()
        for view in views:
            for url in view['urls']:
                view_name = url[0]
                reverse_kwargs = url[1] if len(url)>1 else {}
                views_tested.add(view_name)
                url = reverse(view_name, **reverse_kwargs)

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
                for user in all_users - view['allowed']:
                    self.log_in_user(user)
                    resp = self.client.get(url)
                    self.assertRedirects(resp, settings.LOGIN_REDIRECT_URL)

        for view in any_user_allowed:
            self.get(view)

        # make sure that all ^manage/ views were tested
        for urlpattern in urlpatterns:
            if urlpattern.name not in any_user_allowed and urlpattern._regex.startswith(r'^manage/'):
                self.assertTrue(urlpattern.name in views_tested,
                                "Permissions not checked for view '%s' -- add to 'views' or 'any_user_allowed'." % urlpattern.name)