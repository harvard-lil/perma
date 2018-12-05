from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

from mock import patch, sentinel

from perma.exceptions import PermaPaymentsCommunicationException, InvalidTransmissionException
from perma.models import (
    ACTIVE_SUBSCRIPTION_STATUSES,
    FIELDS_REQUIRED_FROM_PERMA_PAYMENTS,
    Link, LinkUser, Organization,Registrar,
    link_count_in_time_period,
    most_active_org_in_time_period,
    subscription_is_active
)
from perma.utils import pp_date_from_post, tz_datetime, first_day_of_next_month, today_next_year

from .utils import PermaTestCase


# Fixtures

GENESIS = datetime.fromtimestamp(0).replace(tzinfo=timezone.utc)

def nonpaying_registrar():
    registrar = Registrar()
    registrar.save()
    assert registrar.nonpaying
    return registrar

def paying_registrar():
    registrar = Registrar(
        nonpaying=False,
        cached_subscription_status="Sentinel Status",
        cached_paid_through="1970-01-21T00:00:00.000000Z",
        base_rate=Decimal(100.00)
    )
    registrar.save()
    assert not registrar.nonpaying
    return registrar

def nonpaying_user():
    user = LinkUser()
    user.save()
    assert user.nonpaying
    return user

def paying_user():
    user = LinkUser(
        nonpaying=False,
        cached_subscription_status="Sentinel Status",
        cached_paid_through="1970-01-21T00:00:00.000000Z",
        base_rate=Decimal(100.00)
    )
    user.save()
    assert not user.nonpaying
    return user

def customers():
    return [paying_registrar(), paying_user()]

def noncustomers():
    return [nonpaying_registrar(), nonpaying_user()]

def user_with_links():
    # a user with 6 links, made at intervals
    user = LinkUser()
    user.save()
    now = timezone.now()
    today = now.replace(day=5)
    earlier_this_month = today.replace(day=1)
    last_calendar_year = today - relativedelta(years=1)
    within_the_last_year = now - relativedelta(months=6)
    over_a_year_ago = today - relativedelta(years=1, days=2)
    three_years_ago = today - relativedelta(years=3)
    links = [
        Link(creation_timestamp=today, guid="AAAA-AAAA", created_by=user),
        Link(creation_timestamp=earlier_this_month, guid="BBBB-BBBB", created_by=user),
        Link(creation_timestamp=last_calendar_year, guid="CCCC-CCCC", created_by=user),
        Link(creation_timestamp=within_the_last_year, guid="DDDD-DDDDD", created_by=user),
        Link(creation_timestamp=over_a_year_ago, guid="EEEE-EEEE", created_by=user),
        Link(creation_timestamp=three_years_ago, guid="FFFF-FFFF", created_by=user),
    ]
    for link in links:
        link.save()
    return user

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
        "subscription": None
    }

def spoof_pp_response_subscription(customer):
    return {
        "customer_pk": customer.pk,
        "customer_type": customer.customer_type,
        "subscription": {
            "status": "Sentinel Status",
            "rate": "9999.99",
            "frequency": "Sentinel Frequency",
            "paid_through": "1970-01-21T00:00:00.000000Z",
            "link_limit_effective_timestamp": "1970-01-21T00:00:00.000000Z",
            "link_limit": "unlimited"

        }
    }

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
        for noncustomer in noncustomers():
            self.assertIsNone(noncustomer.get_subscription())
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
            process.return_value = spoof_pp_response_no_subscription(customer)
            self.assertIsNone(customer.get_subscription())
            self.assertEqual(post.call_count, 1)
            post.reset_mock()


    @patch('perma.models.process_perma_payments_transmission', autospec=True)
    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_happy_path(self, post, process):
        post.return_value.status_code = 200
        for customer in customers():
            response = spoof_pp_response_subscription(customer)
            process.return_value = response
            subscription = customer.get_subscription()
            self.assertEqual(customer.cached_subscription_status, response['subscription']['status'])
            self.assertEqual(subscription, {
                'status': response['subscription']['status'],
                'rate': response['subscription']['rate'],
                'frequency': response['subscription']['frequency'],
                'paid_through': pp_date_from_post('1970-01-21T00:00:00.000000Z')
            })
            self.assertEqual(post.call_count, 1)
            post.reset_mock()


    # check monthly tiers for customers with no subscriptions

    def test_annotate_tier_monthly_no_subscription_first_of_month(self):
        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = None
        for customer in noncustomers():
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
        for customer in noncustomers():
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
        for customer in noncustomers():
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

    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_change_disallowed_with_inactive_monthly_subscription(self, is_active):
        is_active.return_value = False

        now = GENESIS.replace(day=31)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '0.10',
            'frequency': 'monthly',
            'paid_through': next_month
        }

        for customer in noncustomers():
            for tier in settings.TIERS[customer.customer_type]:
                customer.annotate_tier(tier, subscription, now, next_month, next_year)
                self.assertEqual(tier['type'], 'unavailable')


    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_change_disallowed_with_inactive_annual_subscription(self, is_active):
        is_active.return_value = False

        now = GENESIS.replace(day=31)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '0.10',
            'frequency': 'annually',
            'paid_through': next_year
        }

        for customer in noncustomers():
            for tier in settings.TIERS[customer.customer_type]:
                customer.annotate_tier(tier, subscription, now, next_month, next_year)
                self.assertEqual(tier['type'], 'unavailable')



    # check upgrade monthly tiers for customers with subscriptions

    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_monthly_active_subscription_upgrade_first_of_month(self, is_active):
        '''
        Observe, if this change of recurring_amount DOES get picked up by CyberSource
        in time for today's recurring charge, then the customer will be overcharged.
        We would need to refund them tier['amount']. Let's hope Cybersource is
        smart enough not to do that......
        '''
        is_active.return_value = True

        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '0.10',
            'frequency': 'monthly'
        }
        for customer in noncustomers():
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


    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_monthly_active_subscription_upgrade_mid_month(self, is_active):
        is_active.return_value = True

        now = GENESIS.replace(day=16)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '0.10',
            'frequency': 'monthly'
        }
        for customer in noncustomers():
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


    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_monthly_active_subscription_upgrade_last_of_month(self, is_active):
        is_active.return_value = True

        now = GENESIS.replace(day=31)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '0.10',
            'frequency': 'monthly'
        }
        for customer in noncustomers():
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

    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_monthly_active_subscription_downgrade_first_of_month(self, is_active):
        '''
        Observe, this does NOT affect the current month at all.... too late
        to do without risking overcharging people.
        '''
        is_active.return_value = True

        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '9999.10',
            'frequency': 'monthly'
        }
        for customer in noncustomers():
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


    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_monthly_active_subscription_downgrade_mid_month(self, is_active):
        is_active.return_value = True

        now = GENESIS.replace(day=16)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '9999.10',
            'frequency': 'monthly'
        }
        for customer in noncustomers():
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


    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_monthly_active_subscription_downgrade_last_of_month(self, is_active):
        is_active.return_value = True

        now = GENESIS.replace(day=31)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '9999.10',
            'frequency': 'monthly'
        }
        for customer in noncustomers():
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
        for customer in noncustomers():
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

    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_annually_active_subscription_upgrade_same_day(self, is_active):
        is_active.return_value = True

        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '0.10',
            'frequency': 'annually',
            'paid_through': next_year

        }
        for customer in noncustomers():
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


    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_annually_active_subscription_upgrade_midyear(self, is_active):
        is_active.return_value = True

        now = GENESIS.replace(day=30, month=12)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '0.10',
            'frequency': 'annually',
            'paid_through': today_next_year(GENESIS.replace(day=1))

        }
        for customer in noncustomers():
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


    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_annually_active_subscription_upgrade_on_anniversary(self, is_active):
        '''
        Observe, if this change of recurring_amount DOES NOT get picked up by CyberSource
        in time for today's recurring charge, then the customer will not be charged
        for this upgrade for a whole year LOL!
        We'll need to manually charge them the difference between the tiers.
        Why do I have this working the opposite way for months and years?
        '''
        is_active.return_value = True

        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '0.10',
            'frequency': 'annually',
            'paid_through': now

        }
        for customer in noncustomers():
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

    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_annually_active_subscription_downgrade_same_day(self, is_active):
        is_active.return_value = True

        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '9999.10',
            'frequency': 'annually',
            'paid_through': next_year

        }
        for customer in noncustomers():
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


    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_annually_active_subscription_downgrade_midyear(self, is_active):
        is_active.return_value = True

        now = GENESIS.replace(day=30, month=12)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '9999.10',
            'frequency': 'annually',
            'paid_through': today_next_year(GENESIS.replace(day=1))

        }
        for customer in noncustomers():
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


    @patch('perma.models.subscription_is_active', autospec=True)
    def test_annotate_tier_annually_active_subscription_downgrade_on_anniversary(self, is_active):
        is_active.return_value = True

        now = GENESIS.replace(day=1)
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = {
            'status': 'Sentinel Status',
            'rate': '9999.10',
            'frequency': 'annually',
            'paid_through': now

        }
        for customer in noncustomers():
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


    # Does this have to be tested? It's important, but.....
    # def test_get_subscription_info(self, get_subscription):
    #     pass

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
        self.assertEqual(u.links_remaining_in_period('once', 7), 1)
        self.assertEqual(u.links_remaining_in_period('once', 6), 0)


    def test_monthly_link_limit(self):
        u = user_with_links()
        self.assertFalse(u.unlimited)
        self.assertEqual(u.links_remaining_in_period('monthly', 3), 1)
        self.assertEqual(u.links_remaining_in_period('monthly', 2), 0)


    def test_annual_link_limit(self):
        '''
        Why is this passing locally and failing on Travis?
        '''
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
        get_links_remaining.return_value = (1, 'some period')
        user = nonpaying_user()
        self.assertTrue(user.link_creation_allowed())
        self.assertEqual(get_subscription.call_count, 0)
        self.assertEqual(get_links_remaining.call_count, 1)


    @patch('perma.models.LinkUser.get_links_remaining', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_denied_if_nonpaying_and_over_limit(self, get_subscription, get_links_remaining):
        get_links_remaining.return_value = (0, 'some period')
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
            'paid_through': '1970-01-21T00:00:00.000000Z'
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
            'paid_through': '1970-01-21T00:00:00.000000Z'
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
