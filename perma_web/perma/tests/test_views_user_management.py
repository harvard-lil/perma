# -*- coding: utf-8 -*-

import csv
from datetime import datetime, timezone as tz
from io import StringIO
import json
from mock import patch, sentinel
from random import random, getrandbits
import re

from bs4 import BeautifulSoup
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.core import mail
from django.conf import settings
from django.db import IntegrityError
from django.test import override_settings

from perma.exceptions import PermaPaymentsCommunicationException
from perma.models import LinkUser, Organization, Registrar, Sponsorship
from perma.tests.utils import PermaTestCase

# Fixtures

GENESIS = datetime.fromtimestamp(0).replace(tzinfo=tz.utc)

def spoof_current_monthly_subscription():
    return {
        "status": "Current",
        "rate": "10.00",
        "frequency": "monthly",
        "paid_through": GENESIS,
        "link_limit": 10
    }

def spoof_current_monthly_subscription_with_scheduled_downgrade():
    return {
        "status": "Current",
        "rate": "10.00",
        "frequency": "monthly",
        "paid_through": GENESIS,
        "link_limit": 10,
        "pending_change": {
            "rate": "1.00",
            "link_limit": 1,
            "effective": GENESIS.replace(year=9999)
        },
    }

def spoof_on_hold_monthly_subscription():
    return {
        "status": "Hold",
        "rate": "7777.77",
        "frequency": "monthly",
        "paid_through": GENESIS,
        "link_limit": 10
    }


def spoof_cancellation_requested_subscription():
    return {
        "status": "Cancellation Requested",
        "rate": "3333.33",
        "frequency": "monthly",
        "paid_through": GENESIS,
        "link_limit": 10
    }


# Tests

class UserManagementViewsTestCase(PermaTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = LinkUser.objects.get(pk=1)
        cls.registrar_user = LinkUser.objects.get(pk=2)
        cls.sponsored_user = LinkUser.objects.get(pk=20)
        cls.another_sponsored_user = LinkUser.objects.get(pk=21)
        cls.inactive_sponsored_user = LinkUser.objects.get(pk=22)
        cls.another_inactive_sponsored_user = LinkUser.objects.get(pk=23)
        cls.regular_user = LinkUser.objects.get(pk=4)
        cls.another_regular_user = LinkUser.objects.get(pk=16)
        cls.registrar = cls.registrar_user.registrar
        cls.pending_registrar = Registrar.objects.get(pk=2)
        cls.unrelated_registrar = Registrar.objects.get(pk=2)
        cls.unrelated_registrar_user = cls.unrelated_registrar.users.first()
        cls.organization = Organization.objects.get(pk=1)
        cls.organization_user = cls.organization.users.first()
        cls.another_organization = Organization.objects.get(pk=2)
        cls.unrelated_organization = cls.unrelated_registrar.organizations.first()
        cls.unrelated_organization_user = cls.unrelated_organization.users.first()
        cls.another_unrelated_organization_user = cls.unrelated_organization.users.get(pk=11)
        cls.deletable_organization = Organization.objects.get(pk=3)

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
        self.assertEqual(response.count(b'needs approval'), 1)

        # get just approved registrars
        response = self.get('user_management_manage_registrar',
                             user=self.admin_user,
                             request_kwargs={'data':{'status':'approved'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 registrars", count)
        self.assertEqual(response.count(b'needs approval'), 0)

        # get just pending registrars
        response = self.get('user_management_manage_registrar',
                             user=self.admin_user,
                             request_kwargs={'data': {'status': 'pending'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 registrar", count)
        self.assertEqual(response.count(b'needs approval'), 1)

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
        self.assertEqual(response.count(b'deactivated account'), 1)
        self.assertEqual(response.count(b'User must activate account'), 1)
        # registrar name appears by each user, and once in the filter dropdown
        self.assertEqual(response.count(b'Test Library'), 2)
        self.assertEqual(response.count(b'Another Library'), 4)
        self.assertEqual(response.count(b'Test Firm'), 2)

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
        self.assertEqual(response.count(b'deactivated account'), 0)
        self.assertEqual(response.count(b'User must activate account'), 0)
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'status': 'deactivated'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count(b'deactivated account'), 1)
        self.assertEqual(response.count(b'User must activate account'), 0)
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'status': 'unactivated'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count(b'deactivated account'), 0)
        self.assertEqual(response.count(b'User must activate account'), 1)

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
                 require_status_code=403)

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
        self.assertEqual(response.count(b'Test Library'), 3 + 2)
        self.assertEqual(response.count(b'Test Firm'), 2 + 2)
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
        self.assertEqual(response.count(b'Test Journal'), 3 + 1)
        self.assertEqual(response.count(b'Another Journal'), 1 + 1)
        self.assertEqual(response.count(b"A Third Journal"), 3 + 1)
        self.assertEqual(response.count(b"Another Library&#x27;s Journal"), 3 + 1)
        self.assertEqual(response.count(b"Some Case"), 1 + 1)

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

    def test_org_export_user_list(self):
        expected_results = {
            # Org ID: (record count, org name)
            1: (3, 'Test Journal'),
            2: (1, 'Another Journal'),
            3: (3, 'A Third Journal'),
            4: (3, "Another Library's Journal"),
            5: (1, 'Some Case'),
            6: (0, 'Some Other Case'),
        }
        for org_id, (record_count, org_name) in expected_results.items():
            # Get CSV export output
            csv_response: HttpResponse = self.get(
                'user_management_manage_single_organization_export_user_list',
                request_kwargs={'data': {'format': 'csv'}},
                reverse_kwargs={'args': [org_id]},
                user=self.admin_user,
            )
            self.assertEqual(csv_response.headers['Content-Type'], 'text/csv')

            # Validate CSV output against expected results
            csv_file = StringIO(csv_response.content.decode('utf8'))
            reader = csv.DictReader(csv_file)
            reader_record_count = 0
            for record in reader:
                self.assertEqual(record['organization_name'], org_name)
                reader_record_count += 1
            self.assertEqual(reader_record_count, record_count)

            # Get JSON export output
            json_response: JsonResponse = self.get(
                'user_management_manage_single_organization_export_user_list',
                request_kwargs={'data': {'format': 'json'}},
                reverse_kwargs={'args': [org_id]},
                user=self.admin_user,
            )
            self.assertEqual(json_response.headers['Content-Type'], 'application/json')

            # Validate JSON output against expected results
            reader = json.loads(json_response.content)
            reader_record_count = 0
            for record in reader:
                self.assertEqual(record['organization_name'], org_name)
                reader_record_count += 1
            self.assertEqual(reader_record_count, record_count)

    def test_sponsored_user_export_user_list(self):
        expected_results = [
            ('another_inactive_sponsored_user@example.com', 'inactive'),
            ('another_sponsored_user@example.com', 'active'),
            ('inactive_sponsored_user@example.com', 'inactive'),
            ('test_sponsored_user@example.com', 'active'),
        ]

        # Get CSV export output
        csv_response: HttpResponse = self.get(
            'user_management_manage_sponsored_user_export_user_list',
            request_kwargs={'data': {'format': 'csv'}},
            user=self.admin_user,
        )
        self.assertEqual(csv_response.headers['Content-Type'], 'text/csv')

        # Validate CSV output against expected results
        csv_file = StringIO(csv_response.content.decode('utf8'))
        reader = csv.DictReader(csv_file)
        for index, record in enumerate(reader):
            expected_email, expected_sponsorship_status = expected_results[index]
            self.assertEqual(record['email'], expected_email)
            self.assertEqual(record['sponsorship_status'], expected_sponsorship_status)
        self.assertEqual(index + 1, len(expected_results))

        # Get JSON export output
        json_response: HttpResponse = self.get(
            'user_management_manage_sponsored_user_export_user_list',
            request_kwargs={'data': {'format': 'json'}},
            user=self.admin_user,
        )
        self.assertEqual(json_response.headers['Content-Type'], 'application/json')

        # Validate JSON output against expected results
        reader = json.loads(json_response.content)
        for index, record in enumerate(reader):
            expected_email, expected_sponsorship_status = expected_results[index]
            self.assertEqual(record['email'], expected_email)
            self.assertEqual(record['sponsorship_status'], expected_sponsorship_status)
        self.assertEqual(index + 1, len(expected_results))

    def test_sponsored_user_list_filters(self):
        # test assumptions: four users, with five sponsorships between them
        # - two users with active sponsorships, two users with inactive sponsorships
        # - two sponsored by Test Library, two from Another Library, one from A Third Library
        response = self.get('user_management_manage_sponsored_user',
                             user=self.admin_user).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 4 users", count)
        self.assertEqual(response.count(b'(inactive sponsorship)'), 2)
        # registrar name appears by each user, and once in the filter dropdown
        self.assertEqual(response.count(b'Test Library'), 3)
        self.assertEqual(response.count(b'Another Library'), 3)
        self.assertEqual(response.count(b'A Third Library'), 2)

        # filter by registrar
        response = self.get('user_management_manage_sponsored_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 1}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 2 users", count)
        response = self.get('user_management_manage_sponsored_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 2}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 2 users", count)
        response = self.get('user_management_manage_sponsored_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 3}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)

        # filter by sponsorship status
        response = self.get('user_management_manage_sponsored_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'sponsorship_status': 'active'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 2 users", count)
        response = self.get('user_management_manage_sponsored_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'sponsorship_status': 'inactive'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 2 users", count)

        # user status filter tested in test_registrar_user_list_filters



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
                 require_status_code=403)

    def test_org_user_cannot_update_unrelated_organization(self):
        self.get('user_management_manage_single_organization',
                 user=self.organization_user,
                 reverse_kwargs={'args': [self.unrelated_organization.pk]},
                 require_status_code=403)

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
        # test assumptions: nine users
        # - one aspiring court user, faculty user, journal user
        response = self.get('user_management_manage_user',
                             user=self.admin_user).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 9 users", count)
        self.assertEqual(response.count(b'Interested in a court account'), 1)
        self.assertEqual(response.count(b'Interested in a journal account'), 1)
        self.assertEqual(response.count(b'Interested in a faculty account'), 1)

        # filter by requested_account_type ("upgrade")
        response = self.get('user_management_manage_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'upgrade': 'court'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count(b'Interested in a court account'), 1)
        self.assertEqual(response.count(b'Interested in a journal account'), 0)
        self.assertEqual(response.count(b'Interested in a faculty account'), 0)
        response = self.get('user_management_manage_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'upgrade': 'journal'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count(b'Interested in a court account'), 0)
        self.assertEqual(response.count(b'Interested in a journal account'), 1)
        self.assertEqual(response.count(b'Interested in a faculty account'), 0)
        response = self.get('user_management_manage_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'upgrade': 'faculty'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count(b'Interested in a court account'), 0)
        self.assertEqual(response.count(b'Interested in a journal account'), 0)
        self.assertEqual(response.count(b'Interested in a faculty account'), 1)

        # status filter tested in test_registrar_user_list_filters

    def test_create_and_delete_user(self):
        self.log_in_user(self.admin_user)

        base_user = {
            'a-first_name':'First',
            'a-last_name':'Last',
        }
        email = self.randomize_capitalization('test_views_test@test.com')
        normalized_email = email.lower()

        for view_name, form_extras in [
            ['registrar_user', {'a-registrar': 1}],
            ['user', {}],
            ['organization_user', {'a-organizations': 1}],
            ['sponsored_user', {'a-sponsoring_registrars': 1}],
        ]:
            # create user
            email += '1'
            normalized_email += '1'
            self.submit_form('user_management_' + view_name + '_add_user',
                           data=dict(list(base_user.items()) + list(form_extras.items()) + [['a-e-address', email]]),
                           success_url=reverse('user_management_manage_' + view_name),
                           success_query=LinkUser.objects.filter(email=normalized_email, raw_email=email))
            new_user = LinkUser.objects.get(email=normalized_email)

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

    def add_org_user(self):
        email = self.randomize_capitalization('doesnotexist@example.com')
        normalized_email = email.lower()
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-e-address': email},
                         query_params={'email': email},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=LinkUser.objects.filter(
                             email=normalized_email,
                             raw_email=email,
                             organizations=self.organization
                         ).exists())

    def test_admin_user_can_add_new_user_to_org(self):
        self.log_in_user(self.admin_user)
        self.add_org_user()

    def test_registrar_user_can_add_new_user_to_org(self):
        self.log_in_user(self.registrar_user)
        self.add_org_user()

    def test_org_user_can_add_new_user_to_org(self):
        self.log_in_user(self.organization_user)
        self.add_org_user()

    def test_registrar_user_cannot_add_new_user_to_inaccessible_org(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.unrelated_organization.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-e-address': 'doesnotexist@example.com'},
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
                               'a-e-address': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         error_keys=['organizations'])
        self.assertFalse(LinkUser.objects.filter(email='doesnotexist@example.com',
                                                 organizations=self.unrelated_organization).exists())

    ### ADDING EXISTING USERS TO ORGANIZATIONS ###

    def add_org_users(self):
        # submit email with the same capitalization
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=self.regular_user.organizations.filter(pk=self.organization.pk))

        # submit email with a different capitalization
        scrambled_email = self.randomize_capitalization(self.another_regular_user.email)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': scrambled_email},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=self.another_regular_user.organizations.filter(pk=self.organization.pk))

    def test_admin_user_can_add_existing_user_to_org(self):
        self.log_in_user(self.admin_user)
        self.add_org_users()

    def test_registrar_user_can_add_existing_user_to_org(self):
        self.log_in_user(self.registrar_user)
        self.add_org_users()

    def test_org_user_can_add_existing_user_to_org(self):
        self.log_in_user(self.organization_user)
        self.add_org_users()

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
        self.assertIn(b"is an admin user", resp.content)
        self.assertFalse(self.admin_user.organizations.exists())

    def test_cannot_add_registrar_user_to_org(self):
        self.log_in_user(self.organization_user)
        resp = self.submit_form('user_management_organization_user_add_user',
                                data={'a-organizations': self.organization.pk},
                                query_params={'email': self.registrar_user.email})
        self.assertIn(b"is already a registrar user", resp.content)
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
                  require_status_code=403)
        # Repeat with the other registrar, to confirm we're
        # getting 404s because of permission reasons, not because the
        # test fixtures are broken.
        self.log_in_user(self.unrelated_registrar_user)
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.organization_user.pk]},
                  require_status_code=403)
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
                  require_status_code=403)

        # Repeat with another org
        self.log_in_user(org_two_users[1])
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.pk_from_email(org_one_users[1])]},
                  require_status_code=403)
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

    ### ADDING NEW USERS TO REGISTRARS AS SPONSORED USERS ###

    def test_admin_user_can_add_new_sponsored_user_to_registrar(self):
        address = self.randomize_capitalization('doesnotexist@example.com')
        normalized_address = address.lower()
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_sponsored_user_add_user',
                          data={'a-sponsoring_registrars': self.registrar.pk,
                                'a-first_name': 'First',
                                'a-last_name': 'Last',
                                'a-e-address': address},
                          query_params={'email': address},
                          success_url=reverse('user_management_manage_sponsored_user'))

        # Check that everything is set up correctly (we'll do this once, here, and not repeat in other tests)
        user = LinkUser.objects.get(
            email=normalized_address,
            raw_email=address,
            sponsoring_registrars=self.registrar
        )
        sponsorship = user.sponsorships.first()
        sponsored_folder = sponsorship.folders.get()
        self.assertEqual(sponsorship.status, 'active')
        self.assertEqual(sponsored_folder.parent, user.sponsored_root_folder)
        self.assertFalse(sponsored_folder.read_only)

        # Try to add the same person again; should fail
        scrambled_email = self.randomize_capitalization(address)
        response = self.submit_form('user_management_sponsored_user_add_user',
                                     data={'a-sponsoring_registrars': self.registrar.pk,
                                           'a-first_name': 'First',
                                           'a-last_name': 'Last',
                                           'a-e-address': scrambled_email},
                                     query_params={'email': scrambled_email}).content
        self.assertIn(bytes("Select a valid choice. That choice is not one of the available choices", 'utf-8'), response)

    def test_registrar_user_can_add_new_sponsored_user_to_registrar(self):
        address = self.randomize_capitalization('doesnotexist@example.com')
        normalized_address = address.lower()
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_sponsored_user_add_user',
                         data={'a-sponsoring_registrars': self.registrar.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-e-address': address},
                         query_params={'email': address},
                         success_url=reverse('user_management_manage_sponsored_user'),
                         success_query=LinkUser.objects.filter(
                             email=normalized_address,
                             raw_email=address,
                             sponsoring_registrars=self.registrar
                         ).exists())

        # Try to add the same person again; should fail
        scrambled_email = self.randomize_capitalization(address)
        response = self.submit_form('user_management_sponsored_user_add_user',
                                     data={'a-sponsoring_registrars': self.registrar.pk,
                                           'a-first_name': 'First',
                                           'a-last_name': 'Last',
                                           'a-e-address': scrambled_email},
                                     query_params={'email': scrambled_email}).content
        self.assertIn(bytes("{} is already sponsored by your registrar.".format(normalized_address), 'utf-8'), response)

    def test_registrar_user_cannot_add_sponsored_user_to_inaccessible_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_sponsored_user_add_user',
                         data={'a-sponsoring_registrars': self.unrelated_registrar.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-e-address': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         error_keys=['sponsoring_registrars'])
        self.assertFalse(LinkUser.objects.filter(email='doesnotexist@example.com',
                                                 sponsoring_registrars=self.unrelated_registrar).exists())

    ### ADDING EXISTING USERS TO REGISTRARS AS SPONSORED USERS ###

    def test_admin_user_can_add_sponsorship_to_existing_user(self):
        self.log_in_user(self.admin_user)
        scrambled_email = self.randomize_capitalization(self.regular_user.email)
        self.submit_form('user_management_sponsored_user_add_user',
                         data={'a-sponsoring_registrars': self.registrar.pk},
                         query_params={'email': scrambled_email},
                         success_url=reverse('user_management_manage_sponsored_user'),
                         success_query=LinkUser.objects.filter(pk=self.regular_user.pk, sponsoring_registrars=self.registrar))

    def test_registrar_user_can_add_sponsorship_to_existing_user(self):
        self.log_in_user(self.registrar_user)
        scrambled_email = self.randomize_capitalization(self.regular_user.email)
        self.submit_form('user_management_sponsored_user_add_user',
                         data={'a-sponsoring_registrars': self.registrar.pk},
                         query_params={'email': scrambled_email},
                         success_url=reverse('user_management_manage_sponsored_user'),
                         success_query=LinkUser.objects.filter(pk=self.regular_user.pk, sponsoring_registrars=self.registrar))

    def test_registrar_user_cannot_add_sponsorship_for_other_registrar_to_existing_user(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_sponsored_user_add_user',
                         data={'a-sponsoring_registrars': self.unrelated_registrar.pk},
                         query_params={'email': self.regular_user.email},
                         error_keys=['sponsoring_registrars'])
        self.assertFalse(LinkUser.objects.filter(pk=self.regular_user.pk, sponsoring_registrars=self.unrelated_registrar).exists())

    ### TOGGLING THE STATUS OF SPONSORSHIPS ###

    def test_admin_user_can_deactivate_active_sponsorship(self):
        sponsorship = Sponsorship.objects.get(user=self.sponsored_user, registrar=self.registrar, status='active')
        self.assertTrue(all(not folder.read_only for folder in sponsorship.folders))
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_manage_single_sponsored_user_remove',
                         reverse_kwargs={'args': [self.sponsored_user.id, self.registrar.id]},
                         success_url=reverse('user_management_manage_single_sponsored_user', args=[self.sponsored_user.id]))
        sponsorship.refresh_from_db()
        self.assertEqual(sponsorship.status, 'inactive')
        self.assertTrue(all(folder.read_only for folder in sponsorship.folders))


    def test_admin_user_can_reactivate_inactive_sponsorship(self):
        sponsorship = Sponsorship.objects.get(user=self.inactive_sponsored_user, registrar=self.registrar, status='inactive')
        self.assertTrue(all(folder.read_only for folder in sponsorship.folders))
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_manage_single_sponsored_user_readd',
                         reverse_kwargs={'args': [self.inactive_sponsored_user.id, self.registrar.id]},
                         success_url=reverse('user_management_manage_single_sponsored_user', args=[self.inactive_sponsored_user.id]))
        sponsorship.refresh_from_db()
        self.assertEqual(sponsorship.status, 'active')
        self.assertTrue(all(not folder.read_only for folder in sponsorship.folders))

    def test_registrar_user_can_deactivate_active_sponsorship(self):
        sponsorship = Sponsorship.objects.get(user=self.sponsored_user, registrar=self.registrar, status='active')
        self.assertTrue(all(not folder.read_only for folder in sponsorship.folders))
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_manage_single_sponsored_user_remove',
                         reverse_kwargs={'args': [self.sponsored_user.id, self.registrar.id]},
                         success_url=reverse('user_management_manage_single_sponsored_user', args=[self.sponsored_user.id]))
        sponsorship.refresh_from_db()
        self.assertEqual(sponsorship.status, 'inactive')
        self.assertTrue(all(folder.read_only for folder in sponsorship.folders))

    def test_registrar_user_cannot_deactivate_active_sponsorship_for_other_registrar(self):
        self.assertTrue(self.unrelated_registrar in self.another_sponsored_user.sponsoring_registrars.all())
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_manage_single_sponsored_user_remove',
                         reverse_kwargs={'args': [self.another_sponsored_user.id, self.unrelated_registrar.id]},
                         require_status_code=404)

    def test_registrar_user_can_reactivate_inactive_sponsorship(self):
        sponsorship = Sponsorship.objects.get(user=self.inactive_sponsored_user, registrar=self.registrar, status='inactive')
        self.assertTrue(all(folder.read_only for folder in sponsorship.folders))
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_manage_single_sponsored_user_readd',
                         reverse_kwargs={'args': [self.inactive_sponsored_user.id, self.registrar.id]},
                         success_url=reverse('user_management_manage_single_sponsored_user', args=[self.inactive_sponsored_user.id]))
        sponsorship.refresh_from_db()
        self.assertEqual(sponsorship.status, 'active')
        self.assertTrue(all(not folder.read_only for folder in sponsorship.folders))

    def test_registrar_user_cannot_reactivate_inactive_sponsorship_for_other_registrar(self):
        sponsorship = Sponsorship.objects.get(user=self.another_inactive_sponsored_user, registrar=self.unrelated_registrar, status='inactive')
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_manage_single_sponsored_user_readd',
                         reverse_kwargs={'args': [self.another_inactive_sponsored_user.id, self.unrelated_registrar.id]},
                         require_status_code=404)
        sponsorship.refresh_from_db()
        self.assertEqual(sponsorship.status, 'inactive')

    ### ADDING NEW USERS TO REGISTRARS AS REGISTRAR USERS) ###

    def test_admin_user_can_add_new_user_to_registrar(self):
        address = self.randomize_capitalization('doesnotexist@example.com')
        normalized_address = address.lower()
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_registrar_user_add_user',
                          data={'a-registrar': self.registrar.pk,
                                'a-first_name': 'First',
                                'a-last_name': 'Last',
                                'a-e-address': address},
                          query_params={'email': address},
                          success_url=reverse('user_management_manage_registrar_user'),
                          success_query=LinkUser.objects.filter(
                              email=normalized_address,
                              raw_email=address,
                              registrar=self.registrar).exists()
                         )

    def test_registrar_user_can_add_new_user_to_registrar(self):
        address = self.randomize_capitalization('doesnotexist@example.com')
        normalized_address = address.lower()
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.registrar.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-e-address': address},
                         query_params={'email': address},
                         success_url=reverse('user_management_manage_registrar_user'),
                         success_query=LinkUser.objects.filter(
                             email=normalized_address,
                             raw_email=address,
                             registrar=self.registrar).exists()
                         )

        # Try to add the same person again; should fail
        scrambled_email = self.randomize_capitalization(address)
        response = self.submit_form('user_management_registrar_user_add_user',
                                     data={'a-registrar': self.registrar.pk,
                                           'a-first_name': 'First',
                                           'a-last_name': 'Last',
                                           'a-e-address': scrambled_email},
                                     query_params={'email': scrambled_email}).content
        self.assertIn(bytes("{} is already a registrar user for your registrar.".format(normalized_address), 'utf-8'), response)

    def test_registrar_user_cannot_add_new_user_to_inaccessible_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.unrelated_registrar.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-e-address': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         error_keys=['registrar'])
        self.assertFalse(LinkUser.objects.filter(email='doesnotexist@example.com',
                                                 registrar=self.unrelated_registrar).exists())

    ### ADDING EXISTING USERS TO REGISTRARS ###

    def add_registrars(self):
        # submit email with the same capitalization
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.registrar.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_registrar_user'),
                         success_query=LinkUser.objects.filter(pk=self.regular_user.pk, registrar=self.registrar))

        # submit email with a different capitalization
        scrambled_email = self.randomize_capitalization(self.another_regular_user.email)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.registrar.pk},
                         query_params={'email': scrambled_email},
                         success_url=reverse('user_management_manage_registrar_user'),
                         success_query=LinkUser.objects.filter(pk=self.another_regular_user.pk, registrar=self.registrar))

    def test_admin_user_can_add_existing_user_to_registrar(self):
        self.log_in_user(self.admin_user)
        self.add_registrars()

    def test_registrar_user_can_add_existing_user_to_registrar(self):
        self.log_in_user(self.registrar_user)
        self.add_registrars()

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
        self.assertIn(b"belongs to organizations that are not controlled by your registrar", resp.content)
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
        self.assertIn(b"is an admin user", resp.content)
        self.assertFalse(LinkUser.objects.filter(pk=self.admin_user.pk, registrar=self.registrar).exists())

    def test_cannot_add_registrar_user_to_registrar(self):
        self.log_in_user(self.registrar_user)
        resp = self.submit_form('user_management_registrar_user_add_user',
                                data={'a-registrar': self.registrar.pk},
                                query_params={'email': self.unrelated_registrar_user.email})
        self.assertIn(b"is already a member of another registrar", resp.content)
        self.assertFalse(LinkUser.objects.filter(pk=self.unrelated_registrar_user.pk, registrar=self.registrar).exists())

    ### REMOVING REGISTRAR USERS FROM REGISTRARS ###

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
        address = self.randomize_capitalization('doesnotexist@example.com')
        normalized_address = address.lower()
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_admin_user_add_user',
                         data={'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-e-address': address},
                         query_params={'email': address},
                         success_url=reverse('user_management_manage_admin_user'),
                         success_query=LinkUser.objects.filter(
                             email=normalized_address,
                             raw_email=address,
                             is_staff=True).exists()
                         )

    ### ADDING EXISTING USERS AS ADMINS ###

    def test_admin_user_can_add_existing_user_as_admin(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_admin_user_add_user',
                         query_params={'email': self.randomize_capitalization(self.regular_user.email)},
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
        response = self.submit_form('user_management_settings_profile',
                                     user=self.admin_user,
                                     data={
                                         'a-first_name': 'Newfirst',
                                         'a-last_name': 'Newlast',
                                         'a-email': 'test_admin_user@example.com'
                                     },
                                     request_kwargs={"follow": True},
                                     success_query=LinkUser.objects.filter(first_name='Newfirst'))
        self.assertIn(bytes('Profile saved!', 'utf-8'), response.content)

    def test_user_can_request_deletion_once(self):
        deletion_url = reverse('user_management_delete_account')
        self.assertNotIn('Requested account deletion', self.regular_user.notes)
        response1 = self.get('user_management_settings_profile',
                             user=self.regular_user).content
        self.assertIn(bytes('<form method="post" action="{}"'.format(deletion_url), 'utf-8'), response1)
        response2 = self.post('user_management_delete_account',
                             user=self.regular_user,
                             request_kwargs={"follow": True}).content
        self.assertNotIn(bytes('<form method="post" action="{}"'.format(deletion_url), 'utf-8'), response2)
        self.assertIn(b'Deletion Request Received', response2)
        self.regular_user.refresh_from_db()
        self.assertIn('Requested account deletion', self.regular_user.notes)
        self.assertEqual(len(mail.outbox),1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'Perma.cc account deletion request')

    def test_edit_org_privacy(self):
        '''
            Can an authorized user change the privacy setting of an org?
        '''

        # Toggle as an org user
        response = self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                             user='test_org_user@example.com').content
        self.assertIn(b"Your Perma Links are currently <strong>Public</strong> by default.", response)
        self.submit_form('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                          user='test_org_user@example.com',
                          data={},
                          success_url=reverse('user_management_settings_affiliations'))
        response = self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                             user='test_org_user@example.com').content
        self.assertIn(b"Your Perma Links are currently <strong>Private</strong> by default.", response)

        # Toggle as a registrar user
        self.submit_form('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                  user='test_registrar_user@example.com',
                  data={},
                  success_url=reverse('user_management_manage_organization'))
        response = self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                             user='test_registrar_user@example.com').content
        self.assertIn(b"Your Perma Links are currently <strong>Public</strong> by default.", response)

        # Toggle as a staff user
        self.submit_form('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                  user='test_admin_user@example.com',
                  data={},
                  success_url=reverse('user_management_manage_organization'))
        response = self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                             user='test_admin_user@example.com').content
        self.assertIn(b"Your Perma Links are currently <strong>Private</strong> by default.", response)

        # As staff, try to access non-existent org
        self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[99999]},
                  user='test_admin_user@example.com',
                  require_status_code=404)


    # Subscription, Individuals (except registrar users)

    def test_nonpaying_user_cannot_see_usage_plan_page(self):
        u = LinkUser.objects.get(email='test_nonpaying_user@example.com')
        assert not u.can_view_usage_plan()
        self.get('user_management_settings_usage_plan',
                  user=u,
                  require_status_code=403)

    def test_regular_user_can_see_usage_plan_page(self):
        u = LinkUser.objects.get(email='test_user@example.com')
        assert u.can_view_usage_plan()
        self.get('user_management_settings_usage_plan',
                  user=u,
                  require_status_code=200)


    @patch('perma.models.prep_for_perma_payments', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_purchase_history', autospec=True)
    def test_no_purchase_history_section_if_no_one_time_purchases(self, get_purchase_history, get_subscription, prepped):
        u = LinkUser.objects.get(email='test_user@example.com')
        get_subscription.return_value = None
        get_purchase_history.return_value = {'purchases': [], 'total_links': 0}
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.get('user_management_settings_usage_plan',
                      user=u)

        self.assertNotIn(b'Purchase History', r.content)
        get_subscription.assert_called_once_with(u)
        get_purchase_history.assert_called_once_with(u)


    @patch('perma.models.prep_for_perma_payments', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_purchase_history', autospec=True)
    def test_purchase_history_present_if_one_time_purchases(self, get_purchase_history, get_subscription, prepped):
        u = LinkUser.objects.get(email='test_user@example.com')
        get_subscription.return_value = None
        get_purchase_history.return_value = {
            'purchases': [
                {'link_quantity': 10, 'date': GENESIS},
                {'link_quantity': 3, 'date': GENESIS}
            ],
            'total_links': 13
        }
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.get('user_management_settings_usage_plan',
                      user=u)

        self.assertIn(b'Purchase History', r.content)
        self.assertIn(b'10 Links', r.content)
        self.assertIn(b'3 Links', r.content)
        self.assertIn(b'13 Links', r.content)
        self.assertIn(b'January 1, 1970', r.content)
        get_subscription.assert_called_once_with(u)
        get_purchase_history.assert_called_once_with(u)


    @patch('perma.models.prep_for_perma_payments', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_purchase_history', autospec=True)
    def test_subscribe_form_if_no_standing_subscription(self, get_purchase_history, get_subscription, prepped):
        u = LinkUser.objects.get(email='test_user@example.com')
        get_subscription.return_value = None
        get_purchase_history.return_value = {'purchases': [], 'total_links': 0}
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.get('user_management_settings_usage_plan',
                      user=u)

        individual_tier_count = len(settings.TIERS['Individual'])
        bonus_package_count = len(settings.BONUS_PACKAGES)
        self.assertIn(b'Get More Personal Links', r.content)
        self.assertIn(b'Purchase a personal subscription', r.content)
        self.assertIn(b'<form class="purchase-form', r.content, bonus_package_count)
        self.assertIn(b'<form class="upgrade-form', r.content, individual_tier_count)
        self.assertIn(b'<input type="hidden" name="encrypted_data"', r.content, individual_tier_count + bonus_package_count)
        self.assertIn(prepped.return_value, r.content)
        get_subscription.assert_called_once_with(u)
        get_purchase_history.assert_called_once_with(u)

    @patch('perma.models.prep_for_perma_payments', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_purchase_history', autospec=True)
    def test_update_button_cancel_button_and_subscription_info_present_if_standing_subscription(self, get_purchase_history, get_subscription, prepped):
        u = LinkUser.objects.get(email='test_user@example.com')
        subscription = spoof_current_monthly_subscription()
        get_subscription.return_value = subscription
        get_purchase_history.return_value = {'purchases': [], 'total_links': 0}
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.get('user_management_settings_usage_plan',
                      user=u)

        self.assertIn(b'Rate', r.content)
        self.assertIn(b'Paid Through', r.content)
        self.assertIn(bytes(subscription['status'].lower(), 'utf-8'), r.content)
        self.assertIn(b'Modify Subscription', r.content)
        self.assertContains(r, '<input type="hidden" name="account_type"', 2)
        self.assertIn(b'Cancel Subscription', r.content)
        get_subscription.assert_called_once_with(u)
        get_purchase_history.assert_called_once_with(u)

    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_purchase_history', autospec=True)
    def test_help_present_if_subscription_on_hold(self, get_purchase_history, get_subscription):
        u = LinkUser.objects.get(email='test_user@example.com')
        subscription = spoof_on_hold_monthly_subscription()
        get_subscription.return_value = subscription
        get_purchase_history.return_value = {'purchases': [], 'total_links': 0}

        r = self.get('user_management_settings_usage_plan',
                      user=u)

        self.assertIn(b'problem with your credit card', r.content)
        get_subscription.assert_called_once_with(u)
        get_purchase_history.assert_called_once_with(u)

    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_purchase_history', autospec=True)
    def test_cancellation_info_present_if_cancellation_requested(self, get_purchase_history, get_subscription):
        u = LinkUser.objects.get(email='test_user@example.com')
        subscription = spoof_cancellation_requested_subscription()
        get_subscription.return_value = subscription
        get_purchase_history.return_value = {'purchases': [], 'total_links': 0}

        r = self.get('user_management_settings_usage_plan',
                      user=u)

        bonus_package_count = len(settings.BONUS_PACKAGES)
        self.assertIn(b'Get More Personal Links', r.content)
        self.assertIn(b'<input type="hidden" name="encrypted_data"', r.content, bonus_package_count)
        self.assertIn(b'received the request to cancel', r.content)
        get_subscription.assert_called_once_with(u)
        get_purchase_history.assert_called_once_with(u)

    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_apology_page_displayed_if_perma_payments_is_down(self, get_subscription):
        u = LinkUser.objects.get(email='test_user@example.com')
        get_subscription.side_effect = PermaPaymentsCommunicationException

        r = self.get('user_management_settings_usage_plan',
                      user=u)

        self.assertNotIn(b'<input type="hidden" name="encrypted_data"', r.content)
        self.assertIn(b'is currently unavailable', r.content)
        get_subscription.assert_called_once_with(u)

    def test_unauthorized_user_cannot_see_cancellation_page(self):
        u = LinkUser.objects.get(email='test_nonpaying_user@example.com')
        assert not u.can_view_usage_plan()
        self.post('user_management_settings_subscription_cancel',
                  user=u,
                  require_status_code=403)


    def test_authorized_user_cant_use_get_for_cancellation_page(self):
        u = LinkUser.objects.get(email='test_user@example.com')
        assert u.can_view_usage_plan()
        self.get('user_management_settings_subscription_cancel',
                  user=u,
                  require_status_code=405)


    @patch('perma.views.user_management.prep_for_perma_payments', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_authorized_user_cancellation_confirm_form(self, get_subscription, prepped):
        u = LinkUser.objects.get(email='test_user@example.com')
        assert u.can_view_usage_plan()
        subscription = spoof_current_monthly_subscription()
        get_subscription.return_value = subscription
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.post('user_management_settings_subscription_cancel',
                      user=u,
                      data={'account_type':'Individual'})

        self.assertIn(b'<input type="hidden" name="encrypted_data"', r.content)
        self.assertIn(prepped.return_value, r.content)
        self.assertIn(b'Are you sure you want to cancel', r.content)

        get_subscription.assert_called_once_with(u)


    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_update_page_if_no_standing_subscription(self, get_subscription):
        u = LinkUser.objects.get(email='test_user@example.com')
        get_subscription.return_value = None

        self.post('user_management_settings_subscription_update',
                  user=u,
                  data={'account_type':'Individual'},
                  require_status_code=403)


    @patch('perma.views.user_management.prep_for_perma_payments', autospec=True)
    @patch('perma.models.prep_for_perma_payments', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_update_page_if_standing_subscription(self, get_subscription, prepped, prepped_v):
        u = LinkUser.objects.get(email='test_user@example.com')
        subscription = spoof_current_monthly_subscription()
        get_subscription.return_value = subscription
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')
        prepped_v.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.post('user_management_settings_subscription_update',
                      user=u,
                      data={'account_type':'Individual'})

        # Should be able to up/downgrade to all monthly individual tiers, except the current tier
        available_tiers = len([tier for tier in settings.TIERS['Individual'] if tier['period'] == 'monthly']) - 1

        self.assertContains(r, 'Update Credit Card Information')
        self.assertContains(r, '<input type="hidden" name="encrypted_data"', 1)
        self.assertContains(r, 'Change Plan')
        self.assertNotContains(r, 'Cancel Scheduled Downgrade')
        self.assertContains(r, '<input required type="radio" name="encrypted_data"', available_tiers)
        self.assertContains(r, prepped.return_value, available_tiers + 1)
        get_subscription.assert_called_once_with(u)


    @patch('perma.views.user_management.prep_for_perma_payments', autospec=True)
    @patch('perma.models.prep_for_perma_payments', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_update_page_if_downgrade_scheduled(self, get_subscription, prepped, prepped_v):
        u = LinkUser.objects.get(email='test_user@example.com')
        subscription = spoof_current_monthly_subscription_with_scheduled_downgrade()
        get_subscription.return_value = subscription
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')
        prepped_v.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.post('user_management_settings_subscription_update',
                      user=u,
                      data={'account_type':'Individual'})

        self.assertContains(r, 'Update Credit Card Information')
        self.assertContains(r, 'Cancel Scheduled Downgrade')
        self.assertContains(r, '<input type="hidden" name="encrypted_data"', 2)
        self.assertNotContains(r, '<input required type="radio" name="encrypted_data"')
        self.assertContains(r, prepped.return_value, 2)
        get_subscription.assert_called_once_with(u)


    @patch('perma.views.user_management.prep_for_perma_payments', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_update_page_if_subscription_on_hold(self, get_subscription, prepped):
        u = LinkUser.objects.get(email='test_user@example.com')
        subscription = spoof_on_hold_monthly_subscription()
        get_subscription.return_value = subscription
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.post('user_management_settings_subscription_update',
                      user=u,
                      data={'account_type':'Individual'})

        self.assertContains(r, 'Update Credit Card Information')
        self.assertContains(r, '<input type="hidden" name="encrypted_data"', 1)
        self.assertContains(r, prepped.return_value, 1)
        self.assertNotContains(r, 'Change Plan')
        get_subscription.assert_called_once_with(u)


    @patch('perma.views.user_management.prep_for_perma_payments', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_update_page_if_cancellation_requested(self, get_subscription, prepped):
        u = LinkUser.objects.get(email='test_user@example.com')
        subscription = spoof_cancellation_requested_subscription()
        get_subscription.return_value = subscription
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.post('user_management_settings_subscription_update',
                      user=u,
                      data={'account_type':'Individual'})

        self.assertContains(r, 'Update Credit Card Information')
        self.assertContains(r, '<input type="hidden" name="encrypted_data"', 1)
        self.assertContains(r, prepped.return_value, 1)
        self.assertNotContains(r, 'Change Plan')
        get_subscription.assert_called_once_with(u)


    # Subscription, Registrar Users

    @patch('perma.models.prep_for_perma_payments', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_purchase_history', autospec=True)
    def test_registrar_user_nonpaying_registrar(self, get_purchase_history, get_subscription_u, get_subscription_r, prepped):
        u = LinkUser.objects.get(email='test_registrar_user@example.com')
        get_subscription_u.return_value = None
        get_purchase_history.return_value = {'purchases': [], 'total_links': 0}
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.get('user_management_settings_usage_plan',
                      user=u)

        # Individual tiers should be available; no registrar section should be present

        individual_tier_count = len(settings.TIERS['Individual'])
        bonus_package_count = len(settings.BONUS_PACKAGES)
        self.assertIn(b'Get More Personal Links', r.content)
        self.assertIn(b'Purchase a personal subscription', r.content)
        self.assertNotIn(b'Purchase a subscription for Test Firm', r.content)
        self.assertContains(r, '<form class="purchase-form', bonus_package_count)
        self.assertContains(r, '<form class="upgrade-form', individual_tier_count)
        self.assertContains(r, '<input type="hidden" name="encrypted_data"', individual_tier_count + bonus_package_count)
        self.assertContains(r, prepped.return_value, individual_tier_count + bonus_package_count)

        get_subscription_u.assert_called_once_with(u)
        self.assertEqual(get_subscription_r.call_count, 0)
        get_purchase_history.assert_called_once_with(u)

    @patch('perma.models.prep_for_perma_payments', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_purchase_history', autospec=True)
    def test_allpaying_registrar_user_sees_both_subscribe_forms(self, get_purchase_history, get_subscription_u, get_subscription_r, prepped):
        u = LinkUser.objects.get(email='registrar_user@firm.com')
        get_subscription_u.return_value = None
        get_subscription_r.return_value = None
        get_purchase_history.return_value = {'purchases': [], 'total_links': 0}
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.get('user_management_settings_usage_plan',
                      user=u)

        # all tiers should be offered, both individual and registrar-level
        tier_count = len(settings.TIERS['Individual']) + len(settings.TIERS['Registrar'])
        bonus_package_count = len(settings.BONUS_PACKAGES)
        self.assertIn(b'Get More Personal Links', r.content)
        self.assertIn(b'Purchase a personal subscription', r.content)
        self.assertIn(b'Purchase a subscription for Test Firm', r.content)
        self.assertContains(r, '<form class="purchase-form', bonus_package_count)
        self.assertContains(r, '<form class="upgrade-form', tier_count)
        self.assertContains(r, '<input type="hidden" name="encrypted_data"', tier_count + bonus_package_count)
        self.assertContains(r, prepped.return_value, tier_count + bonus_package_count)
        get_subscription_u.assert_called_once_with(u)
        get_subscription_r.assert_called_once_with(u.registrar)
        get_purchase_history.assert_called_once_with(u)

    @patch('perma.models.prep_for_perma_payments', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_purchase_history', autospec=True)
    def test_allpaying_registrar_user_sees_subscriptions_independently(self, get_purchase_history, get_subscription_u, get_subscription_r, prepped):
        u = LinkUser.objects.get(email='registrar_user@firm.com')
        get_subscription_u.return_value = None
        subscription = spoof_current_monthly_subscription()
        get_subscription_r.return_value = subscription
        get_purchase_history.return_value = {'purchases': [], 'total_links': 0}
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.get('user_management_settings_usage_plan',
                      user=u)

        # Individual tiers should be available; the registrar's subscription should be present

        individual_tier_count = len(settings.TIERS['Individual'])
        bonus_package_count = len(settings.BONUS_PACKAGES)
        self.assertIn(b'Get More Personal Links', r.content)
        self.assertIn(b'Purchase a personal subscription', r.content)
        self.assertNotIn(b'Purchase a subscription for Test Firm', r.content)
        self.assertContains(r, '<form class="purchase-form', bonus_package_count)
        self.assertContains(r, '<form class="upgrade-form', individual_tier_count)
        self.assertContains(r, '<input type="hidden" name="encrypted_data"', individual_tier_count + bonus_package_count)
        self.assertContains(r, prepped.return_value, individual_tier_count+ bonus_package_count)

        self.assertIn(b'Rate', r.content)
        self.assertIn(b'Paid Through', r.content)
        self.assertIn(bytes(subscription['status'].lower(), 'utf-8'), r.content)
        self.assertIn(b'Modify Subscription', r.content)
        self.assertContains(r, '<input type="hidden" name="account_type"', 2)
        self.assertIn(b'Cancel Subscription', r.content)

        get_subscription_u.assert_called_once_with(u)
        get_subscription_r.assert_called_once_with(u.registrar)
        get_purchase_history.assert_called_once_with(u)

    @patch('perma.views.user_management.prep_for_perma_payments', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_allpaying_registrar_user_personal_cancellation_confirm_form(self, get_subscription_u, get_subscription_r, prepped):
        u = LinkUser.objects.get(email='registrar_user@firm.com')
        assert u.can_view_usage_plan()
        subscription = spoof_current_monthly_subscription()
        get_subscription_u.return_value = subscription
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.post('user_management_settings_subscription_cancel',
                      user=u,
                      data={'account_type':'Individual'})

        self.assertIn(b'<input type="hidden" name="encrypted_data"', r.content)
        self.assertIn(prepped.return_value, r.content)
        self.assertIn(b'Are you sure you want to cancel', r.content)
        self.assertNotIn(b'Test Firm', r.content)
        self.assertIn(b'personal', r.content)

        get_subscription_u.assert_called_once_with(u)


    @patch('perma.views.user_management.prep_for_perma_payments', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_allpaying_registrar_user_institutional_cancellation_confirm_form(self, get_subscription_u, get_subscription_r, prepped):
        u = LinkUser.objects.get(email='registrar_user@firm.com')
        assert u.can_view_usage_plan()
        subscription = spoof_current_monthly_subscription()
        get_subscription_r.return_value = subscription
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.post('user_management_settings_subscription_cancel',
                      user=u,
                      data={'account_type':'Registrar'})

        self.assertIn(b'<input type="hidden" name="encrypted_data"', r.content)
        self.assertIn(prepped.return_value, r.content)
        self.assertIn(b'Are you sure you want to cancel', r.content)
        self.assertIn(b'Test Firm', r.content)
        self.assertNotIn(b'Personal', r.content)

        get_subscription_r.assert_called_once_with(u.registrar)


    @patch('perma.views.user_management.prep_for_perma_payments', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_allpaying_registrar_user_personal_update_form(self, get_subscription, prepped):
        u = LinkUser.objects.get(email='registrar_user@firm.com')
        assert u.can_view_usage_plan()
        subscription = spoof_current_monthly_subscription()
        get_subscription.return_value = subscription
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

        r = self.post('user_management_settings_subscription_update',
                      user=u,
                      data={'account_type':'Individual'})

        self.assertNotIn(b'Test Firm', r.content)
        self.assertIn(b'Personal', r.content)
        get_subscription.assert_called_once_with(u)


    @patch('perma.views.user_management.prep_for_perma_payments', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_allpaying_registrar_user_institutional_update_form(self, get_subscription, prepped):
        u = LinkUser.objects.get(email='registrar_user@firm.com')
        assert u.can_view_usage_plan()
        subscription = spoof_current_monthly_subscription()
        get_subscription.return_value = subscription
        prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')


        r = self.post('user_management_settings_subscription_update',
                      user=u,
                      data={'account_type':'Registrar'})

        self.assertIn(b'Test Firm', r.content)
        self.assertNotIn(b'personal', r.content)
        get_subscription.assert_called_once_with(u.registrar)


    # Tools

    def test_api_key(self):
        response = self.get('user_management_settings_tools',
                             user='test_another_library_org_user@example.com').content
        self.assertNotIn(b'id="id_api_key"', response)
        self.submit_form('api_key_create',
                          user='test_another_library_org_user@example.com',
                          data={},
                          success_url=reverse('user_management_settings_tools'))
        response = self.get('user_management_settings_tools',
                             user='test_another_library_org_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        key = soup.find('input', {'id': 'id_api_key'})
        val = key.get('value', '')
        self.assertTrue(val)
        # do it again, and make sure the key changes
        self.submit_form('api_key_create',
                          user='test_another_library_org_user@example.com',
                          data={},
                          success_url=reverse('user_management_settings_tools'))
        response = self.get('user_management_settings_tools',
                             user='test_another_library_org_user@example.com').content
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
        self.assertIn(b'Pending Registrar', response)
        self.assertIn(b'Thank you for requesting an account for your library. Perma.cc will review your request as soon as possible.', response)
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
        return { 'email': 'library{}@university.org'.format(rand),
                 'name': 'University Library {}'.format(rand),
                 'website': 'http://website{}.org'.format(rand),
                 'address': '{} Main St., Boston MA 02144'.format(rand)}

    def new_lib_user(self):
        rand = random()
        email = self.randomize_capitalization('user{}@university.org'.format(rand))
        return { 'raw_email': email,
                 'normalized_email': email.lower(),
                 'first': 'Joe',
                 'last': 'Yacobówski' }

    def check_library_labels(self, soup):
        name_label = soup.find('label', {'for': 'id_b-name'})
        self.assertEqual(name_label.text, "Library name")
        email_label = soup.find('label', {'for': 'id_b-email'})
        self.assertEqual(email_label.text, "Library email")
        website_label = soup.find('label', {'for': 'id_b-website'})
        self.assertEqual(website_label.text, "Library website")

    def check_lib_user_labels(self, soup):
        email_label = soup.find('label', {'for': 'id_a-e-address'})
        self.assertEqual(email_label.text, "Your email")

    def check_lib_email(self, message, new_lib, user):
        our_address = settings.DEFAULT_FROM_EMAIL

        self.assertIn(new_lib['name'], message.body)
        self.assertIn(new_lib['email'], message.body)

        self.assertIn(user['raw_email'], message.body)

        id = Registrar.objects.get(email=new_lib['email']).id
        approve_url = "http://testserver{}".format(reverse('user_management_approve_pending_registrar', args=[id]))
        self.assertIn(approve_url, message.body)
        self.assertEqual(message.subject, "Perma.cc new library registrar account request")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': user['raw_email']})

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
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
        self.assertEqual(len(inputs), 9)
        for input in inputs:
            if input['name'] in ['csrfmiddlewaretoken', 'telephone']:
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))

        # If request_data is present in session, registrar form is prepopulated,
        # and labels are still customized as expected
        session = self.client.session
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        session['request_data'] = { 'b-email': new_lib['email'],
                                    'b-website': new_lib['website'],
                                    'b-name': new_lib['name'],
                                    'b-address': new_lib['address'],
                                    'a-e-address': new_lib_user['raw_email'],
                                    'a-first_name': new_lib_user['first'],
                                    'a-last_name': new_lib_user['last'],
                                    'csrfmiddlewaretoken': '11YY3S2DgOw2DHoWVEbBArnBMdEA2svu' }
        session.save()
        response = self.get('libraries').content
        soup = BeautifulSoup(response, 'html.parser')
        self.check_library_labels(soup)
        self.check_lib_user_labels(soup)
        inputs = soup.select('input')
        self.assertEqual(len(inputs), 9)
        for input in inputs:
            if input['name'] in ['csrfmiddlewaretoken', 'telephone']:
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

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_library_submit_success(self):
        '''
           Does the library signup form submit as expected? Success cases.
        '''
        expected_emails_sent = 0

        # Not logged in, submit all fields sans first and last name
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        self.submit_form('libraries',
                          data = { 'b-email': new_lib['email'],
                                   'b-website': new_lib['website'],
                                   'b-name': new_lib['name'],
                                   'a-e-address': new_lib_user['raw_email'] },
                          success_url=reverse('register_library_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_lib_email(mail.outbox[expected_emails_sent - 2], new_lib, new_lib_user)
        self.check_new_activation_email(mail.outbox[expected_emails_sent - 1], new_lib_user['raw_email'])

        # Not logged in, submit all fields including first and last name
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        self.submit_form('libraries',
                          data = { 'b-email': new_lib['email'],
                                   'b-website': new_lib['website'],
                                   'b-name': new_lib['name'],
                                   'a-e-address': new_lib_user['raw_email'],
                                   'a-first_name': new_lib_user['first'],
                                   'a-last_name': new_lib_user['last']},
                          success_url=reverse('register_library_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_lib_email(mail.outbox[expected_emails_sent - 2], new_lib, new_lib_user)
        self.check_new_activation_email(mail.outbox[expected_emails_sent - 1], new_lib_user['raw_email'])

        # Logged in
        new_lib = self.new_lib()
        existing_lib_user = {
            'raw_email': 'test_user@example.com',
            'normalized_email': 'test_user@example.com',
        }
        self.submit_form('libraries',
                          data = { 'b-email': new_lib['email'],
                                   'b-website': new_lib['website'],
                                   'b-name': new_lib['name'] },
                          success_url=reverse('user_management_settings_affiliations'),
                          user=existing_lib_user['raw_email'])
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_lib_email(mail.outbox[expected_emails_sent - 1], new_lib, existing_lib_user)

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_library_form_honeypot(self):
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        self.submit_form('libraries',
                          data = { 'b-email': new_lib['email'],
                                   'b-website': new_lib['website'],
                                   'b-name': new_lib['name'],
                                   'a-e-address': new_lib_user['raw_email'],
                                   'a-first_name': new_lib_user['first'],
                                   'a-last_name': new_lib_user['last'],
                                   'a-telephone': "I'm a bot."},
                          success_url=reverse('register_library_instructions'))
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(Registrar.objects.filter(name=new_lib['name']).exists())

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
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
                          data = {'b-email': new_lib['email'],
                                  'b-website': new_lib['website'],
                                  'b-name': new_lib['name']},
                          form_keys = ['registrar_form', 'user_form'],
                          error_keys = ['email'])
        self.assertEqual(len(mail.outbox), 0)

        # Not logged in, user appears to have already registered
        data = {'b-email': new_lib['email'],
                'b-website': new_lib['website'],
                'b-name': new_lib['name'],
                'a-e-address': self.randomize_capitalization(existing_lib_user['email'])}
        self.submit_form('libraries',
                          data = data,
                          form_keys = ['registrar_form', 'user_form'],
                          success_url = '/login?next=/libraries/')
        self.assertDictEqual(self.client.session['request_data'], data)
        self.assertEqual(len(mail.outbox), 0)

        # Not logged in, registrar appears to exist already
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
        return { 'requested_account_note': 'Court {}'.format(rand) }

    def new_court_user(self):
        rand = random()
        email = self.randomize_capitalization('user{}@university.org'.format(rand))
        return { 'raw_email': email,
                 'normalized_email': email.lower(),
                 'first': 'Joe',
                 'last': 'Yacobówski' }

    def check_court_email(self, message, court_email):
        our_address = settings.DEFAULT_FROM_EMAIL

        # Doesn't check email contents yet; too many variations possible presently
        self.assertEqual(message.subject, "Perma.cc new library court account information request")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': court_email})

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
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
                          data = { 'e-address': self.randomize_capitalization(existing_user['email'])},
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

        # Existing user's email address + court info
        self.submit_form('sign_up_courts',
                          data = { 'e-address': self.randomize_capitalization(existing_user['email']),
                                   'requested_account_note': new_court['requested_account_note']},
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

        # New user email address, don't create account
        self.submit_form('sign_up_courts',
                          data = { 'e-address': new_user['raw_email'],
                                   'requested_account_note': new_court['requested_account_note']},
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], new_user['raw_email'])

        # New user email address, create account
        self.submit_form('sign_up_courts',
                          data = { 'e-address': new_user['raw_email'],
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True },
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_new_activation_email(mail.outbox[expected_emails_sent - 2], new_user['raw_email'])
        self.check_court_email(mail.outbox[expected_emails_sent - 1], new_user['raw_email'])

        # LOGGED IN

        # New user email address
        # (This succeeds and creates a new account; see issue 1749)
        new_user = self.new_court_user()
        self.submit_form('sign_up_courts',
                          data = { 'e-address': new_user['raw_email'],
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True },
                          user = existing_user['email'],
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_new_activation_email(mail.outbox[expected_emails_sent - 2], new_user['raw_email'])
        self.check_court_email(mail.outbox[expected_emails_sent - 1], new_user['raw_email'])

        # Existing user's email address, not that of the user logged in.
        # (This is odd; see issue 1749)
        self.submit_form('sign_up_courts',
                          data = { 'e-address': self.randomize_capitalization(existing_user['email']),
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True },
                          user = another_existing_user['email'],
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_court_form_honeypot(self):
        new_court = self.new_court()
        new_user = self.new_court_user()
        self.submit_form('sign_up_courts',
                          data = { 'e-address': new_user['raw_email'],
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True,
                                   'telephone': "I'm a bot." },
                          success_url = reverse('register_email_instructions'))
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(LinkUser.objects.filter(email__iexact=new_user['raw_email']).exists())

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
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

    def create_firm_organization_form(self):
        return {
            'name': f'Firm {random()}',
            'email': 'test-firm@example.com',
            'website': 'https://www.example.com',
        }

    def create_firm_usage_form(self):
        return {
            'estimated_number_of_accounts': '10 - 50',
            'estimated_perma_links_per_month': '100+',
        }

    def create_firm_user_form(self):
        email = self.randomize_capitalization(f'user{random()}@university.org')
        return {
            'raw_email': email,
            'normalized_email': email.lower(),
            'first': 'Joe',
            'last': 'Yacobówski',
            'would_be_org_admin': bool(getrandbits(1)),
        }

    def check_firm_email(self, message, firm_email):
        our_address = settings.DEFAULT_FROM_EMAIL

        # Doesn't check email contents yet; too many variations possible presently
        self.assertEqual(message.subject, "Perma.cc new law firm account information request")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': firm_email})

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_firm_success(self):
        '''
            Does the firm signup form submit as expected? Success cases.
        '''
        firm_organization_form = self.create_firm_organization_form()
        firm_usage_form = self.create_firm_usage_form()
        firm_user_form = self.create_firm_user_form()
        existing_user = {'email': 'test_user@example.com'}
        another_existing_user = {'email': 'another_library_user@example.com'}
        expected_emails_sent = 0

        # NOT LOGGED IN

        # Existing user's email address, no firm info (should not succeed due to missing values)
        self.submit_form(
            'sign_up_firm',
            data={'e-address': self.randomize_capitalization(existing_user['email'])},
            success_url=reverse('firm_request_response'),
        )
        expected_emails_sent += 0
        self.assertEqual(len(mail.outbox), expected_emails_sent)

        # Existing user's email address + firm info
        self.submit_form(
            'sign_up_firm',
            data={
                'e-address': self.randomize_capitalization(existing_user['email']),
                'would_be_org_admin': firm_user_form['would_be_org_admin'],
                **firm_organization_form,
                **firm_usage_form,
            },
            success_url=reverse('firm_request_response'),
        )
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

        # New user email address, don't create account
        self.submit_form(
            'sign_up_firm',
            data={
                'e-address': firm_user_form['raw_email'],
                'would_be_org_admin': firm_user_form['would_be_org_admin'],
                **firm_organization_form,
                **firm_usage_form,
            },
            success_url=reverse('firm_request_response'),
        )
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], firm_user_form['raw_email'])

        # New user email address, create account
        self.submit_form(
            'sign_up_firm',
            data={
                'e-address': firm_user_form['raw_email'],
                'would_be_org_admin': firm_user_form['would_be_org_admin'],
                **firm_organization_form,
                **firm_usage_form,
                'create_account': True,
            },
            success_url=reverse('register_email_instructions'),
        )
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_new_activation_email(
            mail.outbox[expected_emails_sent - 2], firm_user_form['raw_email']
        )
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], firm_user_form['raw_email'])

        # LOGGED IN

        # New user email address
        # (This succeeds and creates a new account; see issue 1749)
        firm_user_form = self.create_firm_user_form()
        self.submit_form(
            'sign_up_firm',
            data={
                'e-address': firm_user_form['raw_email'],
                'would_be_org_admin': firm_user_form['would_be_org_admin'],
                **firm_organization_form,
                **firm_usage_form,
                'create_account': True,
            },
            user=existing_user['email'],
            success_url=reverse('register_email_instructions'),
        )
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_new_activation_email(
            mail.outbox[expected_emails_sent - 2], firm_user_form['raw_email']
        )
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], firm_user_form['raw_email'])

        # Existing user's email address, not that of the user logged in.
        # (This is odd; see issue 1749)
        self.submit_form(
            'sign_up_firm',
            data={
                'e-address': self.randomize_capitalization(existing_user['email']),
                'would_be_org_admin': firm_user_form['would_be_org_admin'],
                **firm_organization_form,
                **firm_usage_form,
                'create_account': True,
            },
            user=another_existing_user['email'],
            success_url=reverse('firm_request_response'),
        )
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_firm_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_firm_form_honeypot(self):
        firm_organization_form = self.create_firm_organization_form()
        firm_usage_form = self.create_firm_usage_form()
        firm_user_form = self.create_firm_user_form()
        self.submit_form(
            'sign_up_firm',
            data={
                'e-address': firm_user_form['raw_email'],
                'create_account': True,
                'telephone': "I'm a bot.",
                **firm_organization_form,
                **firm_usage_form,
            },
            success_url=reverse('register_email_instructions'),
        )
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(
            LinkUser.objects.filter(email__iexact=firm_user_form['raw_email']).exists()
        )

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_firm_failure(self):
        '''
            Does the firm signup form submit as expected? Failure cases.
        '''
        # Not logged in, blank submission reports correct fields required
        self.submit_form(
            'sign_up_firm',
            data={},
            form_keys=['organization_form', 'usage_form', 'user_form'],
            error_keys=['email', 'would_be_org_admin'],
        )
        self.assertEqual(len(mail.outbox), 0)

        # Logged in, blank submission reports same fields required
        # (This is odd; see issue 1749)
        self.submit_form(
            'sign_up_firm',
            data={},
            form_keys=['organization_form', 'usage_form', 'user_form'],
            user='test_user@example.com',
            error_keys=['email', 'would_be_org_admin'],
        )
        self.assertEqual(len(mail.outbox), 0)

    ### Individual Users ###

    def check_new_activation_email(self, message, user_email):
        self.assertEqual(message.subject, "A Perma.cc account has been created for you")
        self.assertEqual(message.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(message.recipients(), [user_email])

        activation_url = next(
            line for line in message.body.rstrip().split('\n') if line.strip().startswith('http')
        )
        return activation_url

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_account_creation_views(self):
        # user registration
        new_user_raw_email = self.randomize_capitalization("new_email@test.com")
        new_user_normalized_email = new_user_raw_email.lower()
        self.submit_form('sign_up', {'e-address': new_user_raw_email, 'first_name': 'Test', 'last_name': 'Test'},
                         success_url=reverse('register_email_instructions'),
                         success_query=LinkUser.objects.filter(
                             email=new_user_normalized_email,
                             raw_email=new_user_raw_email
                         ))

        # email sent
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        activation_url = self.check_new_activation_email(message, new_user_raw_email)

        # the new user is created, but is unactivated
        user = LinkUser.objects.get(email=new_user_normalized_email)
        self.assertEqual(user.raw_email, new_user_raw_email)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_confirmed)

        # if you tamper with the code, it is rejected
        response = self.client.get(activation_url[:-1]+'wrong/', secure=True)
        self.assertContains(response, 'This activation/reset link is invalid')

        # reg confirm - non-matching passwords
        response = self.client.get(activation_url, follow=True, secure=True)
        post_url = response.redirect_chain[0][0]
        self.assertTemplateUsed(response, 'registration/password_reset_confirm.html')
        response = self.client.post(post_url, {'new_password1': 'Anewpass1', 'new_password2': 'Anewpass2'}, follow=True, secure=True)
        self.assertNotContains(response, 'Your password has been set')
        self.assertContains(response, "The two password fields didn’t match")
        # reg confirm - correct
        response = self.client.post(post_url, {'new_password1': 'Anewpass1', 'new_password2': 'Anewpass1'}, follow=True, secure=True)
        self.assertContains(response, 'Your password has been set')

        # Doesn't work twice.
        response = self.client.post(post_url, {'new_password1': 'Anotherpass1', 'new_password2': 'Anotherpass1'}, follow=True, secure=True)
        self.assertContains(response, 'This activation/reset link is invalid')

        # the new user is now activated and can log in
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_confirmed)
        response = self.client.post(reverse('user_management_limited_login'), {'username': new_user_raw_email, 'password': 'Anewpass1'}, follow=True, secure=True)
        self.assertContains(response, 'Enter any URL to preserve it forever')

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_suggested_registrars(self):
        # Register user
        _, registrar_domain = self.registrar.email.split('@')
        new_user_email = f'new_user@{registrar_domain}'
        self.submit_form(
            'sign_up',
            {'e-address': new_user_email, 'first_name': 'Test', 'last_name': 'Test'},
            success_url=reverse('register_email_instructions'),
            success_query=LinkUser.objects.filter(email=new_user_email),
        )
        self.assertEqual(len(mail.outbox), 1)

        # Obtain suggested registrar(s) from activation email message
        message = mail.outbox[0]
        lines = message.body.splitlines()
        captures = []
        for line in lines:
            if line.lstrip().startswith('- '):
                captures.append(line.strip('- '))

        # Validate suggested registrar(s)
        self.assertEqual(len(captures), 1)
        self.assertEqual(captures[0], f'{self.registrar.name}: {self.registrar.email}')

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_signup_with_existing_email_rejected(self):
        self.assertEqual(LinkUser.objects.filter(email__iexact=self.registrar_user.email).count(), 1)
        self.submit_form('sign_up',
                         {'e-address': self.registrar_user.email, 'first_name': 'Test', 'last_name': 'Test'},
                         error_keys=['email'])
        self.submit_form('sign_up',
                 {'e-address': self.randomize_capitalization(self.registrar_user.email), 'first_name': 'Test', 'last_name': 'Test'},
                 error_keys=['email'])
        self.assertEqual(LinkUser.objects.filter(email__iexact=self.registrar_user.email).count(), 1)

    @override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
    def test_new_user_form_honeypot(self):
        new_user_email = "new_email@test.com"
        self.submit_form('sign_up',
                          data = { 'e-address': new_user_email,
                                   'telephone': "I'm a bot." },
                          success_url = reverse('register_email_instructions'))
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(LinkUser.objects.filter(email__iexact=new_user_email).exists())

    def test_manual_user_creation_rejects_duplicative_emails(self):
        email = 'test_user@example.com'
        self.assertTrue(LinkUser.objects.filter(email=email).exists())
        new_user = LinkUser(email=self.randomize_capitalization(email))
        self.assertRaises(IntegrityError, new_user.save)

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

    ### PASSWORD RESETS ###

    def test_password_reset_is_case_insensitive(self):
        email = 'test_user@example.com'
        not_a_user = 'doesnotexist@example.com'
        self.assertEqual(LinkUser.objects.filter(email__iexact=email).count(), 1)
        self.assertFalse(LinkUser.objects.filter(email=not_a_user).exists())

        self.submit_form('password_reset', data={})
        self.submit_form('password_reset', data={'email': not_a_user})
        self.assertEqual(len(mail.outbox), 0)

        self.submit_form('password_reset', data={'email': email})
        self.assertEqual(len(mail.outbox), 1)

        self.submit_form('password_reset', data={'email': self.randomize_capitalization(email)})
        self.assertEqual(len(mail.outbox), 2)

    ### ADMIN STATS ###

    def test_admin_stats(self):
        self.log_in_user(self.admin_user)
        self.get('admin_stats', reverse_kwargs={'args':['days']})
        self.get('admin_stats', reverse_kwargs={'args':['celery']})
        self.get('admin_stats', reverse_kwargs={'args':['random']})
        self.get('admin_stats', reverse_kwargs={'args':['emails']})
        self.get('admin_stats', reverse_kwargs={'args':['job_queue']})
