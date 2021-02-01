from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.conf import settings
from django.test import override_settings
from django.utils import timezone

from mock import patch, sentinel

from perma.exceptions import PermaPaymentsCommunicationException, InvalidTransmissionException
import perma.models
from perma.models import (
    ACTIVE_SUBSCRIPTION_STATUSES,
    FIELDS_REQUIRED_FROM_PERMA_PAYMENTS,
    Link, LinkUser, Organization, Registrar, Folder, Sponsorship,
    link_count_in_time_period,
    most_active_org_in_time_period,
    subscription_is_active
)
from perma.utils import pp_date_from_post, tz_datetime, first_day_of_next_month, today_next_year

from .utils import PermaTestCase


# Fixtures

GENESIS = datetime.fromtimestamp(0).replace(tzinfo=timezone.utc)

FAKE_TIERS = {
    'Individual': [defaultdict(str) for i in range(3)],
    'Registrar': [defaultdict(str) for i in range(3)]
}

def nonpaying_registrar():
    registrar = Registrar()
    registrar.save()
    registrar.refresh_from_db()
    assert registrar.nonpaying
    return registrar

def paying_registrar():
    registrar = Registrar(
        nonpaying=False,
        cached_subscription_status="Sentinel Status",
        cached_paid_through=GENESIS,
        base_rate=Decimal(100.00),
        in_trial=False
    )
    registrar.save()
    registrar.refresh_from_db()
    assert not registrar.nonpaying
    assert registrar.unlimited
    return registrar

def paying_limited_registrar():
    registrar = Registrar(
        nonpaying=False,
        cached_subscription_status="Sentinel Status",
        cached_paid_through=GENESIS,
        cached_subscription_rate=Decimal(0.01),
        base_rate=Decimal(100.00),
        unlimited=False,
        in_trial=False
    )
    registrar.save()
    registrar.refresh_from_db()
    assert not registrar.nonpaying
    assert not registrar.unlimited
    return registrar

def nonpaying_user():
    user = LinkUser(
        nonpaying=True
    )
    user.save()
    user.refresh_from_db()
    assert user.nonpaying
    return user

def paying_user():
    user = LinkUser(
        nonpaying=False,
        cached_subscription_status="Sentinel Status",
        cached_paid_through=GENESIS,
        cached_subscription_rate=Decimal(0.01),
        base_rate=Decimal(100.00),
        in_trial=False
    )
    user.save()
    user.refresh_from_db()
    assert not user.nonpaying
    return user

def customers():
    return [paying_registrar(), paying_user()]

def noncustomers():
    return [nonpaying_registrar(), nonpaying_user()]

def user_with_links():
    # a user with 6 personal links, made at intervals
    user = LinkUser()
    user.save()
    today = timezone.now()
    earlier_this_month = today.replace(day=1)
    within_the_last_year = today - relativedelta(months=6)
    over_a_year_ago = today - relativedelta(years=1, days=2)
    three_years_ago = today - relativedelta(years=3)
    links = [
        Link(creation_timestamp=today, guid="AAAA-AAAA", created_by=user),
        Link(creation_timestamp=earlier_this_month, guid="BBBB-BBBB", created_by=user),
        Link(creation_timestamp=within_the_last_year, guid="DDDD-DDDDD", created_by=user),
        Link(creation_timestamp=over_a_year_ago, guid="EEEE-EEEE", created_by=user),
        Link(creation_timestamp=three_years_ago, guid="FFFF-FFFF", created_by=user),
    ]
    for link in links:
        link.save()
    return user

def user_with_links_this_month_before_the_15th():
    # for use in testing mid-month link count limits
    user = LinkUser()
    user.save()
    links = [
        Link(creation_timestamp=timezone.now().replace(day=1), guid="AAAA-AAAA", created_by=user),
        Link(creation_timestamp=timezone.now().replace(day=2), guid="BBBB-BBBB", created_by=user),
        Link(creation_timestamp=timezone.now().replace(day=3), guid="DDDD-DDDDD", created_by=user),
        Link(creation_timestamp=timezone.now().replace(day=4), guid="EEEE-EEEE", created_by=user),
        Link(creation_timestamp=timezone.now().replace(day=14), guid="FFFF-FFFF", created_by=user),
    ]
    for link in links:
        link.save()
    return user

def complex_user_with_bonus_link(in_subfolder=False):
    user = LinkUser(link_limit=2, bonus_links=0)
    user.save()
    user.organizations.add(Organization.objects.get(pk=1))
    sponsorship = Sponsorship(registrar=Registrar.objects.get(pk=1), user=user, created_by=user)
    sponsorship.save()
    subfolder = Folder(parent=user.top_level_folders()[0], name='Subfolder')
    subfolder.save()
    bonus_link = Link(created_by=user, bonus_link=True)
    bonus_link.save()
    if in_subfolder:
        bonus_link.move_to_folder_for_user(subfolder, user)
    user.refresh_from_db()
    return user, bonus_link

def spoof_pp_response_wrong_pk(customer):
    data = {
        "customer_pk": "not_the_pk",
        "customer_type": customer.customer_type
    }
    assert customer.pk != data['customer_pk']
    return data

def spoof_pp_response_wrong_type(customer):
    data = {
        "customer_pk": customer.pk,
        "customer_type": "not_the_type"
    }
    assert customer.customer_type != data['customer_type']
    return data

def spoof_pp_response_no_subscription(customer):
    return {
        "customer_pk": customer.pk,
        "customer_type": customer.customer_type,
        "subscription": None,
        "purchases": []
    }

def spoof_pp_response_no_subscription_two_purchases(customer):
    return {
        "customer_pk": customer.pk,
        "customer_type": customer.customer_type,
        "subscription": None,
        "purchases": [{
            "id": 1,
            "link_quantity": "10"
        },{
            "id": 2,
            "link_quantity": "50"
        }]
    }

def spoof_pp_response_subscription(customer):
    return {
        "customer_pk": customer.pk,
        "customer_type": customer.customer_type,
        "subscription": {
            "status": "Sentinel Status",
            "rate": "9999.99",
            "frequency": "sample",
            "paid_through": "1970-01-21T00:00:00.000000Z",
            "link_limit_effective_timestamp": "1970-01-21T00:00:00.000000Z",
            "link_limit": "unlimited"

        },
        "purchases": []
    }

def spoof_pp_response_subscription_with_pending_change(customer):
    response = {
        "customer_pk": customer.pk,
        "customer_type": customer.customer_type,
        "subscription": {
            "status": "Sentinel Status",
            "rate": "9999.99",
            "frequency": "sample",
            "paid_through": "9999-01-21T00:00:00.000000Z",
            "link_limit_effective_timestamp": "9999-01-21T00:00:00.000000Z",
            "link_limit": "unlimited"

        },
        "purchases": []
    }
    assert pp_date_from_post(response['subscription']['link_limit_effective_timestamp']), timezone.now()
    return response

def active_cancelled_subscription():
    return {
        'status': "Canceled",
        'paid_through': timezone.now() + relativedelta(years=1)
    }

def expired_cancelled_subscription():
    return {
        'status': "Canceled",
        'paid_through': timezone.now() + relativedelta(years=-1)
    }

# Tests

class ModelsTestCase(PermaTestCase):

    def test_new_orgs_are_public_by_default(self):
        r = Registrar()
        r.save()
        o = Organization(registrar=r)
        o.save()
        r.refresh_from_db()
        o.refresh_from_db()
        self.assertFalse(r.orgs_private_by_default)
        self.assertFalse(o.default_to_private)

    def test_new_orgs_respect_registrar_default_privacy_policy(self):
        r = Registrar(orgs_private_by_default=True)
        r.save()
        o = Organization(registrar=r)
        o.save()
        r.refresh_from_db()
        o.refresh_from_db()
        self.assertTrue(r.orgs_private_by_default)
        self.assertTrue(o.default_to_private)

    def test_existing_org_privacy_unaffected_by_registrar_change(self):
        r = Registrar()
        r.save()
        o = Organization(registrar=r)
        o.save()
        r.refresh_from_db()
        o.refresh_from_db()
        self.assertFalse(r.orgs_private_by_default)
        self.assertFalse(o.default_to_private)

        r.orgs_private_by_default = True
        r.save()
        r.refresh_from_db()
        o.refresh_from_db()
        self.assertTrue(r.orgs_private_by_default)
        self.assertFalse(o.default_to_private)

        r.orgs_private_by_default = False
        r.save()
        r.refresh_from_db()
        o.refresh_from_db()
        self.assertFalse(r.orgs_private_by_default)
        self.assertFalse(o.default_to_private)

    def test_org_privacy_does_not_revert_to_registrar_default_on_save(self):
        r = Registrar(orgs_private_by_default=True)
        r.save()
        o = Organization(registrar=r)
        o.save()
        r.refresh_from_db()
        o.refresh_from_db()
        self.assertTrue(r.orgs_private_by_default)
        self.assertTrue(o.default_to_private)

        o.default_to_private = False
        o.save()
        o.refresh_from_db()
        self.assertFalse(o.default_to_private)

        o.name = 'A New Name'
        o.save()
        o.refresh_from_db()
        self.assertEqual(o.name, 'A New Name')
        self.assertFalse(o.default_to_private)

    def test_new_folder_path_is_cached(self):
        f1 = Folder()
        f1.save()
        f1.refresh_from_db()
        self.assertEqual(str(f1.pk), f1.cached_path)
        f2 = Folder(parent=f1)
        f2.save()
        f2.refresh_from_db()
        self.assertEqual(f'{f1.pk}-{f2.pk}', f2.cached_path)

    def test_folders_cached_paths_updated_when_moved(self):
        # f1
        # f2
        # f3 -> f3_1
        f1 = Folder(name=1)
        f1.save()
        f1.refresh_from_db()
        f2 = Folder(parent=f1, name='2')
        f2.save()
        f2.refresh_from_db()
        f3 = Folder(parent=f1, name='3')
        f3.save()
        f3.refresh_from_db()
        f3_1 = Folder(parent=f3, name='3_1')
        f3_1.save()
        f3_1.refresh_from_db()
        self.assertEqual(f'{f1.pk}-{f3.pk}', f3.cached_path)
        self.assertEqual(f'{f1.pk}-{f3.pk}-{f3_1.pk}', f3_1.cached_path)

        # f1
        # f2 -> f3 -> f3_1
        f3.parent = f2
        f3.save()
        f3.refresh_from_db()
        f3_1.refresh_from_db()
        self.assertEqual(f'{f1.pk}-{f2.pk}-{f3.pk}', f3.cached_path)
        self.assertEqual(f'{f1.pk}-{f2.pk}-{f3.pk}-{f3_1.pk}', f3_1.cached_path)

    def test_link_count_in_time_period_no_links(self):
        '''
            If no links in period, should return 0
        '''
        no_links = Link.objects.none()
        self.assertEqual(link_count_in_time_period(no_links), 0)

    def test_link_count_period_invalid_dates(self):
        '''
            If end date is before start date, should raise an exception
        '''
        no_links = Link.objects.none()
        now = tz_datetime(timezone.now().year, 1, 1)
        later = tz_datetime(timezone.now().year + 1, 1, 1)
        with self.assertRaises(ValueError):
            link_count_in_time_period(no_links, later, now)

    def test_link_count_period_equal_dates(self):
        '''
            If end date = start date, links are only counted once
        '''
        now = tz_datetime(timezone.now().year, 1, 1)
        user = LinkUser()
        user.save()
        link = Link(creation_timestamp=now, guid="AAAA-AAAA", created_by=user)
        link.save()

        links = Link.objects.filter(pk=link.pk)
        self.assertEqual(len(links), 1)
        self.assertEqual(link_count_in_time_period(links, now, now), len(links))

    def test_link_count_valid_period(self):
        '''
            Should include links created only in the target year
        '''
        now = tz_datetime(timezone.now().year, 1, 1)
        two_years_ago = tz_datetime(now.year - 2, 1, 1)
        three_years_ago = tz_datetime(now.year - 3, 1, 1)
        user = LinkUser()
        user.save()
        link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC", "DDDD-DDDD", "EEEE-EEEE"]
        older= Link(creation_timestamp=three_years_ago, guid=link_pks[0], created_by=user)
        older.save()
        old = Link(creation_timestamp=two_years_ago, guid=link_pks[1], created_by=user)
        old.save()
        now1 = Link(creation_timestamp=now, guid=link_pks[2], created_by=user)
        now1.save()
        now2 = Link(creation_timestamp=now, guid=link_pks[3], created_by=user)
        now2.save()
        now3 = Link(creation_timestamp=now, guid=link_pks[4], created_by=user)
        now3.save()

        links = Link.objects.filter(pk__in=link_pks)
        self.assertEqual(len(links), 5)
        self.assertEqual(link_count_in_time_period(links, three_years_ago, two_years_ago), 2)

    def test_org_link_count_this_year(self):
        '''
            Should include links created this year and exclude links
            older than that.
        '''
        r = Registrar()
        r.save()
        o = Organization(registrar=r)
        o.save()
        self.assertEqual(o.link_count_this_year(), 0)

        now = tz_datetime(timezone.now().year, 1, 1)
        two_years_ago = tz_datetime(now.year - 2, 1, 1)
        user = LinkUser()
        user.save()
        link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC"]
        too_early = Link(creation_timestamp=two_years_ago, guid=link_pks[0], created_by=user, organization=o)
        too_early.save()
        now1 = Link(creation_timestamp=now, guid=link_pks[1], created_by=user, organization=o)
        now1.save()
        now2 = Link(creation_timestamp=now, guid=link_pks[2], created_by=user, organization=o)
        now2.save()

        links = Link.objects.filter(pk__in=link_pks)
        self.assertEqual(len(links), 3)
        self.assertEqual(o.link_count_this_year(), 2)

    def test_registrar_link_count_this_year(self):
        '''
            Should include links created this year and exclude links
            older than that. Should work across all its orgs.
        '''
        r = Registrar()
        r.save()
        o1 = Organization(registrar=r)
        o1.save()
        o2 = Organization(registrar=r)
        o2.save()

        now = tz_datetime(timezone.now().year, 1, 1)
        two_years_ago = tz_datetime(now.year - 2, 1, 1)
        user = LinkUser()
        user.save()
        link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC", "DDDD-DDDD"]
        too_early = Link(creation_timestamp=two_years_ago, guid=link_pks[0], created_by=user, organization=o1)
        too_early.save()
        now1 = Link(creation_timestamp=now, guid=link_pks[1], created_by=user, organization=o1)
        now1.save()
        now2 = Link(creation_timestamp=now, guid=link_pks[2], created_by=user, organization=o1)
        now2.save()
        now3 = Link(creation_timestamp=now, guid=link_pks[3], created_by=user, organization=o2)
        now3.save()

        links = Link.objects.filter(pk__in=link_pks)
        self.assertEqual(len(links), 4)
        self.assertEqual(r.link_count_this_year(), 3)

    def test_most_active_org_in_time_period_no_links(self):
        '''
            If no orgs with links in period, should return None
        '''
        r = Registrar()
        r.save()
        o1 = Organization(registrar=r)
        o1.save()
        o2 = Organization(registrar=r)
        o2.save()
        self.assertEqual(type(most_active_org_in_time_period(r.organizations)), type(None))

    def test_most_active_org_in_time_period_invalid_dates(self):
        '''
            If end date is before start date, should raise an exception
        '''
        r = Registrar()
        r.save()
        now = tz_datetime(timezone.now().year, 1, 1)
        later = tz_datetime(now.year + 1, 1, 1)
        with self.assertRaises(ValueError):
            most_active_org_in_time_period(r.organizations, later, now)

    def test_most_active_org_in_time_period_valid_period(self):
        '''
            Should include links created only in the target year
        '''
        now = tz_datetime(timezone.now().year, 1, 1)
        two_years_ago = tz_datetime(now.year - 2, 1, 1)
        three_years_ago = tz_datetime(now.year - 3, 1, 1)

        r = Registrar()
        r.save()
        o1 = Organization(registrar=r)
        o1.save()
        o2 = Organization(registrar=r)
        o2.save()
        user = LinkUser()
        user.save()
        link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC", "DDDD-DDDD", "EEEE-EEEE"]

        too_early1 = Link(creation_timestamp=three_years_ago, guid=link_pks[0], organization=o1, created_by=user)
        too_early1.save()
        too_early2 = Link(creation_timestamp=three_years_ago, guid=link_pks[1], organization=o1, created_by=user)
        too_early2.save()

        now1 = Link(creation_timestamp=now, guid=link_pks[2], organization=o1, created_by=user)
        now1.save()
        now2 = Link(creation_timestamp=now, guid=link_pks[3], organization=o2, created_by=user)
        now2.save()
        now3 = Link(creation_timestamp=now, guid=link_pks[4], organization=o2, created_by=user)
        now3.save()

        # organization 1 was more active in the past
        self.assertEqual(most_active_org_in_time_period(r.organizations, three_years_ago, two_years_ago), o1)
        # but organization 2 was more active during the period in question
        self.assertEqual(most_active_org_in_time_period(r.organizations, two_years_ago), o2)
        # with a total of three links, organization 1 has been more active over all
        self.assertEqual(most_active_org_in_time_period(r.organizations), o1)

    def test_registrar_most_active_org_this_year(self):
        '''
            Should return the org (whole object)with the most links
            created this year, or None if it has no orgs with links
            created this year.
        '''
        r = Registrar()
        r.save()
        self.assertEqual(type(r.most_active_org_this_year()), type(None))

        o1 = Organization(registrar=r)
        o1.save()
        o2 = Organization(registrar=r)
        o2.save()

        now = tz_datetime(timezone.now().year, 1, 1)
        two_years_ago = tz_datetime(now.year - 2, 1, 1)
        user = LinkUser()
        user.save()
        link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC", "DDDD-DDDD", "EEEE-EEEE", "FFFF-FFFF"]
        too_early = Link(creation_timestamp=two_years_ago, guid=link_pks[0], created_by=user, organization=o1)
        too_early.save()
        self.assertEqual(type(r.most_active_org_this_year()), type(None))

        now1 = Link(creation_timestamp=now, guid=link_pks[1], created_by=user, organization=o1)
        now1.save()
        now2 = Link(creation_timestamp=now, guid=link_pks[2], created_by=user, organization=o1)
        now2.save()
        now3 = Link(creation_timestamp=now, guid=link_pks[3], created_by=user, organization=o2)
        now3.save()

        self.assertEqual(r.most_active_org_this_year(), o1)

        now4 = Link(creation_timestamp=now, guid=link_pks[4], created_by=user, organization=o2)
        now4.save()
        now5 = Link(creation_timestamp=now, guid=link_pks[5], created_by=user, organization=o2)
        now5.save()

        self.assertEqual(r.most_active_org_this_year(), o2)

    #
    # Related to Perma Payments
    #

    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_none_and_no_network_call_if_nonpaying(self, post):
        # also verify that their value of in_trial is unchanged by the call
        for noncustomer in noncustomers():
            in_trial = noncustomer.in_trial
            self.assertIsNone(noncustomer.get_subscription())
            noncustomer.refresh_from_db()
            self.assertEqual(in_trial, noncustomer.in_trial)
            self.assertEqual(post.call_count, 0)


    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_raises_on_non_200(self, post):
        post.return_value.ok = False
        for customer in customers():
            with self.assertRaises(PermaPaymentsCommunicationException):
                customer.get_subscription()
            self.assertEqual(post.call_count, 1)
            post.reset_mock()


    @patch('perma.models.process_perma_payments_transmission', autospec=True)
    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_verifies_transmission_valid(self, post, process):
        post.return_value.status_code = 200
        post.return_value.json.return_value = sentinel.json
        for customer in customers():
            # This will raise an exception further down in the function;
            # we don't care at this point
            with self.assertRaises(Exception):
                customer.get_subscription()
            self.assertEqual(post.call_count, 1)
            process.assert_called_once_with(sentinel.json, FIELDS_REQUIRED_FROM_PERMA_PAYMENTS['get_subscription'])
            post.reset_mock()
            process.reset_mock()


    @patch('perma.models.process_perma_payments_transmission', autospec=True)
    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_raises_if_unexpected_customer_pk(self, post, process):
        post.return_value.status_code = 200
        for customer in customers():
            process.return_value = spoof_pp_response_wrong_pk(customer)
            with self.assertRaises(InvalidTransmissionException):
                customer.get_subscription()
            self.assertEqual(post.call_count, 1)
            post.reset_mock()


    @patch('perma.models.process_perma_payments_transmission', autospec=True)
    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_raises_if_unexpected_registrar_type(self, post, process):
        post.return_value.status_code = 200
        for customer in customers():
            process.return_value = spoof_pp_response_wrong_type(customer)
            with self.assertRaises(InvalidTransmissionException):
                customer.get_subscription()
            self.assertEqual(post.call_count, 1)
            post.reset_mock()


    @patch('perma.models.process_perma_payments_transmission', autospec=True)
    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_no_subscription(self, post, process):
        post.return_value.status_code = 200
        for customer in customers():
            with patch.object(customer, 'credit_for_purchased_links', autospec=True, wraps=True) as credited:
                # artificially set this for the purpose of this test
                customer.cached_subscription_started = timezone.now()
                customer.save()
                customer.refresh_from_db()
                self.assertTrue(customer.cached_subscription_started)

                process.return_value = spoof_pp_response_no_subscription(customer)
                self.assertIsNone(customer.get_subscription())
                self.assertFalse(customer.cached_subscription_started)
                self.assertEqual(post.call_count, 1)
                self.assertEqual(credited.call_count, 0)
                post.reset_mock()


    @patch('perma.models.process_perma_payments_transmission', autospec=True)
    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_no_subscription_purchased_bonus(self, post, process):
        post.return_value.status_code = 200
        for customer in customers():
            with patch.object(customer, 'credit_for_purchased_links', autospec=True, wraps=True) as credited:
                from_pp = spoof_pp_response_no_subscription_two_purchases(customer)
                process.return_value = from_pp
                self.assertIsNone(customer.get_subscription())
                self.assertFalse(customer.cached_subscription_started)
                self.assertEqual(post.call_count, 1)
                credited.assert_called_once_with(from_pp['purchases'])
                post.reset_mock()


    @patch('perma.models.process_perma_payments_transmission', autospec=True)
    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_happy_path_sets_customer_trial_period_to_false(self, post, process):
        post.return_value.status_code = 200
        for customer in [paying_limited_registrar(), paying_user()]:
            # artificially set this for the purpose of this test
            customer.in_trial = True
            customer.cached_subscription_started = None
            customer.save()
            customer.refresh_from_db()
            self.assertTrue(customer.in_trial)
            self.assertFalse(customer.cached_subscription_started)

            response = spoof_pp_response_subscription(customer)
            process.return_value = response
            customer.get_subscription()
            customer.refresh_from_db()

            self.assertFalse(customer.in_trial)
            self.assertTrue(customer.cached_subscription_started)


    @patch('perma.models.process_perma_payments_transmission', autospec=True)
    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_happy_path_no_change_pending(self, post, process):
        post.return_value.status_code = 200
        for customer in [paying_limited_registrar(), paying_user()]:
            with patch.object(customer, 'credit_for_purchased_links', autospec=True, wraps=True) as credited:
                response = spoof_pp_response_subscription(customer)
                process.return_value = response
                subscription = customer.get_subscription()
                customer.refresh_from_db()
                self.assertEqual(customer.cached_subscription_status, response['subscription']['status'])
                self.assertEqual(subscription, {
                    'status': response['subscription']['status'],
                    'link_limit': response['subscription']['link_limit'],
                    'rate': response['subscription']['rate'],
                    'frequency': response['subscription']['frequency'],
                    'paid_through': pp_date_from_post('1970-01-21T00:00:00.000000Z'),
                    'pending_change': None
                })
                self.assertEqual(post.call_count, 1)
                self.assertEqual(credited.call_count, 0)
                post.reset_mock()


    @patch('perma.models.process_perma_payments_transmission', autospec=True)
    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_happy_path_with_pending_change(self, post, process):
        post.return_value.status_code = 200
        for customer in [paying_limited_registrar(), paying_user()]:
            with patch.object(customer, 'credit_for_purchased_links', autospec=True, wraps=True) as credited:
                response = spoof_pp_response_subscription_with_pending_change(customer)
                process.return_value = response
                subscription = customer.get_subscription()
                customer.refresh_from_db()
                self.assertEqual(customer.cached_subscription_status, response['subscription']['status'])
                self.assertEqual(subscription, {
                    'status': response['subscription']['status'],
                    'link_limit': str(customer.link_limit),
                    'rate': str(customer.cached_subscription_rate),
                    'frequency': customer.link_limit_period,
                    'paid_through': pp_date_from_post('9999-01-21T00:00:00.000000Z'),
                    'pending_change': {
                        'rate': response['subscription']['rate'],
                        'link_limit': response['subscription']['link_limit'],
                        'effective': pp_date_from_post(response['subscription']['link_limit_effective_timestamp'])
                    }
                })
                self.assertNotEqual(str(customer.link_limit), response['subscription']['link_limit'])
                self.assertNotEqual(str(customer.cached_subscription_rate), response['subscription']['rate'])
                self.assertEqual(post.call_count, 1)
                self.assertEqual(credited.call_count, 0)
                post.reset_mock()

    ### Annotating Tiers with Prices and Dates

    # check monthly tiers for customers with no subscriptions

    def test_annotate_tier_monthly_no_subscription_first_of_month(self):
        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = None
        for customer in customers():
            tier = {
                'period': 'monthly',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'upgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], now.timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), customer.base_rate * tier['rate_ratio'])
            self.assertEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], next_month)


    def test_annotate_tier_monthly_no_subscription_mid_month(self):
        now = GENESIS.replace(day=16)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = None
        for customer in customers():
            tier = {
                'period': 'monthly',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'upgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], now.timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), (customer.base_rate * tier['rate_ratio'] / 31 * 16).quantize(Decimal('.01')))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], next_month)


    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_monthly_no_subscription_last_of_month(self, is_active):
        is_active.return_value = True

        now = GENESIS.replace(day=31)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = None
        for customer in customers():
            tier = {
                'period': 'monthly',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'upgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], now.timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), (customer.base_rate * tier['rate_ratio'] / 31).quantize(Decimal('.01')))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], next_month)


    # check upgrading/downgrading not allowed if you have a non-active subscription
    # (for instance, on hold due to lapsed payments), whatever the tier

    def test_annotate_tier_change_disallowed_with_inactive_monthly_subscription(self):
        now = GENESIS.replace(day=31)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '0.10',
            'frequency': 'monthly',
            'paid_through': next_month
        }

        for customer in customers():
            for tier in settings.TIERS[customer.customer_type]:
                customer.annotate_tier(tier, subscription, now, next_month, next_year)
                self.assertEqual(tier['type'], 'unavailable')


    def test_annotate_tier_change_disallowed_with_inactive_annual_subscription(self):
        now = GENESIS.replace(day=31)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '0.10',
            'frequency': 'annually',
            'paid_through': next_year
        }

        for customer in customers():
            for tier in settings.TIERS[customer.customer_type]:
                customer.annotate_tier(tier, subscription, now, next_month, next_year)
                self.assertEqual(tier['type'], 'unavailable')


    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_change_disallowed_with_pending_downgrade(self, is_active):
        is_active.return_value = True

        now = GENESIS.replace(day=31)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '0.10',
            'frequency': 'monthly',
            'paid_through': next_year,
            'pending_change': True
        }

        for customer in customers():
            for tier in settings.TIERS[customer.customer_type]:
                customer.annotate_tier(tier, subscription, now, next_month, next_year)
                self.assertEqual(tier['type'], 'unavailable')

    # check upgrade monthly tiers for customers with subscriptions

    def test_annotate_tier_monthly_active_subscription_upgrade_first_of_month(self):
        '''
        Observe, if this change of recurring_amount DOES get picked up by CyberSource
        in time for today's recurring charge, then the customer will be overcharged.
        We would need to refund them tier['amount'].
        '''
        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Current',
            'rate': '0.10',
            'frequency': 'monthly',
            'link_limit': 0
        }
        for customer in customers():
            tier = {
                'period': 'monthly',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'upgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], now.timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), customer.base_rate * tier['rate_ratio'] - Decimal(subscription['rate']))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], next_month)


    def test_annotate_tier_monthly_active_subscription_upgrade_mid_month(self):
        now = GENESIS.replace(day=16)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Current',
            'rate': '0.10',
            'frequency': 'monthly',
            'link_limit': 0
        }
        for customer in customers():
            tier = {
                'period': 'monthly',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'upgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], now.timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), ((customer.base_rate * tier['rate_ratio'] / 31 * 16) - (Decimal(subscription['rate']) / 31 * 16)).quantize(Decimal('.01')))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], next_month)


    def test_annotate_tier_monthly_active_subscription_upgrade_last_of_month(self):
        now = GENESIS.replace(day=31)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Current',
            'rate': '0.10',
            'frequency': 'monthly',
            'link_limit': 0
        }
        for customer in customers():
            tier = {
                'period': 'monthly',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'upgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], now.timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), ((customer.base_rate * tier['rate_ratio'] / 31) - (Decimal(subscription['rate']) / 31 )).quantize(Decimal('.01')))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], next_month)


    # check downgrade monthly tiers for customers with subscriptions, amount and recurring not equal, amount == 0

    def test_annotate_tier_monthly_active_subscription_downgrade_first_of_month(self):
        '''
        Observe, this does NOT affect the current month at all.... too late
        to do without risking overcharging people.
        '''
        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Current',
            'rate': '9999.10',
            'frequency': 'monthly',
            'link_limit': 9999
        }
        for customer in customers():
            tier = {
                'period': 'monthly',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'downgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], next_month.timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), Decimal('0'))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], next_month)


    def test_annotate_tier_monthly_active_subscription_downgrade_mid_month(self):
        now = GENESIS.replace(day=16)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Current',
            'rate': '9999.10',
            'frequency': 'monthly',
            'link_limit': 9999
        }
        for customer in customers():
            tier = {
                'period': 'monthly',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'downgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], next_month.timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), Decimal('0'))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], next_month)


    def test_annotate_tier_monthly_active_subscription_downgrade_last_of_month(self):
        now = GENESIS.replace(day=31)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Current',
            'rate': '9999.10',
            'frequency': 'monthly',
            'link_limit': 9999
        }
        for customer in customers():
            tier = {
                'period': 'monthly',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'downgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], next_month.timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), Decimal('0'))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], next_month)


    # check annual tiers for customers with no subscriptions

    def test_annotate_tier_annually_no_subscription(self):
        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = None
        for customer in customers():
            tier = {
                'period': 'annually',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'upgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], now.timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), customer.base_rate * tier['rate_ratio'])
            self.assertEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], next_year)


    # check upgrade annual tiers for customers with current subscriptions, amount and recurring not equal, amount correct

    def test_annotate_tier_annually_active_subscription_upgrade_same_day(self):
        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Current',
            'rate': '0.10',
            'frequency': 'annually',
            'paid_through': next_year,
            'link_limit': 0

        }
        for customer in customers():
            tier = {
                'period': 'annually',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'upgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], now.timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), customer.base_rate * tier['rate_ratio'] - Decimal(subscription['rate']))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], subscription['paid_through'])


    def test_annotate_tier_annually_active_subscription_upgrade_midyear(self):
        now = GENESIS.replace(day=30, month=12)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Current',
            'rate': '0.10',
            'frequency': 'annually',
            'paid_through': today_next_year(GENESIS.replace(day=1)),
            'link_limit': 0

        }
        for customer in customers():
            tier = {
                'period': 'annually',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'upgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], now.timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), ((customer.base_rate * tier['rate_ratio'] / 365 * 2) - (Decimal(subscription['rate']) / 365 * 2 )).quantize(Decimal('.01')))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], subscription['paid_through'])


    def test_annotate_tier_annually_active_subscription_upgrade_on_anniversary(self):
        '''
        Observe, if this change of recurring_amount DOES NOT get picked up by CyberSource
        in time for today's recurring charge, then the customer will not be charged
        for this upgrade for a whole year LOL!
        We'll need to manually charge them the difference between the tiers.
        Why do I have this working the opposite way for months and years?
        '''
        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Current',
            'rate': '0.10',
            'frequency': 'annually',
            'paid_through': now,
            'link_limit': 0

        }
        for customer in customers():
            tier = {
                'period': 'annually',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'upgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], now.timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), Decimal('0.00'))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], subscription['paid_through'])


    # check downgrade annual tiers for customers with subscriptions

    def test_annotate_tier_annually_active_subscription_downgrade_same_day(self):
        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Current',
            'rate': '9999.10',
            'frequency': 'annually',
            'paid_through': next_year,
            'link_limit': 9999

        }
        for customer in customers():
            tier = {
                'period': 'annually',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'downgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], subscription['paid_through'].timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), Decimal('0.00'))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], subscription['paid_through'])


    def test_annotate_tier_annually_active_subscription_downgrade_midyear(self):
        now = GENESIS.replace(day=30, month=12)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Current',
            'rate': '9999.10',
            'frequency': 'annually',
            'paid_through': today_next_year(GENESIS.replace(day=1)),
            'link_limit': 9999

        }
        for customer in customers():
            tier = {
                'period': 'annually',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'downgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], subscription['paid_through'].timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), Decimal('0.00'))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], subscription['paid_through'])


    def test_annotate_tier_annually_active_subscription_downgrade_on_anniversary(self):
        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Current',
            'rate': '9999.10',
            'frequency': 'annually',
            'paid_through': now,
            'link_limit': 9999

        }
        for customer in customers():
            tier = {
                'period': 'annually',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'downgrade')
            self.assertEqual(tier['link_limit_effective_timestamp'], subscription['paid_through'].timestamp())
            self.assertEqual(Decimal(tier['todays_charge']), Decimal('0.00'))
            self.assertNotEqual(tier['recurring_amount'], tier['todays_charge'])
            self.assertEqual(tier['next_payment'], subscription['paid_through'])


    # check warnings

    def test_annotate_tier_hides_more_expensive_option_from_grandfathered_customer(self):
        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        for customer in customers():
            subscription = {
                'status': 'Current',
                'rate': str(customer.base_rate * 5),
                'frequency': 'annually',
                'paid_through': now,
                'link_limit': 500
            }
            tier = {
                'period': 'annually',
                'link_limit': 500,
                'rate_ratio': 10
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'unavailable')


    def test_annotate_tier_hides_similar_tier_from_higher_paying_customer(self):
        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        for customer in customers():
            subscription = {
                'status': 'Current',
                'rate': str(customer.base_rate * 10),
                'frequency': 'annually',
                'paid_through': now,
                'link_limit': 500
            }
            tier = {
                'period': 'annually',
                'link_limit': 500,
                'rate_ratio': 5
            }
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            self.assertEqual(tier['type'], 'unavailable')


    @override_settings(TIERS=FAKE_TIERS)
    @patch('perma.models.LinkUser.annotate_tier', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_get_subscription_info_normal(self, get_subscription, annotate_tier):
        now = GENESIS.replace(day=1)
        customer = paying_user()
        subscription = {
            'status': 'Current',
            'rate': str(customer.base_rate * 5),
            'frequency': 'monthly',
            'paid_through': now.replace(day=15),
            'link_limit': 500
        }
        get_subscription.return_value = subscription
        account = customer.get_subscription_info(now)
        self.assertIn('customer', account)
        self.assertEqual(subscription, account['subscription'])
        self.assertIn('tiers', account)
        self.assertEqual(annotate_tier.call_count, len(settings.TIERS[customer.customer_type]))
        self.assertIn('can_change_tiers', account)

    @patch('perma.models.LinkUser.annotate_tier', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_get_subscription_info_downgrade_pending(self, get_subscription, annotate_tier):
        now = GENESIS.replace(day=1)
        customer = paying_user()
        subscription = {
            'status': 'Current',
            'rate': str(customer.base_rate * 5),
            'frequency': 'monthly',
            'paid_through': now.replace(day=15),
            'link_limit': 500,
            'pending_change': {
                'rate': str(customer.base_rate * 1),
                'link_limit': 100,
                'effective': now.replace(day=31)
            }
        }
        get_subscription.return_value = subscription
        account = customer.get_subscription_info(now)
        self.assertIn('customer', account)
        self.assertEqual(subscription, account['subscription'])
        self.assertEqual(len(account['tiers']), 1)
        self.assertEqual(account['tiers'][0]['limit'], subscription['link_limit'])
        self.assertEqual(account['tiers'][0]['rate'], subscription['rate'])
        self.assertEqual(account['tiers'][0]['required_fields']['amount'], '0.00')
        self.assertEqual(account['tiers'][0]['required_fields']['link_limit_effective_timestamp'], now.timestamp())
        self.assertEqual(annotate_tier.call_count, 0)
        self.assertTrue(account['can_change_tiers'])


    def test_subscription_is_active_with_active_status(self):
        for status in ACTIVE_SUBSCRIPTION_STATUSES:
            self.assertTrue(subscription_is_active({
                'status': status,
                'paid_through': 'some datetime'
            }))

    def test_subscription_is_active_with_paid_up_canceled(self):
        self.assertTrue(subscription_is_active(active_cancelled_subscription()))

    def test_subscription_is_active_with_expired_canceled(self):
        self.assertFalse(subscription_is_active(expired_cancelled_subscription()))

    #
    # crediting users for one-time purchases
    #

    def credit_a_customer_for_purchases(self, post):
        customer = paying_user()
        purchases = spoof_pp_response_no_subscription_two_purchases(customer)["purchases"]
        credited = customer.credit_for_purchased_links(purchases)
        self.assertEqual(post.call_count, 2)
        return credited


    @patch('perma.models.requests.post', autospec=True)
    def test_credit_for_purchased_links_increments_for_all(self, post):
        post.return_value.ok = True
        credited = self.credit_a_customer_for_purchases(post)
        self.assertEqual(credited, 60)


    @patch('perma.models.requests.post', autospec=True)
    def test_credit_for_purchased_links_reverses_if_acknoledgment_fails(self, post):
        post.return_value.ok = False
        credited = self.credit_a_customer_for_purchases(post)
        self.assertEqual(credited, 0)
        self.assertEqual(post.call_count, 2)


    #
    # Bonus packages info
    #

    @patch.object(perma.models, 'datetime')
    @patch('perma.models.prep_for_perma_payments', autospec=True)
    def test_get_bonus_packages(self, prep, mock_datetime):
        customer = paying_user()
        perma.models.datetime.utcnow.return_value = GENESIS
        prep.return_value.decode.return_value = sentinel.string

        packages = customer.get_bonus_packages()

        prep.assert_any_call({'timestamp': 0.0, 'customer_pk': customer.pk, 'customer_type': 'Individual', 'amount': '15.00', 'link_quantity': 10})
        prep.assert_any_call({'timestamp': 0.0, 'customer_pk': customer.pk, 'customer_type': 'Individual', 'amount': '30.00', 'link_quantity': 100})
        prep.assert_any_call({'timestamp': 0.0, 'customer_pk': customer.pk, 'customer_type': 'Individual', 'amount': '125.00', 'link_quantity': 500})
        self.assertEqual(packages, [
            {
                'amount': '15.00',
                'link_quantity': 10,
                'unit_cost': 1.5,
                'encrypted_data': sentinel.string
            }, {
                'amount': '30.00',
                'link_quantity': 100,
                'unit_cost': 0.3,
                'encrypted_data': sentinel.string
            }, {
                'amount': '125.00',
                'link_quantity': 500,
                'unit_cost': 0.25,
                'encrypted_data': sentinel.string
            }
        ])


    #
    # Link limit / subscription related tests for individual (non-sponsored) users
    #

    def test_new_user_gets_default_link_limit(self):
        u = LinkUser()
        u.save()
        self.assertEqual(u.link_limit, settings.DEFAULT_CREATE_LIMIT)
        self.assertEqual(u.link_limit_period, settings.DEFAULT_CREATE_LIMIT_PERIOD)


    def test_one_time_link_limit(self):
        u = user_with_links()
        self.assertFalse(u.unlimited)
        self.assertFalse(u.cached_subscription_started)
        self.assertEqual(u.links_remaining_in_period('once', 6), 1)
        self.assertEqual(u.links_remaining_in_period('once', 5), 0)


    @patch('perma.models.timezone', autospec=True)
    def test_one_time_link_limit_with_midmonth_subscription1(self, mocked_timezone):
        fifteenth_of_month = timezone.now().replace(day=15)
        mocked_timezone.now.return_value = fifteenth_of_month

        u = user_with_links_this_month_before_the_15th()
        u.cached_subscription_started = fifteenth_of_month
        u.save()

        self.assertFalse(u.unlimited)
        self.assertEqual(u.links_remaining_in_period('once', 6), 6)
        self.assertEqual(u.links_remaining_in_period('once', 5), 5)
        self.assertEqual(mocked_timezone.now.call_count, 2)


    @patch('perma.models.timezone', autospec=True)
    def test_one_time_link_limit_with_midmonth_subscription2(self, mocked_timezone):
        fifteenth_of_month = timezone.now().replace(day=15)
        fifth_of_month = timezone.now().replace(day=5)
        mocked_timezone.now.return_value = fifteenth_of_month

        u = user_with_links_this_month_before_the_15th()
        u.cached_subscription_started = fifth_of_month
        u.save()

        self.assertFalse(u.unlimited)
        self.assertEqual(u.links_remaining_in_period('once', 6), 5)
        self.assertEqual(u.links_remaining_in_period('once', 5), 4)
        self.assertEqual(mocked_timezone.now.call_count, 2)


    def test_monthly_link_limit(self):
        u = user_with_links()
        self.assertFalse(u.unlimited)
        self.assertEqual(u.links_remaining_in_period('monthly', 3), 1)
        self.assertEqual(u.links_remaining_in_period('monthly', 2), 0)


    @patch('perma.models.timezone', autospec=True)
    def test_monthly_link_limit_with_midmonth_subscription1(self, mocked_timezone):
        fifteenth_of_month = timezone.now().replace(day=15)
        mocked_timezone.now.return_value = fifteenth_of_month

        u = user_with_links_this_month_before_the_15th()
        u.cached_subscription_started = fifteenth_of_month
        u.save()

        self.assertFalse(u.unlimited)
        self.assertEqual(u.links_remaining_in_period('monthly', 3), 3)
        self.assertEqual(u.links_remaining_in_period('monthly', 2), 2)
        self.assertEqual(mocked_timezone.now.call_count, 2)


    @patch('perma.models.timezone', autospec=True)
    def test_monthly_link_limit_with_midmonth_subscription2(self, mocked_timezone):
        fifteenth_of_month = timezone.now().replace(day=15)
        fifth_of_month = timezone.now().replace(day=5)
        mocked_timezone.now.return_value = fifteenth_of_month

        u = user_with_links_this_month_before_the_15th()
        u.cached_subscription_started = fifth_of_month
        u.save()

        self.assertFalse(u.unlimited)
        self.assertEqual(u.links_remaining_in_period('monthly', 3), 2)
        self.assertEqual(u.links_remaining_in_period('monthly', 2), 1)
        self.assertEqual(mocked_timezone.now.call_count, 2)


    def test_annual_link_limit(self):
        u = user_with_links()
        self.assertFalse(u.unlimited)
        self.assertEqual(u.links_remaining_in_period('annually', 4), 1)
        self.assertEqual(u.links_remaining_in_period('annually', 3), 0)


    def test_unlimited_user_link_limit(self):
        u = user_with_links()
        u.unlimited = True
        self.assertEqual(u.links_remaining_in_period('once', 1), float("inf"))
        self.assertEqual(u.links_remaining_in_period('monthly', 1), float("inf"))
        self.assertEqual(u.links_remaining_in_period('annually', 1), float("inf"))
        u.unlimited = False
        self.assertNotEqual(u.links_remaining_in_period('once', 1), float("inf"))
        self.assertNotEqual(u.links_remaining_in_period('monthly', 1), float("inf"))
        self.assertNotEqual(u.links_remaining_in_period('annually', 1), float("inf"))


    def test_override_for_unlimited_user_link_limit(self):
        u = user_with_links()
        u.unlimited = True
        self.assertNotEqual(u.links_remaining_in_period('once', 1, False), float("inf"))
        self.assertNotEqual(u.links_remaining_in_period('monthly', 1, False), float("inf"))
        self.assertNotEqual(u.links_remaining_in_period('annually', 1, False), float("inf"))


    @patch('perma.models.LinkUser.get_links_remaining', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_allowed_if_nonpaying_and_under_limit(self, get_subscription, get_links_remaining):
        get_links_remaining.return_value = (1, 'some period', 0)
        user = nonpaying_user()
        self.assertTrue(user.link_creation_allowed())
        self.assertEqual(get_subscription.call_count, 0)
        self.assertEqual(get_links_remaining.call_count, 1)


    @patch('perma.models.LinkUser.get_links_remaining', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_denied_if_nonpaying_and_over_limit(self, get_subscription, get_links_remaining):
        get_links_remaining.return_value = (0, 'some period', 0)
        user = nonpaying_user()
        self.assertFalse(user.link_creation_allowed())
        self.assertEqual(get_subscription.call_count, 0)
        self.assertEqual(get_links_remaining.call_count, 1)


    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_allowed_checks_cached_if_pp_down(self, get_subscription, is_active):
        get_subscription.side_effect = PermaPaymentsCommunicationException
        customer = paying_user()
        customer.link_creation_allowed()
        get_subscription.assert_called_once_with(customer)
        is_active.assert_called_once_with({
            'status': 'Sentinel Status',
            'paid_through': GENESIS
        })


    @patch('perma.models.LinkUser.links_remaining_in_period', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_allowed_if_no_subscription_and_under_limit(self, get_subscription, links_remaining_in_period):
        get_subscription.return_value = None
        user = paying_user()
        links_remaining_in_period.return_value = 1
        self.assertTrue(user.link_creation_allowed())
        self.assertEqual(get_subscription.call_count, 1)
        links_remaining_in_period.assert_called_once_with(user, settings.DEFAULT_CREATE_LIMIT_PERIOD, settings.DEFAULT_CREATE_LIMIT, False)


    @patch('perma.models.LinkUser.links_remaining_in_period', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_denied_if_no_subscription_and_over_limit(self, get_subscription, links_remaining_in_period):
        get_subscription.return_value = None
        user = paying_user()
        links_remaining_in_period.return_value = 0
        self.assertFalse(user.link_creation_allowed())
        self.assertEqual(get_subscription.call_count, 1)
        links_remaining_in_period.assert_called_once_with(user, settings.DEFAULT_CREATE_LIMIT_PERIOD, settings.DEFAULT_CREATE_LIMIT, False)


    @patch('perma.models.LinkUser.links_remaining_in_period', autospec=True)
    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.subscription_has_problem', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_disallowed_if_subscription_inactive_and_over_limit(self, get_subscription, has_problem, is_active, links_remaining_in_period):
        get_subscription.return_value = sentinel.subscription
        is_active.return_value = False
        has_problem.return_value = True
        user = paying_user()
        links_remaining_in_period.return_value = 0
        self.assertFalse(user.link_creation_allowed())
        get_subscription.assert_called_once_with(user)
        is_active.assert_called_once_with(sentinel.subscription)
        links_remaining_in_period.assert_called_once_with(user, settings.DEFAULT_CREATE_LIMIT_PERIOD, settings.DEFAULT_CREATE_LIMIT, False)


    @patch('perma.models.LinkUser.links_remaining_in_period', autospec=True)
    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.subscription_has_problem', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_allowed_if_subscription_inactive_and_under_limit(self, get_subscription, has_problem, is_active, links_remaining_in_period):
        get_subscription.return_value = sentinel.subscription
        is_active.return_value = False
        has_problem.return_value = True
        user = paying_user()
        links_remaining_in_period.return_value = user.link_limit + 1
        self.assertTrue(user.link_creation_allowed())
        get_subscription.assert_called_once_with(user)
        is_active.assert_called_once_with(sentinel.subscription)
        links_remaining_in_period.assert_called_once_with(user, settings.DEFAULT_CREATE_LIMIT_PERIOD, settings.DEFAULT_CREATE_LIMIT, False)


    @patch('perma.models.LinkUser.links_remaining_in_period', autospec=True)
    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_allowed_if_subscription_active_and_under_limit(self, get_subscription, is_active, links_remaining_in_period):
        get_subscription.return_value = sentinel.subscription
        is_active.return_value = True
        links_remaining_in_period.return_value = 1
        customer = paying_user()
        self.assertTrue(customer.link_creation_allowed())
        get_subscription.assert_called_once_with(customer)
        is_active.assert_called_once_with(sentinel.subscription)
        links_remaining_in_period.assert_called_once_with(customer, customer.link_limit_period, customer.link_limit)


    @patch('perma.models.LinkUser.links_remaining_in_period', autospec=True)
    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_disallowed_if_subscription_active_and_under_limit(self, get_subscription, is_active, links_remaining_in_period):
        get_subscription.return_value = sentinel.subscription
        is_active.return_value = True
        links_remaining_in_period.return_value = 0
        customer = paying_user()
        self.assertFalse(customer.link_creation_allowed())
        get_subscription.assert_called_once_with(customer)
        is_active.assert_called_once_with(sentinel.subscription)
        links_remaining_in_period.assert_called_once_with(customer, customer.link_limit_period, customer.link_limit)


    #
    # Limk limit for sponsored users
    #

    def test_sponsored_links_not_counted_against_personal_total(self):
        sponsored_user = LinkUser.objects.get(email='test_sponsored_user@example.com')
        self.assertEqual(sponsored_user.get_links_remaining()[0], 9)
        link = Link(creation_timestamp=timezone.now().replace(day=1), guid="AAAA-AAAA", created_by=sponsored_user)
        link.save()
        self.assertEqual(sponsored_user.get_links_remaining()[0], 8)
        link.move_to_folder_for_user(sponsored_user.sponsorships.first().folders.first(), sponsored_user)
        self.assertEqual(sponsored_user.get_links_remaining()[0], 9)


    #
    # Link limits and bonus links
    #

    def test_bonus_links_arent_counted_against_personal_total(self):
        user = LinkUser()
        user.save()
        remaining, _, bonus = user.get_links_remaining()

        personal_links = 5
        bonus_links = 2
        for _ in range(personal_links):
            Link(created_by=user).save()
        for _ in range(bonus_links):
            Link(created_by=user, bonus_link=True).save()
        now_remaining, _, now_bonus = user.get_links_remaining()
        self.assertEqual(now_remaining, remaining - personal_links)
        self.assertNotEqual(now_remaining, remaining - personal_links - bonus_links)


    #
    # Link limit / subscription related tests for registrars
    #

    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_registrar_link_creation_always_allowed_if_nonpaying(self, get_subscription):
        registrar = nonpaying_registrar()
        self.assertTrue(registrar.link_creation_allowed())
        self.assertEqual(get_subscription.call_count, 0)

    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_registrar_link_creation_allowed_checks_cached_if_pp_down(self, get_subscription, is_active):
        get_subscription.side_effect = PermaPaymentsCommunicationException
        customer = paying_registrar()
        customer.link_creation_allowed()
        get_subscription.assert_called_once_with(customer)
        is_active.assert_called_once_with({
            'status': 'Sentinel Status',
            'paid_through': GENESIS
        })

    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_registrar_link_creation_disallowed_if_no_subscription(self, get_subscription):
        get_subscription.return_value = None
        r = paying_registrar()
        self.assertFalse(r.link_creation_allowed())
        get_subscription.assert_called_once_with(r)

    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.subscription_has_problem', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_registrar_link_creation_disallowed_if_subscription_inactive(self, get_subscription, has_problem, is_active):
        get_subscription.return_value = sentinel.subscription
        is_active.return_value = False
        has_problem.return_value = True
        registrar = paying_registrar()
        self.assertFalse(registrar.link_creation_allowed())
        get_subscription.assert_called_once_with(registrar)
        is_active.assert_called_once_with(sentinel.subscription)

    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_registrar_link_creation_allowed_if_subscription_active(self, get_subscription, is_active):
        get_subscription.return_value = sentinel.subscription
        is_active.return_value = True
        customer = paying_registrar()
        self.assertTrue(customer.link_creation_allowed())
        get_subscription.assert_called_once_with(customer)
        is_active.assert_called_once_with(sentinel.subscription)

    def test_renaming_registrar_renames_top_level_sponsored_folders(self):
        new_name = 'A New Name'
        registrar = Registrar.objects.get(id=1)
        sponsored_folders = Folder.objects.filter(sponsored_by=registrar).prefetch_related('parent')
        self.assertTrue(registrar.name != new_name and sponsored_folders)
        for folder in sponsored_folders:
            if folder.parent.is_sponsored_root_folder:
                self.assertEqual(folder.name, registrar.name)
            else:
                self.assertNotEqual(folder.name, registrar.name)
        registrar.name = new_name
        registrar.save()
        registrar.refresh_from_db()
        sponsored_folders = sponsored_folders.all()  # hack to refresh queryset
        self.assertTrue(registrar.name == new_name and sponsored_folders)
        for folder in sponsored_folders:
            if folder.parent.is_sponsored_root_folder:
                self.assertEqual(folder.name, registrar.name)
            else:
                self.assertNotEqual(folder.name, registrar.name)


    #
    # Moving bonus links around
    #

    def test_move_bonus_link_to_another_personal_subfolder(self):
        user, bonus_link = complex_user_with_bonus_link()
        subfolder = user.folders.get(name="Subfolder")

        # establish baseline
        links_remaining, _ , bonus_links = user.get_links_remaining()
        self.assertEqual(links_remaining, 2)
        self.assertEqual(bonus_links, 0)

        bonus_link.move_to_folder_for_user(subfolder, user)
        user.refresh_from_db()

        # assert that nothing changed
        links_remaining, _ , bonus_links = user.get_links_remaining()
        self.assertEqual(links_remaining, 2)
        self.assertEqual(bonus_links, 0)


    def test_move_bonus_link_to_sponsored_folder(self):
        user, bonus_link = complex_user_with_bonus_link()
        sponsored_folder = user.folders.get(name="Test Library")

        # establish baseline
        links_remaining, _ , bonus_links = user.get_links_remaining()
        self.assertEqual(links_remaining, 2)
        self.assertEqual(bonus_links, 0)

        bonus_link.move_to_folder_for_user(sponsored_folder, user)
        user.refresh_from_db()

        # the user should be credited for the bonus link
        links_remaining, _ , bonus_links = user.get_links_remaining()
        self.assertEqual(links_remaining, 2)
        self.assertEqual(bonus_links, 1)

        # the link should no longer be a bonus link
        bonus_link.refresh_from_db()
        self.assertFalse(bonus_link.bonus_link)


    def test_move_bonus_link_to_org_folder(self):
        user, bonus_link = complex_user_with_bonus_link()
        org_folder = Folder.objects.get(name="Test Journal")

        # establish baseline
        links_remaining, _ , bonus_links = user.get_links_remaining()
        self.assertEqual(links_remaining, 2)
        self.assertEqual(bonus_links, 0)

        bonus_link.move_to_folder_for_user(org_folder, user)
        user.refresh_from_db()

        # the user should be credited for the bonus link
        links_remaining, _ , bonus_links = user.get_links_remaining()
        self.assertEqual(links_remaining, 2)
        self.assertEqual(bonus_links, 1)

        # the link should no longer be a bonus link
        bonus_link.refresh_from_db()
        self.assertFalse(bonus_link.bonus_link)


    def test_move_subfolder_with_bonus_links_to_sponsored_folder(self):
        user, bonus_link = complex_user_with_bonus_link(in_subfolder=True)
        subfolder = user.folders.get(name="Subfolder")
        sponsored_folder = user.folders.get(name="Test Library")

        # establish baseline
        links_remaining, _ , bonus_links = user.get_links_remaining()
        self.assertEqual(links_remaining, 2)
        self.assertEqual(bonus_links, 0)

        subfolder.parent = sponsored_folder
        subfolder.save()
        user.refresh_from_db()

        # the user should be credited for the bonus link
        links_remaining, _ , bonus_links = user.get_links_remaining()
        self.assertEqual(links_remaining, 2)
        self.assertEqual(bonus_links, 1)

        # the link should no longer be a bonus link
        bonus_link.refresh_from_db()
        self.assertFalse(bonus_link.bonus_link)


    def test_move_subfolder_with_bonus_links_to_org_folder(self):
        user, bonus_link = complex_user_with_bonus_link(in_subfolder=True)
        subfolder = user.folders.get(name="Subfolder")
        org_folder = Folder.objects.get(name="Test Journal")

        # establish baseline
        links_remaining, _ , bonus_links = user.get_links_remaining()
        self.assertEqual(links_remaining, 2)
        self.assertEqual(bonus_links, 0)

        subfolder.parent = org_folder
        subfolder.save()
        user.refresh_from_db()

        # the user should be credited for the bonus link
        links_remaining, _ , bonus_links = user.get_links_remaining()
        self.assertEqual(links_remaining, 2)
        self.assertEqual(bonus_links, 1)

        # the link should no longer be a bonus link
        bonus_link.refresh_from_db()
        self.assertFalse(bonus_link.bonus_link)
