# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core import mail
from django.conf import settings
from django.urls import NoReverseMatch

from mock import patch, sentinel

from perma.models import *
from perma.exceptions import PermaPaymentsCommunicationException

from .utils import PermaTestCase

from random import random
import re
from bs4 import BeautifulSoup


# Fixtures

def spoof_current_monthly_subscription():
    return {
        "status": "Current",
        "rate": "Sentinel Rate",
        "frequency": "monthly"
    }

def spoof_on_hold_monthly_subscription():
    return {
        "status": "On Hold",
        "rate": "Sentinel Rate",
        "frequency": "monthly"
    }


def spoof_cancellation_requested_subscription():
    return {
        "status": "Cancellation Requested",
        "rate": "Sentinel Rate",
        "frequency": "Sentinel Frequency"
    }


# Tests

class UserManagementViewsTestCase(PermaTestCase):

    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/archive.json',
                ]

    def setUp(self):
        super(UserManagementViewsTestCase, self).setUp()

        self.admin_user = LinkUser.objects.get(pk=1)
        self.registrar_user = LinkUser.objects.get(pk=2)
        self.regular_user = LinkUser.objects.get(pk=4)
        self.registrar = self.registrar_user.registrar
        self.pending_registrar = Registrar.objects.get(pk=2)
        self.unrelated_registrar = Registrar.objects.get(pk=2)
        self.unrelated_registrar_user = self.unrelated_registrar.users.first()
        self.organization = Organization.objects.get(pk=1)
        self.organization_user = self.organization.users.first()
        self.another_organization = Organization.objects.get(pk=2)
        self.unrelated_organization = self.unrelated_registrar.organizations.first()
        self.unrelated_organization_user = self.unrelated_organization.users.first()
        self.another_unrelated_organization_user = self.unrelated_organization.users.get(pk=11)
        self.deletable_organization = Organization.objects.get(pk=3)

    ### Helpers ###
    def pk_from_email(self, email):
        return LinkUser.objects.get(email=email).pk

    ### REGISTRAR A/E/D VIEWS ###

    def test_registrar_list_filters(self):
        # test assumptions: two registrars, one pending, one approved
        response = self.get('user_management_manage_registrar',
                             user=self.admin_user).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 4 registrars", count)
        self.assertEqual(response.count('needs approval'), 1)

        # get just approved registrars
        response = self.get('user_management_manage_registrar',
                             user=self.admin_user,
                             request_kwargs={'data':{'status':'approved'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 registrars", count)
        self.assertEqual(response.count('needs approval'), 0)

        # get just pending registrars
        response = self.get('user_management_manage_registrar',
                             user=self.admin_user,
                             request_kwargs={'data': {'status': 'pending'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 registrar", count)
        self.assertEqual(response.count('needs approval'), 1)

    def test_registrar_user_list_filters(self):
        # test assumptions: five users
        # - one deactivated
        # - one unactivated
        # - one from Test Library, three from Another Library, one from Test Firm
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 5 users", count)
        self.assertEqual(response.count('deactivated account'), 1)
        self.assertEqual(response.count('User must activate account'), 1)
        # registrar name appears by each user, and once in the filter dropdown
        self.assertEqual(response.count('Test Library'), 2)
        self.assertEqual(response.count('Another Library'), 4)
        self.assertEqual(response.count('Test Firm'), 2)

        # filter by registrar
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 1}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 2}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 users", count)
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 4}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)


        # filter by status
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'status': 'active'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 users", count)
        self.assertEqual(response.count('deactivated account'), 0)
        self.assertEqual(response.count('User must activate account'), 0)
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'status': 'deactivated'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count('deactivated account'), 1)
        self.assertEqual(response.count('User must activate account'), 0)
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'status': 'unactivated'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count('deactivated account'), 0)
        self.assertEqual(response.count('User must activate account'), 1)

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
                         user=self.registrar_user,
                         reverse_kwargs={'args': [self.registrar.pk]},
                         data={
                             'a-name': 'new_name',
                             'a-email': 'test@test.com2',
                             'a-website': 'http://test.com'},
                         success_url=reverse('user_management_settings_affiliations'),
                         success_query=Registrar.objects.filter(name='new_name'))

    def test_registrar_cannot_update_unrelated_registrar(self):
        self.get('user_management_manage_single_registrar',
                 user=self.registrar_user,
                 reverse_kwargs={'args': [self.unrelated_registrar.pk]},
                 require_status_code=404)

    def test_admin_can_approve_pending_registrar(self):
        self.submit_form('user_management_approve_pending_registrar',
                         user=self.admin_user,
                         data={'status':'approved'},
                         reverse_kwargs={'args': [self.pending_registrar.pk]},
                         success_query=Registrar.objects.filter(pk=self.pending_registrar.pk,
                                                                status="approved").exists())

    def test_admin_can_deny_pending_registrar(self):
        self.submit_form('user_management_approve_pending_registrar',
                         user=self.admin_user,
                         data={'status': 'denied'},
                         reverse_kwargs={'args': [self.pending_registrar.pk]},
                         success_query=Registrar.objects.filter(pk=self.pending_registrar.pk,
                                                                status="denied").exists())

    ### ORGANIZATION A/E/D VIEWS ###

    def test_organization_list_filters(self):
        # test assumptions: six orgs, three for Test Library and one for Another Library, two for Test Firm
        response = self.get('user_management_manage_organization',
                             user=self.admin_user).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 6 organizations", count)
        # registrar name appears by each org, once in the filter dropdown, once in the "add an org" markup
        self.assertEqual(response.count('Test Library'), 3 + 2)
        self.assertEqual(response.count('Test Firm'), 2 + 2)
        # 'Another Library' needs special handling because the fixture's org is
        # named 'Another Library's journal'. The "string" search finds the instance
        # by the org and the instance in the filter dropdown, but not the <option> in the "add an org" markup
        self.assertEqual(len(soup.find_all(string=re.compile(r"Another Library(?!')"))), 1 + 1)

        # get orgs for a single registrar
        response = self.get('user_management_manage_organization',
                             user=self.admin_user,
                             request_kwargs={'data': {'registrar': 1}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 organizations", count)
        response = self.get('user_management_manage_organization',
                             user=self.admin_user,
                             request_kwargs={'data': {'registrar': 2}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 organization", count)

    def test_org_user_list_filters(self):
        # test assumptions: seven users
        # - three from Test Journal
        # - one from Another Journal
        # - three from A Third Journal
        # - three from Another Library's Journal
        # - one from Some Case
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 7 users", count)
        # registrar name appears by each user, and once in the filter dropdown
        self.assertEqual(response.count('Test Journal'), 3 + 1)
        self.assertEqual(response.count('Another Journal'), 1 + 1)
        self.assertEqual(response.count("A Third Journal"), 3 + 1)
        self.assertEqual(response.count("Another Library's Journal"), 3 + 1)
        self.assertEqual(response.count("Some Case"), 1 + 1)

        # filter by org
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'org': 1}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 users", count)
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'org': 2}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'org': 3}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 users", count)
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'org': 4}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 users", count)
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'org': 5}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)

        # filter by registrar
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 1}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 5 users", count)
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 2}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 users", count)
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 4}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)

        # status filter tested in test_registrar_user_list_filters

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
                         user=self.registrar_user,
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
                         user=self.registrar_user,
                         reverse_kwargs={'args':[self.organization.pk]},
                         data={
                             'a-name': 'new_name'},
                         success_url=reverse('user_management_manage_organization'),
                         success_query=Organization.objects.filter(name='new_name'))

    def test_org_user_can_update_organization(self):
        self.submit_form('user_management_manage_single_organization',
                         user=self.organization_user,
                         reverse_kwargs={'args': [self.organization.pk]},
                         data={
                             'a-name': 'new_name'},
                         success_url=reverse('user_management_manage_organization'),
                         success_query=Organization.objects.filter(name='new_name'))

    def test_registrar_cannot_update_unrelated_organization(self):
        self.get('user_management_manage_single_organization',
                 user=self.registrar_user,
                 reverse_kwargs={'args': [self.unrelated_organization.pk]},
                 require_status_code=404)

    def test_org_user_cannot_update_unrelated_organization(self):
        self.get('user_management_manage_single_organization',
                 user=self.organization_user,
                 reverse_kwargs={'args': [self.unrelated_organization.pk]},
                 require_status_code=404)

    def _delete_organization(self, user, should_succeed=True):
        if should_succeed:
            self.submit_form('user_management_manage_single_organization_delete',
                              user=user,
                              reverse_kwargs={'args': [self.deletable_organization.pk]},
                              success_url=reverse('user_management_manage_organization'),
                              success_query=Organization.objects.filter(user_deleted=True, pk=self.deletable_organization.pk))
        else:
            self.submit_form('user_management_manage_single_organization_delete',
                              user=user,
                              reverse_kwargs={'args': [self.deletable_organization.pk]},
                              require_status_code=404)

    def test_admin_user_can_delete_empty_organization(self):
        self._delete_organization(self.admin_user)
        self._delete_organization(self.admin_user, False)

    def test_registrar_user_can_delete_empty_organization(self):
        self._delete_organization(self.deletable_organization.registrar.users.first())
        self._delete_organization(self.deletable_organization.registrar.users.first(), False)

    def test_org_user_can_delete_empty_organization(self):
        self._delete_organization(self.deletable_organization.users.first())
        self._delete_organization(self.deletable_organization.users.first(), False)

    def test_cannot_delete_nonempty_organization(self):
        self.submit_form('user_management_manage_single_organization_delete',
                         user=self.admin_user,
                         reverse_kwargs={'args': [self.organization.pk]},
                         require_status_code=404)

    ### USER A/E/D VIEWS ###

    def test_user_list_filters(self):
        # test assumptions: five users
        # - one aspiring court user, faculty user, journal user
        response = self.get('user_management_manage_user',
                             user=self.admin_user).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 5 users", count)
        self.assertEqual(response.count('Interested in a court account'), 1)
        self.assertEqual(response.count('Interested in a journal account'), 1)
        self.assertEqual(response.count('Interested in a faculty account'), 1)

        # filter by requested_account_type ("upgrade")
        response = self.get('user_management_manage_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'upgrade': 'court'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count('Interested in a court account'), 1)
        self.assertEqual(response.count('Interested in a journal account'), 0)
        self.assertEqual(response.count('Interested in a faculty account'), 0)
        response = self.get('user_management_manage_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'upgrade': 'journal'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count('Interested in a court account'), 0)
        self.assertEqual(response.count('Interested in a journal account'), 1)
        self.assertEqual(response.count('Interested in a faculty account'), 0)
        response = self.get('user_management_manage_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'upgrade': 'faculty'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count('Interested in a court account'), 0)
        self.assertEqual(response.count('Interested in a journal account'), 0)
        self.assertEqual(response.count('Interested in a faculty account'), 1)

        # status filter tested in test_registrar_user_list_filters

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
            self.submit_form('user_management_' + view_name + '_add_user',
                           data=dict(list(base_user.items()) + list(form_extras.items()) + [['a-email', email]]),
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

    ### ADDING NEW USERS TO ORGANIZATIONS ###

    def test_admin_user_can_add_new_user_to_org(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=LinkUser.objects.filter(email='doesnotexist@example.com',
                                                               organizations=self.organization).exists())


    def test_registrar_user_can_add_new_user_to_org(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=LinkUser.objects.filter(email='doesnotexist@example.com',
                                                               organizations=self.organization).exists())


    def test_org_user_can_add_new_user_to_org(self):
        self.log_in_user(self.organization_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=LinkUser.objects.filter(email='doesnotexist@example.com',
                                                               organizations=self.organization).exists())

    def test_registrar_user_cannot_add_new_user_to_inaccessible_org(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.unrelated_organization.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         error_keys=['organizations'])
        self.assertFalse(LinkUser.objects.filter(email='doesnotexist@example.com',
                                                 organizations=self.unrelated_organization).exists())

    def test_org_user_cannot_add_new_user_to_inaccessible_org(self):
        self.log_in_user(self.organization_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.unrelated_organization.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         error_keys=['organizations'])
        self.assertFalse(LinkUser.objects.filter(email='doesnotexist@example.com',
                                                 organizations=self.unrelated_organization).exists())

    ### ADDING EXISTING USERS TO ORGANIZATIONS ###

    def test_admin_user_can_add_existing_user_to_org(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=self.regular_user.organizations.filter(pk=self.organization.pk))

    def test_registrar_user_can_add_existing_user_to_org(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=self.regular_user.organizations.filter(pk=self.organization.pk))

    def test_org_user_can_add_existing_user_to_org(self):
        self.log_in_user(self.organization_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=self.regular_user.organizations.filter(pk=self.organization.pk))

    def test_registrar_user_cannot_add_existing_user_to_inaccessible_org(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.unrelated_organization.pk},
                         query_params={'email': self.regular_user.email},
                         error_keys=['organizations'])
        self.assertFalse(self.regular_user.organizations.filter(pk=self.unrelated_organization.pk).exists())

    def test_org_user_cannot_add_existing_user_to_inaccessible_org(self):
        self.log_in_user(self.organization_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.another_organization.pk},
                         query_params={'email': self.regular_user.email},
                         error_keys=['organizations'])
        self.assertFalse(self.regular_user.organizations.filter(pk=self.another_organization.pk).exists())

    def test_cannot_add_admin_user_to_org(self):
        self.log_in_user(self.organization_user)
        resp = self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': self.admin_user.email})
        self.assertIn("is an admin user", resp.content)
        self.assertFalse(self.admin_user.organizations.exists())

    def test_cannot_add_registrar_user_to_org(self):
        self.log_in_user(self.organization_user)
        resp = self.submit_form('user_management_organization_user_add_user',
                                data={'a-organizations': self.organization.pk},
                                query_params={'email': self.registrar_user.email})
        self.assertIn("is already a registrar user", resp.content)
        self.assertFalse(self.registrar_user.organizations.exists())

    ### VOLUNTARILY LEAVING ORGANIZATIONS ###

    def test_org_user_can_leave_org(self):
        u = LinkUser.objects.get(email='test_another_library_org_user@example.com')
        orgs = u.organizations.all()

        # check assumptions
        self.assertEqual(len(orgs), 2)

        # 404 if tries to leave non-existent org
        self.submit_form('user_management_organization_user_leave_organization',
                          user=u,
                          data={},
                          reverse_kwargs={'args': [999]},
                          require_status_code=404)

        # returns to affiliations page if still a member of at least one org
        self.submit_form('user_management_organization_user_leave_organization',
                          user=u,
                          data={},
                          reverse_kwargs={'args': [orgs[0].pk]},
                          success_url=reverse('user_management_settings_affiliations'))

        # returns to create/manage page if no longer a member of any orgs
        self.submit_form('user_management_organization_user_leave_organization',
                          user=u,
                          data={},
                          reverse_kwargs={'args': [orgs[1].pk]},
                          success_url=reverse('create_link'))

        # 404 if tries to leave an org they are not a member of
        self.submit_form('user_management_organization_user_leave_organization',
                          user=u,
                          data={},
                          reverse_kwargs={'args': [orgs[1].pk]},
                          require_status_code=404)


    ### REMOVING USERS FROM ORGANIZATIONS ###

    # Just try to access the page with remove/deactivate links

    def test_registrar_can_edit_org_user(self):
        # User from one of registrar's own orgs succeeds
        self.log_in_user(self.registrar_user)
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.organization_user.pk]})
        # User from another registrar's org fails
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.another_unrelated_organization_user.pk]},
                  require_status_code=404)
        # Repeat with the other registrar, to confirm we're
        # getting 404s because of permission reasons, not because the
        # test fixtures are broken.
        self.log_in_user(self.unrelated_registrar_user)
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.organization_user.pk]},
                  require_status_code=404)
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.another_unrelated_organization_user.pk]})

    def test_org_can_edit_org_user(self):
        # User from own org succeeds
        org_one_users = ['test_org_user@example.com', 'test_org_rando_user@example.com']
        org_two_users = ['test_another_library_org_user@example.com', 'test_another_org_user@example.com']

        self.log_in_user(org_one_users[0])
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.pk_from_email(org_one_users[1])]})
        # User from another org fails
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.pk_from_email(org_two_users[0])]},
                  require_status_code=404)
        # Repeat in reverse, to confirm we're
        # getting 404s because of permission reasons, not because the
        # test fixtures are broken.
        self.log_in_user(org_two_users[1])
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.pk_from_email(org_one_users[1])]},
                  require_status_code=404)
        # User from another org fails
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.pk_from_email(org_two_users[0])]})

    # Actually try removing them

    def test_can_remove_user_from_organization(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_manage_single_organization_user_remove',
                         data={'org': self.organization.pk},
                         reverse_kwargs={'args': [self.organization_user.pk]},
                         success_url=reverse('user_management_manage_organization_user'))
        self.assertFalse(self.organization_user.organizations.filter(pk=self.organization.pk).exists())

    def test_registrar_cannot_remove_unrelated_user_from_organization(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_manage_single_organization_user_remove',
                         data={'org': self.unrelated_organization.pk},
                         reverse_kwargs={'args': [self.unrelated_organization_user.pk]},
                         require_status_code=404)

    def test_org_user_cannot_remove_unrelated_user_from_organization(self):
        self.log_in_user(self.organization_user)
        self.submit_form('user_management_manage_single_organization_user_remove',
                         data={'org': self.unrelated_organization.pk},
                         reverse_kwargs={'args': [self.unrelated_organization_user.pk]},
                         require_status_code=404)

    def test_can_remove_self_from_organization(self):
        self.log_in_user(self.organization_user)
        self.submit_form('user_management_manage_single_organization_user_remove',
                         data={'org': self.organization.pk},
                         reverse_kwargs={'args': [self.organization_user.pk]},
                         success_url=reverse('create_link'))
        self.assertFalse(self.organization_user.organizations.filter(pk=self.organization.pk).exists())

    ### ADDING NEW USERS TO REGISTRARS ###

    def test_admin_user_can_add_new_user_to_registrar(self):
        address = 'doesnotexist@example.com'
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_registrar_user_add_user',
                          data={'a-registrar': self.registrar.pk,
                                'a-first_name': 'First',
                                'a-last_name': 'Last',
                                'a-email': address},
                          query_params={'email': address},
                          success_url=reverse('user_management_manage_registrar_user'),
                          success_query=LinkUser.objects.filter(email=address,
                                                                registrar=self.registrar).exists())

    def test_registrar_user_can_add_new_user_to_registrar(self):
        address = 'doesnotexist@example.com'
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.registrar.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': address},
                         query_params={'email': address},
                         success_url=reverse('user_management_manage_registrar_user'),
                         success_query=LinkUser.objects.filter(email=address,
                                                               registrar=self.registrar).exists())
        # Try to add the same person again; should fail
        response = self.submit_form('user_management_registrar_user_add_user',
                                     data={'a-registrar': self.registrar.pk,
                                           'a-first_name': 'First',
                                           'a-last_name': 'Last',
                                           'a-email': address},
                                     query_params={'email': address}).content
        self.assertIn("{} is already a registrar user for your registrar.".format(address), response)

    def test_registrar_user_cannot_add_new_user_to_inaccessible_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.unrelated_registrar.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         error_keys=['registrar'])
        self.assertFalse(LinkUser.objects.filter(email='doesnotexist@example.com',
                                                 registrar=self.unrelated_registrar).exists())

    ### ADDING EXISTING USERS TO REGISTRARS ###

    def test_admin_user_can_add_existing_user_to_registrar(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.registrar.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_registrar_user'),
                         success_query=LinkUser.objects.filter(pk=self.regular_user.pk, registrar=self.registrar))

    def test_registrar_user_can_add_existing_user_to_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.registrar.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_registrar_user'),
                         success_query=LinkUser.objects.filter(pk=self.regular_user.pk, registrar=self.registrar))

    def test_registrar_user_can_upgrade_org_user_to_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.registrar.pk},
                         query_params={'email': self.organization_user.email},
                         success_url=reverse('user_management_manage_registrar_user'),
                         success_query=LinkUser.objects.filter(pk=self.organization_user.pk, registrar=self.registrar))
        self.assertFalse(LinkUser.objects.filter(pk=self.organization_user.pk, organizations=self.organization).exists())

    def test_registrar_user_cannot_upgrade_unrelated_org_user_to_registrar(self):
        self.log_in_user(self.registrar_user)
        resp = self.submit_form('user_management_registrar_user_add_user',
                                data={'a-registrar': self.registrar.pk},
                                query_params={'email': self.unrelated_organization_user.email})
        self.assertIn("belongs to organizations that are not controlled by your registrar", resp.content)
        self.assertFalse(LinkUser.objects.filter(pk=self.unrelated_organization_user.pk, registrar=self.registrar).exists())

    def test_registrar_user_cannot_add_existing_user_to_inaccessible_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.unrelated_registrar.pk},
                         query_params={'email': self.regular_user.email},
                         error_keys=['registrar'])
        self.assertFalse(LinkUser.objects.filter(pk=self.regular_user.pk, registrar=self.unrelated_registrar).exists())

    def test_cannot_add_admin_user_to_registrar(self):
        self.log_in_user(self.registrar_user)
        resp = self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.registrar.pk},
                         query_params={'email': self.admin_user.email})
        self.assertIn("is an admin user", resp.content)
        self.assertFalse(LinkUser.objects.filter(pk=self.admin_user.pk, registrar=self.registrar).exists())

    def test_cannot_add_registrar_user_to_registrar(self):
        self.log_in_user(self.registrar_user)
        resp = self.submit_form('user_management_registrar_user_add_user',
                                data={'a-registrar': self.registrar.pk},
                                query_params={'email': self.unrelated_registrar_user.email})
        self.assertIn("is already a member of another registrar", resp.content)
        self.assertFalse(LinkUser.objects.filter(pk=self.unrelated_registrar_user.pk, registrar=self.registrar).exists())

    ### REMOVING USERS FROM REGISTRARS ###

    def test_can_remove_user_from_registrar(self):
        self.log_in_user(self.registrar_user)
        self.regular_user.registrar = self.registrar
        self.regular_user.save()
        self.submit_form('user_management_manage_single_registrar_user_remove',
                         reverse_kwargs={'args': [self.regular_user.pk]},
                         success_url=reverse('user_management_manage_registrar_user'))
        self.assertFalse(LinkUser.objects.filter(pk=self.regular_user.pk, registrar=self.registrar).exists())

    def test_registrar_cannot_remove_unrelated_user_from_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_manage_single_registrar_user_remove',
                         reverse_kwargs={'args': [self.unrelated_registrar_user.pk]},
                         require_status_code=404)

    def test_can_remove_self_from_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_manage_single_registrar_user_remove',
                         reverse_kwargs={'args': [self.registrar_user.pk]},
                         success_url=reverse('create_link'))
        self.assertFalse(LinkUser.objects.filter(pk=self.registrar_user.pk, registrar=self.registrar).exists())

    ### ADDING NEW USERS AS ADMINS ###

    def test_admin_user_can_add_new_user_as_admin(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_admin_user_add_user',
                         data={'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         success_url=reverse('user_management_manage_admin_user'),
                         success_query=LinkUser.objects.filter(email='doesnotexist@example.com',
                                                               is_staff=True).exists())
    ### ADDING EXISTING USERS AS ADMINS ###

    def test_admin_user_can_add_existing_user_as_admin(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_admin_user_add_user',
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_admin_user'),
                         success_query=LinkUser.objects.filter(pk=self.regular_user.pk, is_staff=True))

    ### REMOVING USERS AS ADMINS ###

    def test_can_remove_user_from_admin(self):
        self.log_in_user(self.admin_user)
        self.regular_user.is_staff = True
        self.regular_user.save()
        self.submit_form('user_management_manage_single_admin_user_remove',
                         reverse_kwargs={'args': [self.regular_user.pk]},
                         success_url=reverse('user_management_manage_admin_user'))
        self.assertFalse(LinkUser.objects.filter(pk=self.regular_user.pk, is_staff=True).exists())

    def test_can_remove_self_from_admin(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_manage_single_admin_user_remove',
                         reverse_kwargs={'args': [self.admin_user.pk]},
                         success_url=reverse('create_link'))
        self.assertFalse(LinkUser.objects.filter(pk=self.admin_user.pk, is_staff=True).exists())

    ### SETTINGS ###

    def test_user_can_change_own_settings(self):
        self.submit_form('user_management_settings_profile',
                         user=self.admin_user,
                         data={
                             'a-first_name': 'Newfirst',
                             'a-last_name': 'Newlast',
                             'a-email': 'test_admin_user@example.com'
                         },
                         success_url=reverse('user_management_settings_profile'),
                         success_query=LinkUser.objects.filter(first_name='Newfirst'))

    def test_edit_org_privacy(self):
        '''
            Can an authorized user change the privacy setting of an org?
        '''

        # Toggle as an org user
        response = self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                             user='test_org_user@example.com').content
        self.assertIn("Your Perma Links are currently <strong>Public</strong> by default.", response)
        self.submit_form('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                          user='test_org_user@example.com',
                          data={},
                          success_url=reverse('user_management_settings_affiliations'))
        response = self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                             user='test_org_user@example.com').content
        self.assertIn("Your Perma Links are currently <strong>Private</strong> by default.", response)

        # Toggle as a registrar user
        self.submit_form('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                  user='test_registrar_user@example.com',
                  data={},
                  success_url=reverse('user_management_manage_organization'))
        response = self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                             user='test_registrar_user@example.com').content
        self.assertIn("Your Perma Links are currently <strong>Public</strong> by default.", response)

        # Toggle as a staff user
        self.submit_form('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                  user='test_admin_user@example.com',
                  data={},
                  success_url=reverse('user_management_manage_organization'))
        response = self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                             user='test_admin_user@example.com').content
        self.assertIn("Your Perma Links are currently <strong>Private</strong> by default.", response)

        # As staff, try to access non-existent org
        self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[99999]},
                  user='test_admin_user@example.com',
                  require_status_code=404)


    # Subscription

    def test_unauthorized_user_cannot_see_subscription_page(self):
        u = LinkUser.objects.get(email='test_user@example.com')
        assert not u.can_view_subscription()
        self.get('user_management_settings_subscription',
                  user=u,
                  require_status_code=403)


    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_authorized_user_can_see_subscription_page(self, get_subscription):
        u = LinkUser.objects.get(email='registrar_user@firm.com')
        assert u.can_view_subscription()
        self.get('user_management_settings_subscription',
                  user=u,
                  require_status_code=200)


    @patch('perma.views.user_management.prep_for_perma_payments', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_subscribe_form_if_no_standing_subscription(self, get_subscription, prepped):
        u = LinkUser.objects.get(email='registrar_user@firm.com')
        get_subscription.return_value = None
        prepped.return_value = sentinel.prepped

        r = self.get('user_management_settings_subscription',
                      user=u)

        self.assertIn('Purchase a subscription', r.content)
        self.assertIn('<form class="upgrade-form', r.content)
        self.assertIn('<input type="hidden" name="encrypted_data"', r.content)
        self.assertIn(str(sentinel.prepped), r.content)
        get_subscription.assert_called_once_with(u.registrar)


    @patch('perma.views.user_management.prep_for_perma_payments', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_update_cancel_and_subscription_info_present_if_standing_subscription(self, get_subscription, prepped):
        u = LinkUser.objects.get(email='registrar_user@firm.com')
        subscription = spoof_current_monthly_subscription()
        get_subscription.return_value = subscription
        prepped.return_value = sentinel.prepped

        r = self.get('user_management_settings_subscription',
                      user=u)

        self.assertIn('Rate', r.content)
        self.assertIn('Next payment', r.content)
        self.assertIn(subscription['status'].lower(), r.content)
        self.assertIn('Update Payment Information', r.content)
        self.assertIn('<input type="hidden" name="encrypted_data"', r.content)
        self.assertIn(str(sentinel.prepped), r.content)
        self.assertIn('Cancel Subscription', r.content)
        get_subscription.assert_called_once_with(u.registrar)


    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_help_present_if_subscription_on_hold(self, get_subscription):
        u = LinkUser.objects.get(email='registrar_user@firm.com')
        subscription = spoof_on_hold_monthly_subscription()
        get_subscription.return_value = subscription

        r = self.get('user_management_settings_subscription',
                      user=u)

        self.assertIn('problem with your credit card', r.content)
        get_subscription.assert_called_once_with(u.registrar)


    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_cancellation_info_present_if_cancellation_requested(self, get_subscription):
        u = LinkUser.objects.get(email='registrar_user@firm.com')
        subscription = spoof_cancellation_requested_subscription()
        get_subscription.return_value = subscription

        r = self.get('user_management_settings_subscription',
                      user=u)

        self.assertNotIn('<input type="hidden" name="encrypted_data"', r.content)
        self.assertIn('received the request to cancel', r.content)
        get_subscription.assert_called_once_with(u.registrar)


    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_apology_page_displayed_if_perma_payments_is_down(self, get_subscription):
        u = LinkUser.objects.get(email='registrar_user@firm.com')
        get_subscription.side_effect = PermaPaymentsCommunicationException

        r = self.get('user_management_settings_subscription',
                      user=u)

        self.assertNotIn('<input type="hidden" name="encrypted_data"', r.content)
        self.assertIn('subscription information is currently unavailable', r.content)
        get_subscription.assert_called_once_with(u.registrar)


    def test_unauthorized_user_cannot_see_cancellation_page(self):
        u = LinkUser.objects.get(email='test_user@example.com')
        assert not u.can_view_subscription()
        self.get('user_management_settings_subscription_cancel',
                  user=u,
                  require_status_code=403)


    @patch('perma.views.user_management.prep_for_perma_payments', autospec=True)
    def test_authorized_user_cancellation_confirm_form(self, prepped):
        u = LinkUser.objects.get(email='registrar_user@firm.com')
        assert u.can_view_subscription()
        prepped.return_value = sentinel.prepped

        r = self.get('user_management_settings_subscription_cancel',
                      user=u)

        self.assertIn('<input type="hidden" name="encrypted_data"', r.content)
        self.assertIn(str(sentinel.prepped), r.content)
        self.assertIn('Are you sure you want to cancel', r.content)


    # Tools

    def test_api_key(self):
        response = self.get('user_management_settings_tools',
                             user='test_user@example.com').content
        self.assertNotIn('id="id_api_key"', response)
        self.submit_form('api_key_create',
                          user='test_user@example.com',
                          data={},
                          success_url=reverse('user_management_settings_tools'))
        response = self.get('user_management_settings_tools',
                             user='test_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        key = soup.find('input', {'id': 'id_api_key'})
        val = key.get('value', '')
        self.assertTrue(val)
        # do it again, and make sure the key changes
        self.submit_form('api_key_create',
                          user='test_user@example.com',
                          data={},
                          success_url=reverse('user_management_settings_tools'))
        response = self.get('user_management_settings_tools',
                             user='test_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        key = soup.find('input', {'id': 'id_api_key'})
        new_val = key.get('value', '')
        self.assertTrue(new_val)
        self.assertFalse(val == new_val)

    # Affiliations
    def test_affiliations(self):
        '''
            Does the expected information show up on the affliations page?
            (Tries not to be overly picky about the page design and markup.)
        '''
        # As an org user
        response = self.get('user_management_settings_affiliations',
                             user='multi_registrar_org_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        registrars = soup.select('h4 a')
        self.assertEqual(len(registrars), 2)
        for registrar in registrars:
            self.assertTrue(registrar.text.strip())
        orgs = soup.select('.settings-block p')
        self.assertEqual(len(orgs), 4)
        for org in orgs:
            self.assertTrue(org.text.strip())

        # As a registrar user
        response = self.get('user_management_settings_affiliations',
                             user='test_registrar_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        registrars = soup.select('h4')
        self.assertEqual(len(registrars), 1)
        for registrar in registrars:
            self.assertTrue(registrar.text.strip())
        settings = soup.select('dt')
        self.assertEqual(len(settings), 2)
        for setting in settings:
            self.assertTrue(org.text.strip())

        # As a pending registrar user
        response = self.get('user_management_settings_affiliations',
                             user='test_requested_registrar_account@example.com').content
        self.assertIn('Pending Registrar', response)
        self.assertIn('Thank you for requesting an account for your library. Perma.cc will review your request as soon as possible.', response)
        soup = BeautifulSoup(response, 'html.parser')
        registrars = soup.select('.sponsor-name')
        self.assertEqual(len(registrars), 1)
        for registrar in registrars:
            self.assertTrue(registrar.text.strip())
        settings = soup.select('dt')
        self.assertEqual(len(settings), 2)
        for setting in settings:
            self.assertTrue(org.text.strip())


    ###
    ### SIGNUP
    ###

    ### Libraries ###

    def new_lib(self):
        rand = random()
        return { 'email': u'library{}@university.org'.format(rand),
                 'name': u'University Library {}'.format(rand),
                 'website': u'http://website{}.org'.format(rand),
                 'address': u'{} Main St., Boston MA 02144'.format(rand)}

    def new_lib_user(self):
        rand = random()
        return { 'email': u'user{}@university.org'.format(rand),
                 'first': u'Joe',
                 'last': u'Yacobówski' }

    def check_library_labels(self, soup):
        name_label = soup.find('label', {'for': 'id_b-name'})
        self.assertEqual(name_label.text, "Library name")
        email_label = soup.find('label', {'for': 'id_b-email'})
        self.assertEqual(email_label.text, "Library email")
        website_label = soup.find('label', {'for': 'id_b-website'})
        self.assertEqual(website_label.text, "Library website")

    def check_lib_user_labels(self, soup):
        email_label = soup.find('label', {'for': 'id_a-email'})
        self.assertEqual(email_label.text, "Your email")

    def check_lib_email(self, message, new_lib, user):
        our_address = settings.DEFAULT_FROM_EMAIL

        self.assertIn(new_lib['name'], message.body)
        self.assertIn(new_lib['email'], message.body)

        self.assertIn(user['email'], message.body)

        id = Registrar.objects.get(email=new_lib['email']).id
        approve_url = "http://testserver{}".format(reverse('user_management_approve_pending_registrar', args=[id]))
        self.assertIn(approve_url, message.body)
        self.assertEqual(message.subject, "Perma.cc new library registrar account request")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': user['email']})

    def check_lib_user_email(self, message, new_lib_user):
        our_address = settings.DEFAULT_FROM_EMAIL

        confirmation_code = LinkUser.objects.get(email=new_lib_user['email']).confirmation_code
        confirm_url = "http://testserver{}".format(reverse('register_password', args=[confirmation_code]))
        self.assertIn(confirm_url, message.body)
        self.assertEqual(message.subject, "A Perma.cc account has been created for you")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [new_lib_user['email']])

    def test_new_library_render(self):
        '''
           Does the library signup form display as expected?
        '''

        # NOT LOGGED IN

        # Registrar and user forms are displayed,
        # inputs are blank, and labels are customized as expected
        response = self.get('libraries').content
        soup = BeautifulSoup(response, 'html.parser')
        self.check_library_labels(soup)
        self.check_lib_user_labels(soup)
        inputs = soup.select('input')
        self.assertEqual(len(inputs), 8)
        for input in inputs:
            if input['name'] == 'csrfmiddlewaretoken':
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))

        # If request_data is present in session, registrar form is prepopulated,
        # and labels are still customized as expected
        session = self.client.session
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        session['request_data'] = { u'b-email': new_lib['email'],
                                    u'b-website': new_lib['website'],
                                    u'b-name': new_lib['name'],
                                    u'b-address': new_lib['address'],
                                    u'a-email': new_lib_user['email'],
                                    u'a-first_name': new_lib_user['first'],
                                    u'a-last_name': new_lib_user['last'],
                                    u'csrfmiddlewaretoken': u'11YY3S2DgOw2DHoWVEbBArnBMdEA2svu' }
        session.save()
        response = self.get('libraries').content
        soup = BeautifulSoup(response, 'html.parser')
        self.check_library_labels(soup)
        self.check_lib_user_labels(soup)
        inputs = soup.select('input')
        self.assertEqual(len(inputs), 8)
        for input in inputs:
            if input['name'] == 'csrfmiddlewaretoken':
                self.assertTrue(input.get('value', ''))
            elif input['name'][:2] == "b-":
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))

        # If there's an unsuccessful submission, field labels are still as expected.
        response = self.post('libraries').content
        soup = BeautifulSoup(response, 'html.parser')
        self.check_library_labels(soup)
        self.check_lib_user_labels(soup)

        # LOGGED IN

        # Registrar form is displayed, but user form is not,
        # inputs are blank, and labels are still customized as expected
        response = self.get('libraries', user="test_user@example.com").content
        soup = BeautifulSoup(response, 'html.parser')
        self.check_library_labels(soup)
        inputs = soup.select('input')
        self.assertEqual(len(inputs), 6) # 6 because csrf is here and in the logout form
        for input in inputs:
            self.assertIn(input['name'],['csrfmiddlewaretoken', 'b-name', 'b-email', 'b-website', 'b-address'])
            if input['name'] == 'csrfmiddlewaretoken':
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))

    def test_new_library_submit_success(self):
        '''
           Does the library signup form submit as expected? Success cases.
        '''
        expected_emails_sent = 0

        # Not logged in, submit all fields sans first and last name
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        self.submit_form('libraries',
                          data = { u'b-email': new_lib['email'],
                                   u'b-website': new_lib['website'],
                                   u'b-name': new_lib['name'],
                                   u'a-email': new_lib_user['email'] },
                          success_url=reverse('register_library_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_lib_email(mail.outbox[expected_emails_sent - 2], new_lib, new_lib_user)
        self.check_lib_user_email(mail.outbox[expected_emails_sent - 1], new_lib_user)

        # Not logged in, submit all fields including first and last name
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        self.submit_form('libraries',
                          data = { u'b-email': new_lib['email'],
                                   u'b-website': new_lib['website'],
                                   u'b-name': new_lib['name'],
                                   u'a-email': new_lib_user['email'],
                                   u'a-first_name': new_lib_user['first'],
                                   u'a-last_name': new_lib_user['last']},
                          success_url=reverse('register_library_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_lib_email(mail.outbox[expected_emails_sent - 2], new_lib, new_lib_user)
        self.check_lib_user_email(mail.outbox[expected_emails_sent - 1], new_lib_user)

        # Logged in
        new_lib = self.new_lib()
        existing_lib_user = { 'email': 'test_user@example.com'}
        self.submit_form('libraries',
                          data = { u'b-email': new_lib['email'],
                                   u'b-website': new_lib['website'],
                                   u'b-name': new_lib['name'] },
                          success_url=reverse('user_management_settings_affiliations'),
                          user=existing_lib_user['email'])
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_lib_email(mail.outbox[expected_emails_sent - 1], new_lib, existing_lib_user)

    def test_new_library_submit_failure(self):
        '''
           Does the library signup form submit as expected? Failures.
        '''
        new_lib = self.new_lib()
        existing_lib_user = { 'email': 'test_user@example.com'}

        # Not logged in, blank submission reports correct fields required
        # ('email' catches both registrar and user email errors, unavoidably,
        # so test with just that missing separately)
        self.submit_form('libraries',
                          data = {},
                          form_keys = ['registrar_form', 'user_form'],
                          error_keys = ['website', 'name', 'email'])
        self.assertEqual(len(mail.outbox), 0)

        # (checking user email missing separately)
        self.submit_form('libraries',
                          data = {u'b-email': new_lib['email'],
                                  u'b-website': new_lib['website'],
                                  u'b-name': new_lib['name']},
                          form_keys = ['registrar_form', 'user_form'],
                          error_keys = ['email'])
        self.assertEqual(len(mail.outbox), 0)

        # Not logged in, user appears to have already registered
        data = {u'b-email': new_lib['email'],
                u'b-website': new_lib['website'],
                u'b-name': new_lib['name'],
                u'a-email': existing_lib_user['email']}
        self.submit_form('libraries',
                          data = data,
                          form_keys = ['registrar_form', 'user_form'],
                          success_url = '/login?next=/libraries/')
        self.assertDictEqual(self.client.session['request_data'], data)
        self.assertEqual(len(mail.outbox), 0)

        # Not logged in, registrar apepars to exist already
        # (actually, this doesn't currently fail)

        # Logged in, blank submission reports all fields required
        self.submit_form('libraries',
                          data = {},
                          user = existing_lib_user['email'],
                          error_keys = ['website', 'name', 'email'])
        self.assertEqual(len(mail.outbox), 0)

        # Logged in, registrar appears to exist already
        # (actually, this doesn't currently fail)

    ### Courts ###

    def new_court(self):
        rand = random()
        return { 'requested_account_note': u'Court {}'.format(rand) }

    def new_court_user(self):
        rand = random()
        return { 'email': u'user{}@university.org'.format(rand),
                 'first': u'Joe',
                 'last': u'Yacobówski' }

    def check_court_email(self, message, court_email):
        our_address = settings.DEFAULT_FROM_EMAIL

        # Doesn't check email contents yet; too many variations possible presently
        self.assertEqual(message.subject, "Perma.cc new library court account information request")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': court_email})

    def check_court_user_email(self, message, new_user):
        our_address = settings.DEFAULT_FROM_EMAIL

        confirmation_code = LinkUser.objects.get(email=new_user['email']).confirmation_code
        confirm_url = "http://testserver{}".format(reverse('register_password', args=[confirmation_code]))
        self.assertIn(confirm_url, message.body)
        self.assertEqual(message.subject, "A Perma.cc account has been created for you")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [new_user['email']])

    def test_new_court_success(self):
        '''
            Does the court signup form submit as expected? Success cases.
        '''
        new_court = self.new_court()
        new_user = self.new_court_user()
        existing_user = { 'email': 'test_user@example.com'}
        another_existing_user = { 'email': 'another_library_user@example.com'}
        expected_emails_sent = 0

        # NOT LOGGED IN

        # Existing user's email address, no court info
        # (currently succeeds, should probably fail; see issue 1746)
        self.submit_form('sign_up_courts',
                          data = { 'email': existing_user['email']},
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

        # Existing user's email address + court info
        self.submit_form('sign_up_courts',
                          data = { 'email': existing_user['email'],
                                   'requested_account_note': new_court['requested_account_note']},
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

        # New user email address, don't create account
        self.submit_form('sign_up_courts',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_court['requested_account_note']},
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

        # New user email address, create account
        self.submit_form('sign_up_courts',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True },
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_user_email(mail.outbox[expected_emails_sent - 2], new_user)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

        # LOGGED IN

        # New user email address
        # (This succeeds and creates a new account; see issue 1749)
        new_user = self.new_court_user()
        self.submit_form('sign_up_courts',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True },
                          user = existing_user['email'],
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_user_email(mail.outbox[expected_emails_sent - 2], new_user)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

        # Existing user's email address, not that of the user logged in.
        # (This is odd; see issue 1749)
        self.submit_form('sign_up_courts',
                          data = { 'email': existing_user['email'],
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True },
                          user = another_existing_user['email'],
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

    def test_new_court_failure(self):
        '''
            Does the court signup form submit as expected? Failure cases.
        '''
        # Not logged in, blank submission reports correct fields required
        self.submit_form('sign_up_courts',
                          data = {},
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)

        # Logged in, blank submission reports same fields required
        # (This is odd; see issue 1749)
        self.submit_form('sign_up_courts',
                          data = {},
                          user = 'test_user@example.com',
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)


    ### Firms ###

    def new_firm(self):
        rand = random()
        return {'requested_account_note': u'Firm {}'.format(rand)}

    def new_firm_user(self):
        rand = random()
        return {'email': u'user{}@university.org'.format(rand),
                'first': u'Joe',
                'last': u'Yacobówski'}

    def check_firm_email(self, message, firm_email):
        our_address = settings.DEFAULT_FROM_EMAIL

        # Doesn't check email contents yet; too many variations possible presently
        self.assertEqual(message.subject, "Perma.cc new law firm account information request")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': firm_email})

    def check_firm_user_email(self, message, new_user):
        our_address = settings.DEFAULT_FROM_EMAIL

        confirmation_code = LinkUser.objects.get(email=new_user['email']).confirmation_code
        confirm_url = "http://testserver{}".format(reverse('register_password', args=[confirmation_code]))
        self.assertIn(confirm_url, message.body)
        self.assertEqual(message.subject, "A Perma.cc account has been created for you")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [new_user['email']])

    def test_new_firm_success(self):
        '''
            Does the firm signup form submit as expected? Success cases.
        '''
        new_firm = self.new_firm()
        new_user = self.new_firm_user()
        existing_user = {'email': 'test_user@example.com'}
        another_existing_user = {'email': 'another_library_user@example.com'}
        expected_emails_sent = 0

        # NOT LOGGED IN

        # Existing user's email address, no court info
        # (currently succeeds, should probably fail; see issue 1746)
        self.submit_form('sign_up_firm',
                         data={'email': existing_user['email']},
                         success_url=reverse('firm_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

        # Existing user's email address + firm info
        self.submit_form('sign_up_firm',
                         data={'email': existing_user['email'],
                               'requested_account_note': new_firm['requested_account_note']},
                         success_url=reverse('firm_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

        # New user email address, don't create account
        self.submit_form('sign_up_firm',
                         data={'email': new_user['email'],
                               'requested_account_note': new_firm['requested_account_note']},
                         success_url=reverse('firm_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

        # New user email address, create account
        self.submit_form('sign_up_firm',
                         data={'email': new_user['email'],
                               'requested_account_note': new_firm['requested_account_note'],
                               'create_account': True},
                         success_url=reverse('register_email_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_firm_user_email(mail.outbox[expected_emails_sent - 2], new_user)
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

        # LOGGED IN

        # New user email address
        # (This succeeds and creates a new account; see issue 1749)
        new_user = self.new_firm_user()
        self.submit_form('sign_up_firm',
                         data={'email': new_user['email'],
                               'requested_account_note': new_firm['requested_account_note'],
                               'create_account': True},
                         user=existing_user['email'],
                         success_url=reverse('register_email_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_firm_user_email(mail.outbox[expected_emails_sent - 2], new_user)
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

        # Existing user's email address, not that of the user logged in.
        # (This is odd; see issue 1749)
        self.submit_form('sign_up_firm',
                         data={'email': existing_user['email'],
                               'requested_account_note': new_firm['requested_account_note'],
                               'create_account': True},
                         user=another_existing_user['email'],
                         success_url=reverse('firm_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

    def test_new_firm_failure(self):
        '''
            Does the firm signup form submit as expected? Failure cases.
        '''
        # Not logged in, blank submission reports correct fields required
        self.submit_form('sign_up_firm',
                         data={},
                         error_keys=['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)

        # Logged in, blank submission reports same fields required
        # (This is odd; see issue 1749)
        self.submit_form('sign_up_firm',
                         data={},
                         user='test_user@example.com',
                         error_keys=['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)

    ### Journals ###

    def new_journal(self):
        rand = random()
        return { 'requested_account_note': u'Journal {}'.format(rand)}

    def new_journal_user(self):
        rand = random()
        return { 'email': u'user{}@university.org'.format(rand),
                 'first': u'Joe',
                 'last': u'Yacobówski' }

    def check_journal_user_email(self, message, new_user_email):
        our_address = settings.DEFAULT_FROM_EMAIL

        confirmation_code = LinkUser.objects.get(email=new_user_email).confirmation_code
        confirm_url = "http://testserver{}".format(reverse('register_password', args=[confirmation_code]))
        self.assertIn(confirm_url, message.body)
        self.assertEqual(message.subject, "A Perma.cc account has been created for you")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [new_user_email])

    def test_new_journal_success(self):
        '''
            Does the journal signup form submit as expected? Success cases.
        '''
        new_journal = self.new_journal()
        new_user = self.new_journal_user()
        existing_user = {'email': 'test_user@example.com'}
        expected_emails_sent = 0

        # NOT LOGGED IN

        # New user email address + journal info
        self.submit_form('sign_up_journals',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_journal['requested_account_note']},
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_journal_user_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

        # LOGGED IN

        # New user email address + journal info
        # (This succeeds and creates a new account; see issue 1749)
        new_user = self.new_journal_user()
        self.submit_form('sign_up_journals',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_journal['requested_account_note']},
                          user = existing_user['email'],
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_journal_user_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

    def test_new_journal_failure(self):
        '''
            Does the journal signup form submit as expected? Failure cases.
        '''

        # NOT LOGGED IN

        # Blank submission reports correct fields required
        self.submit_form('sign_up_journals',
                          data = {},
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)

        # If email address already belongs to an account, validation fails
        self.submit_form('sign_up_journals',
                          data = { 'email': 'test_user@example.com',
                                   'requested_account_note': 'Here'},
                          error_keys = ['email'])
        self.assertEqual(len(mail.outbox), 0)

        # LOGGED IN
        # (This is odd; see issue 1749)

        # Blank submission reports correct fields required
        self.submit_form('sign_up_journals',
                          data = {},
                          user = 'test_user@example.com',
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)

        # If email address already belongs to an account, validation fails
        self.submit_form('sign_up_journals',
                          data = { 'email': 'test_user@example.com',
                                   'requested_account_note': 'Here'},
                          user = 'test_user@example.com',
                          error_keys = ['email'])
        self.assertEqual(len(mail.outbox), 0)


    ### Faculty ###

    def new_faculty_user(self):
        rand = random()
        return { 'email': u'user{}@university.org'.format(rand),
                 'first': u'Joe',
                 'last': u'Yacobówski',
                 'requested_account_note': u'Journal {}'.format(rand) }

    def check_faculty_user_email(self, message, new_user_email):
        our_address = settings.DEFAULT_FROM_EMAIL

        confirmation_code = LinkUser.objects.get(email=new_user_email).confirmation_code
        confirm_url = "http://testserver{}".format(reverse('register_password', args=[confirmation_code]))
        self.assertIn(confirm_url, message.body)
        self.assertEqual(message.subject, "A Perma.cc account has been created for you")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [new_user_email])

    def test_new_faculty_success(self):
        '''
            Does the faculty signup form submit as expected? Success cases.
        '''
        new_user = self.new_faculty_user()
        existing_user = {'email': 'test_user@example.com'}
        expected_emails_sent = 0

        # NOT LOGGED IN

        # New user email address + journal info
        self.submit_form('sign_up_faculty',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_user['requested_account_note']},
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_faculty_user_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

        # LOGGED IN

        # New user email address + journal info
        # (This succeeds and creates a new account; see issue 1749)
        new_user = self.new_faculty_user()
        self.submit_form('sign_up_faculty',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_user['requested_account_note']},
                          user = existing_user['email'],
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_faculty_user_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

    def test_new_faculty_failure(self):
        '''
            Does the faculty signup form submit as expected? Failure cases.
        '''

        # NOT LOGGED IN

        # Blank submission reports correct fields required
        self.submit_form('sign_up_faculty',
                          data = {},
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)

        # If email address already belongs to an account, validation fails
        self.submit_form('sign_up_faculty',
                          data = { 'email': 'test_user@example.com',
                                   'requested_account_note': 'Here'},
                          error_keys = ['email'])
        self.assertEqual(len(mail.outbox), 0)

        # LOGGED IN
        # (This is odd; see issue 1749)

        # Blank submission reports correct fields required
        self.submit_form('sign_up_faculty',
                          data = {},
                          user = 'test_user@example.com',
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)

        # If email address already belongs to an account, validation fails
        self.submit_form('sign_up_faculty',
                          data = { 'email': 'test_user@example.com',
                                   'requested_account_note': 'Here'},
                          user = 'test_user@example.com',
                          error_keys = ['email'])
        self.assertEqual(len(mail.outbox), 0)

    ### Individual Users ###

    def test_account_creation_views(self):
        # user registration
        new_user_email = "new_email@test.com"
        self.submit_form('sign_up', {'email': new_user_email, 'first_name': 'Test', 'last_name': 'Test'},
                         success_url=reverse('register_email_instructions'),
                         success_query=LinkUser.objects.filter(email=new_user_email))

        confirmation_code = LinkUser.objects.get(email=new_user_email).confirmation_code

        # reg confirm - form loads
        self.get('register_password',
                  reverse_kwargs={'args': [confirmation_code]})

        # reg confirm - non-matching passwords
        self.submit_form('register_password', reverse_kwargs={'args': [confirmation_code]},
                         data={'new_password1':'new-password1', 'new_password2':'new-password2'},
                         error_keys=['new_password2'])

        # reg confirm - correct
        self.submit_form('register_password', reverse_kwargs={'args': [confirmation_code]},
                         data={'new_password1': 'new-password1', 'new_password2': 'new-password1'},
                         success_url=reverse('user_management_limited_login'))

    def test_signup_with_existing_email_rejected(self):
        self.submit_form('sign_up',
                         {'email': self.registrar_user.email, 'first_name': 'Test', 'last_name': 'Test'},
                         error_keys=['email'])

    def test_registration_confirmation_with_bad_code_rejected(self):
        response = self.submit_form('register_password', reverse_kwargs={'args':['badconfirmationcode']})
        self.assertTrue('no_code' in response.context)


    def test_registration_confirmation_with_malformed_code_rejected(self):
        # malformed confirmation codes will 404
        with self.assertRaises(NoReverseMatch):
            self.submit_form('register_password', reverse_kwargs={'args':['bad_confirmation_code']})


    def check_new_activation_email(self, message, user_email):
        our_address = settings.DEFAULT_FROM_EMAIL

        confirmation_code = LinkUser.objects.get(email=user_email).confirmation_code
        confirm_url = "http://testserver{}".format(reverse('register_password', args=[confirmation_code]))
        self.assertIn(confirm_url, message.body)
        self.assertEqual(message.subject, "A Perma.cc account has been created for you")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [user_email])

    def test_get_new_activation_code(self):
        self.submit_form('user_management_not_active',
                          user = 'unactivated_faculty_user@example.com',
                          data = {},
                          success_url=reverse('user_management_limited_login'))
        self.assertEqual(len(mail.outbox), 1)
        self.check_new_activation_email(mail.outbox[0], 'unactivated_faculty_user@example.com')

    ### RESENDING ACTIVATION EMAILS ###

    def check_activation_resent(self, user, other_user):
        self.get('user_management_resend_activation',
                  reverse_kwargs={'args':[LinkUser.objects.get(email=other_user).id]},
                  user = user)
        self.assertEqual(len(mail.outbox), 1)
        self.check_new_activation_email(mail.outbox[0], other_user)

    def check_activation_not_resent(self, user, other_user):
        self.get('user_management_resend_activation',
                  reverse_kwargs={'args':[LinkUser.objects.get(email=other_user).id]},
                  user = user,
                  require_status_code = 403)
        self.assertEqual(len(mail.outbox), 0)

    # Registrar Users
    def test_registrar_can_resend_activation_to_org_user(self):
        self.check_activation_resent('test_registrar_user@example.com','test_org_user@example.com')

    def test_registrar_can_resend_activation_to_registrar_user(self):
        self.check_activation_resent('another_library_user@example.com','unactivated_registrar_user@example.com')

    def test_registrar_cannot_resend_activation_to_unrelated_org_user(self):
        self.check_activation_not_resent('test_registrar_user@example.com','test_yet_another_library_org_user@example.com')

    def test_registrar_cannot_resend_activation_to_regular_user(self):
        self.check_activation_not_resent('test_registrar_user@example.com','test_user@example.com')

    def test_registrar_cannot_resend_activation_to_unrelated_registrar_user(self):
        self.check_activation_not_resent('test_registrar_user@example.com','another_library_user@example.com')

    # Org Users
    def test_org_user_can_resend_activation_to_org_user(self):
        self.check_activation_resent('test_org_user@example.com','multi_registrar_org_user@example.com')

    def test_org_user_cannot_resend_activation_to_unrelated_org_user(self):
        self.check_activation_not_resent('test_org_user@example.com','test_yet_another_library_org_user@example.com')

    def test_org_user_cannot_resend_activation_to_regular_user(self):
        self.check_activation_not_resent('test_org_user@example.com','test_user@example.com')

    def test_org_user_cannot_resend_activation_to_registrar_user(self):
        self.check_activation_not_resent('test_org_user@example.com','test_registrar_user@example.com')

    # Admin Users
    def test_admin_can_resend_activation_to_regular_user(self):
        self.check_activation_resent('test_admin_user@example.com','test_user@example.com')

    def test_admin_can_resend_activation_to_org_user(self):
        self.check_activation_resent('test_admin_user@example.com','test_org_user@example.com')

    def test_admin_can_resend_activation_to_registrar_user(self):
        self.check_activation_resent('test_admin_user@example.com','test_registrar_user@example.com')

    ### ADMIN STATS ###

    def test_admin_stats(self):
        self.log_in_user(self.admin_user)
        self.get('user_management_stats', reverse_kwargs={'args':['days']})
        self.get('user_management_stats', reverse_kwargs={'args':['celery']})
        self.get('user_management_stats', reverse_kwargs={'args':['random']})
        self.get('user_management_stats', reverse_kwargs={'args':['emails']})
        self.get('user_management_stats', reverse_kwargs={'args':['job_queue']})
