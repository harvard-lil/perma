from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
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
from perma.utils import paid_through_date_from_post, tz_datetime

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
        monthly_rate=Decimal(100.00)
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
        monthly_rate=Decimal(100.00),
        unlimited=True
    )
    user.save()
    assert user.unlimited
    assert not user.nonpaying

    return user

def customers():
    return [paying_registrar(), paying_user()]

def noncustomers():
    return [nonpaying_registrar(), nonpaying_user()]

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
            "rate": "Sentinel Rate",
            "frequency": "Sentinel Frequency",
            "paid_through": "1970-01-21T00:00:00.000000Z"

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
                'paid_through': paid_through_date_from_post('1970-01-21T00:00:00.000000Z')
            })
            self.assertEqual(post.call_count, 1)
            post.reset_mock()


    def test_annual_rate(self):
        for customer in customers():
            self.assertEqual(customer.annual_rate() / 12, customer.monthly_rate)


    def test_prorated_first_month_cost_full_month(self):
        for customer in customers():
            cost = customer.prorated_first_month_cost(GENESIS)
            self.assertEqual(customer.monthly_rate, cost)


    def test_prorated_first_month_cost_last_day_of_month(self):
        for customer in customers():
            cost = customer.prorated_first_month_cost(GENESIS.replace(day=31))
            self.assertEqual((customer.monthly_rate / 31).quantize(Decimal('.01')), cost)


    def test_prorated_first_month_cost_mid_month(self):
        for customer in customers():
            cost = customer.prorated_first_month_cost(GENESIS.replace(day=16))
            self.assertEqual((customer.monthly_rate / 31 * 16).quantize(Decimal('.01')), cost)


    # Does this have to be tested? It's important, but.....
    # def test_get_subscription_info(self, get_subscription):
    #     pass


    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_registrar_link_creation_always_allowed_if_nonpaying(self, get_subscription):
        registrar = nonpaying_registrar()
        self.assertTrue(registrar.link_creation_allowed())
        self.assertEqual(get_subscription.call_count, 0)


    @patch('perma.models.LinkUser.get_links_remaining', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_allowed_if_nonpaying_and_under_limit(self, get_subscription, get_links_remaining):
        get_links_remaining.return_value = 1
        user = nonpaying_user()
        self.assertTrue(user.link_creation_allowed())
        self.assertEqual(get_subscription.call_count, 0)
        self.assertEqual(get_links_remaining.call_count, 1)


    @patch('perma.models.LinkUser.get_links_remaining', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_denied_if_nonpaying_and_over_limit(self, get_subscription, get_links_remaining):
        get_links_remaining.return_value = 0
        user = nonpaying_user()
        self.assertFalse(user.link_creation_allowed())
        self.assertEqual(get_subscription.call_count, 0)
        self.assertEqual(get_links_remaining.call_count, 1)


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


    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_registrar_link_creation_disallowed_if_no_subscription(self, get_subscription):
        get_subscription.return_value = None
        r = paying_registrar()
        self.assertFalse(r.link_creation_allowed())
        get_subscription.assert_called_once_with(r)


    @patch('perma.models.LinkUser.get_links_remaining', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_allowed_if_no_subscription_and_under_limit(self, get_subscription, get_links_remaining):
        get_subscription.return_value = None
        get_links_remaining.return_value = 1
        user = paying_user()
        self.assertTrue(user.link_creation_allowed())
        self.assertEqual(get_subscription.call_count, 1)
        self.assertEqual(get_links_remaining.call_count, 1)


    @patch('perma.models.LinkUser.get_links_remaining', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_denied_if_no_subscription_and_over_limit(self, get_subscription, get_links_remaining):
        get_subscription.return_value = None
        get_links_remaining.return_value = 0
        user = paying_user()
        self.assertFalse(user.link_creation_allowed())
        self.assertEqual(get_subscription.call_count, 1)
        self.assertEqual(get_links_remaining.call_count, 1)


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


    @patch('perma.models.LinkUser.get_links_remaining', autospec=True)
    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.subscription_has_problem', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_disallowed_if_subscription_inactive_and_over_limit(self, get_subscription, has_problem, is_active, get_links_remaining):
        get_links_remaining.return_value = 0
        get_subscription.return_value = sentinel.subscription
        is_active.return_value = False
        has_problem.return_value = True
        user = paying_user()
        self.assertFalse(user.link_creation_allowed())
        get_subscription.assert_called_once_with(user)
        is_active.assert_called_once_with(sentinel.subscription)
        self.assertEqual(get_links_remaining.call_count, 1)


    @patch('perma.models.LinkUser.get_links_remaining', autospec=True)
    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.subscription_has_problem', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_allowed_if_subscription_inactive_and_under_limit(self, get_subscription, has_problem, is_active, get_links_remaining):
        get_links_remaining.return_value = 1
        get_subscription.return_value = sentinel.subscription
        is_active.return_value = False
        has_problem.return_value = True
        user = paying_user()
        self.assertTrue(user.link_creation_allowed())
        get_subscription.assert_called_once_with(user)
        is_active.assert_called_once_with(sentinel.subscription)
        self.assertEqual(get_links_remaining.call_count, 1)


    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_registrar_link_creation_allowed_if_subscription_active(self, get_subscription, is_active):
        get_subscription.return_value = sentinel.subscription
        is_active.return_value = True
        customer = paying_registrar()
        self.assertTrue(customer.link_creation_allowed())
        get_subscription.assert_called_once_with(customer)
        is_active.assert_called_once_with(sentinel.subscription)


    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.LinkUser.get_subscription', autospec=True)
    def test_user_link_creation_allowed_if_subscription_active(self, get_subscription, is_active):
        get_subscription.return_value = sentinel.subscription
        is_active.return_value = True
        customer = paying_user()
        self.assertTrue(customer.link_creation_allowed())
        get_subscription.assert_called_once_with(customer)
        is_active.assert_called_once_with(sentinel.subscription)


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
