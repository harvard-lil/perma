from django.core.urlresolvers import reverse

from perma.models import *

from .utils import PermaTestCase


class UserManagementViewsTestCase(PermaTestCase):

    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/archive.json',
                ]

    def setUp(self):
        super(UserManagementViewsTestCase, self).setUp()

        self.admin_user = LinkUser.objects.get(pk=1)
        self.registrar_member = LinkUser.objects.get(pk=2)
        self.regular_user = LinkUser.objects.get(pk=4)
        self.registrar = self.registrar_member.registrar
        self.unrelated_registrar = Registrar.objects.exclude(pk=self.registrar.pk).first()
        self.organization = Organization.objects.get(pk=1)
        self.organization_member = self.organization.users.first()
        self.another_organization = Organization.objects.get(pk=2)
        self.unrelated_organization = self.unrelated_registrar.organizations.first()
        self.deletable_organization = Organization.objects.get(pk=3)

    ### REGISTRAR A/E/D VIEWS ###

    def test_registrar_list_filters(self):
        # get just approved registrars
        self.get('user_management_manage_registrar',
                 user=self.admin_user,
                 request_kwargs={'data':{'status':'approved'}})

        # get just pending registrars
        self.get('user_management_manage_registrar',
                 user=self.admin_user,
                 request_kwargs={'data': {'status': 'pending'}})

    def test_admin_can_create_registrar(self):
        self.submit_form(
            'user_management_manage_registrar', {
                'a-name':'test_views_registrar',
                'a-email':'test@test.com',
                'a-website':'http://test.com'
            },
            user=self.admin_user,
            success_url=reverse('user_management_manage_registrar'),
            success_query=Registrar.objects.filter(name='test_views_registrar'))

    def test_admin_can_update_registrar(self):
        self.submit_form('user_management_manage_single_registrar',
                         user=self.admin_user,
                         reverse_kwargs={'args':[self.unrelated_registrar.pk]},
                         data={
                              'a-name': 'new_name',
                              'a-email': 'test@test.com2',
                              'a-website': 'http://test.com'},
                         success_url=reverse('user_management_manage_registrar'),
                         success_query=Registrar.objects.filter(name='new_name'))

    def test_registrar_can_update_registrar(self):
        self.submit_form('user_management_manage_single_registrar',
                         user=self.registrar_member,
                         reverse_kwargs={'args': [self.registrar.pk]},
                         data={
                             'a-name': 'new_name',
                             'a-email': 'test@test.com2',
                             'a-website': 'http://test.com'},
                         success_url=reverse('user_management_settings_organizations'),
                         success_query=Registrar.objects.filter(name='new_name'))

    def test_registrar_cannot_update_unrelated_registrar(self):
        self.get('user_management_manage_single_registrar',
                 user=self.registrar_member,
                 reverse_kwargs={'args': [self.unrelated_registrar.pk]},
                 require_status_code=404)

    ### ORGANIZATION A/E/D VIEWS ###

    def test_organization_list_filters(self):
        # get orgs for a single registrar
        self.get('user_management_manage_organization',
                 user=self.admin_user,
                 request_kwargs={'data': {'registrar': self.registrar.pk}})

    def test_admin_can_create_organization(self):
        self.submit_form('user_management_manage_organization',
                         user=self.admin_user,
                         data={
                             'a-name': 'new_name',
                             'a-registrar': self.registrar.pk},
                         success_url=reverse('user_management_manage_organization'),
                         success_query=Organization.objects.filter(name='new_name'))

    def test_registrar_can_create_organization(self):
        self.submit_form('user_management_manage_organization',
                         user=self.registrar_member,
                         data={
                             'a-name': 'new_name'},
                         success_url=reverse('user_management_manage_organization'),
                         success_query=Organization.objects.filter(name='new_name'))

    def test_admin_can_update_organization(self):
        self.submit_form('user_management_manage_single_organization',
                         user=self.admin_user,
                         reverse_kwargs={'args':[self.organization.pk]},
                         data={
                             'a-name': 'new_name',
                             'a-registrar': self.registrar.pk},
                         success_url=reverse('user_management_manage_organization'),
                         success_query=Organization.objects.filter(name='new_name'))

    def test_registrar_can_update_organization(self):
        self.submit_form('user_management_manage_single_organization',
                         user=self.registrar_member,
                         reverse_kwargs={'args':[self.organization.pk]},
                         data={
                             'a-name': 'new_name'},
                         success_url=reverse('user_management_manage_organization'),
                         success_query=Organization.objects.filter(name='new_name'))

    def test_org_user_can_update_organization(self):
        self.submit_form('user_management_manage_single_organization',
                         user=self.organization_member,
                         reverse_kwargs={'args': [self.organization.pk]},
                         data={
                             'a-name': 'new_name'},
                         success_url=reverse('user_management_manage_organization'),
                         success_query=Organization.objects.filter(name='new_name'))

    def test_registrar_cannot_update_unrelated_organization(self):
        self.get('user_management_manage_single_organization',
                 user=self.registrar_member,
                 reverse_kwargs={'args': [self.unrelated_organization.pk]},
                 require_status_code=404)

    def test_org_user_cannot_update_unrelated_organization(self):
        self.get('user_management_manage_single_organization',
                 user=self.organization_member,
                 reverse_kwargs={'args': [self.unrelated_organization.pk]},
                 require_status_code=404)

    def _delete_organization(self, user):
        self.submit_form('user_management_manage_single_organization_delete',
                         user=user,
                         reverse_kwargs={'args': [self.deletable_organization.pk]},
                         success_url=reverse('user_management_manage_organization'),
                         success_query=Organization.objects.filter(user_deleted=True, pk=self.deletable_organization.pk))

    def test_admin_user_can_delete_empty_organization(self):
        self._delete_organization(self.admin_user)

    def test_registrar_user_can_delete_empty_organization(self):
        self._delete_organization(self.deletable_organization.registrar.users.first())

    def test_org_user_can_delete_empty_organization(self):
        self._delete_organization(self.deletable_organization.users.first())

    def test_cannot_delete_nonempty_organization(self):
        self.submit_form('user_management_manage_single_organization_delete',
                         user=self.admin_user,
                         reverse_kwargs={'args': [self.organization.pk]},
                         require_status_code=404)

    ### USER A/E/D VIEWS ###

    def test_create_and_delete_user(self):
        self.log_in_user(self.admin_user)

        base_user = {
            'a-first_name':'First',
            'a-last_name':'Last',
        }
        email = 'test_views_test@test.com'

        for view_name, form_extras in [
            ['registrar_user', {'a-registrar': 1}],
            ['user', {}],
            ['organization_user', {'a-organizations': 1}],
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

    ### UPGRADING USERS ###

    def test_admin_user_can_add_user_to_org(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=self.regular_user.organizations.filter(pk=self.organization.pk))

    def test_registrar_user_can_add_user_to_org(self):
        self.log_in_user(self.registrar_member)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=self.regular_user.organizations.filter(pk=self.organization.pk))

    def test_org_user_can_add_user_to_org(self):
        self.log_in_user(self.organization_member)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=self.regular_user.organizations.filter(pk=self.organization.pk))

    def test_registrar_user_cannot_add_user_to_inaccessible_org(self):
        self.log_in_user(self.registrar_member)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.unrelated_organization.pk},
                         query_params={'email': self.regular_user.email},
                         error_keys=['organizations'])
        self.assertFalse(self.regular_user.organizations.filter(pk=self.unrelated_organization.pk).exists())

    def test_org_user_cannot_add_user_to_inaccessible_org(self):
        self.log_in_user(self.organization_member)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.another_organization.pk},
                         query_params={'email': self.regular_user.email},
                         error_keys=['organizations'])
        self.assertFalse(self.regular_user.organizations.filter(pk=self.another_organization.pk).exists())

    def test_cannot_add_admin_user_to_org(self):
        self.log_in_user(self.organization_member)
        resp = self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': self.admin_user.email})
        self.assertIn("is an admin user", resp.content)
        self.assertFalse(self.admin_user.organizations.exists())

    def test_cannot_add_registrar_user_to_org(self):
        self.log_in_user(self.organization_member)
        resp = self.submit_form('user_management_organization_user_add_user',
                                data={'a-organizations': self.organization.pk},
                                query_params={'email': self.registrar_member.email})
        self.assertIn("is a registrar member", resp.content)
        self.assertFalse(self.registrar_member.organizations.exists())

    ### SETTINGS ###

    def test_user_can_change_own_settings(self):
        self.submit_form('user_management_settings_profile',
                         user=self.admin_user,
                         data={
                             'a-first_name': 'Newfirst',
                             'a-last_name': 'Newlast',
                             'a-email': 'test_registry_member@example.com'
                         },
                         success_url=reverse('user_management_settings_profile'),
                         success_query=LinkUser.objects.filter(first_name='Newfirst'))

    ### SIGNUP ###

    def test_account_creation_views(self):
        # user registration
        new_user_email = "new_email@test.com"
        self.submit_form('sign_up', {'email': new_user_email, 'first_name': 'Test', 'last_name': 'Test'},
                       success_url=reverse('register_email_instructions'),
                       success_query=LinkUser.objects.filter(email=new_user_email))

        confirmation_code = LinkUser.objects.get(email=new_user_email).confirmation_code

        # reg confirm - non-matching passwords
        response = self.submit_form('register_password', reverse_kwargs={'args': [confirmation_code]},
                                    data={'new_password1':'a', 'new_password2':'b'},
                                    error_keys=['new_password2'])

        # reg confirm - correct
        response = self.submit_form('register_password', reverse_kwargs={'args': [confirmation_code]},
                                    data={'new_password1': 'a', 'new_password2': 'a'},
                                    success_url=reverse('user_management_limited_login'))

    def test_signup_with_existing_email_rejected(self):
        self.submit_form('sign_up',
                         {'email': self.registrar_member.email, 'first_name': 'Test', 'last_name': 'Test'},
                         error_keys=['email'])

    def test_registration_confirmation_with_bad_code_rejected(self):
        response = self.submit_form('register_password', reverse_kwargs={'args':['bad_confirmation_code']})
        self.assertTrue('no_code' in response.context)

    ### ADMIN STATS ###

    def test_admin_stats(self):
        self.log_in_user(self.admin_user)
        self.get('user_management_stats', reverse_kwargs={'args':['days']})
        self.get('user_management_stats', reverse_kwargs={'args':['celery']})
        self.get('user_management_stats', reverse_kwargs={'args':['random']})
        self.get('user_management_stats', reverse_kwargs={'args':['emails']})
