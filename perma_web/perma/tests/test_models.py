from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.utils import timezone

from mock import patch, sentinel

from perma.models import *
from perma.utils import paid_through_date_from_post

from .utils import PermaTestCase


# Fixtures

GENESIS = datetime.fromtimestamp(0).replace(tzinfo=timezone.utc)

def nonpaying_registrar():
    r = Registrar()
    r.save()
    assert r.nonpaying
    return r


def paying_registrar():
    r = Registrar(
        nonpaying=False,
        cached_subscription_status="Sentinel Status",
        cached_paid_through="1970-01-21T00:00:00.000000Z",
        monthly_rate=Decimal(100.00)
    )
    r.save()
    assert not r.nonpaying
    return r


def spoof_pp_response_wrong_registrar(r):
    d = {
        "registrar": "not_the_id"
    }
    assert r.pk != d['registrar']
    return d


def spoof_pp_response_no_subscription(r):
    return {
        "registrar": r.pk,
        "subscription": None
    }


def spoof_pp_response_subscription(r):
    return {
        "registrar": r.pk,
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
        r = nonpaying_registrar()
        self.assertIsNone(r.get_subscription())
        self.assertEqual(post.call_count, 0)


    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_raises_on_non_200(self, post):
        r = paying_registrar()
        post.return_value.ok = False
        with self.assertRaises(PermaPaymentsCommunicationException):
            r.get_subscription()
        self.assertEqual(post.call_count, 1)


    @patch('perma.models.process_perma_payments_transmission', autospec=True)
    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_verifies_transmission_valid(self, post, process):
        r = paying_registrar()
        post.return_value.status_code = 200
        post.return_value.json.return_value = sentinel.json
        # This will raise an exception further down in the function;
        # we don't care at this point
        with self.assertRaises(Exception):
            r.get_subscription()
        self.assertEqual(post.call_count, 1)
        process.assert_called_once_with(sentinel.json, FIELDS_REQUIRED_FROM_PERMA_PAYMENTS['get_subscription'])


    @patch('perma.models.process_perma_payments_transmission', autospec=True)
    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_raises_if_unexpected_registrar_id(self, post, process):
        r = paying_registrar()
        post.return_value.status_code = 200
        process.return_value = spoof_pp_response_wrong_registrar(r)
        with self.assertRaises(InvalidTransmissionException):
            r.get_subscription()
        self.assertEqual(post.call_count, 1)


    @patch('perma.models.process_perma_payments_transmission', autospec=True)
    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_no_subscription(self, post, process):
        r = paying_registrar()
        post.return_value.status_code = 200
        process.return_value = spoof_pp_response_no_subscription(r)
        self.assertIsNone(r.get_subscription())
        self.assertEqual(post.call_count, 1)


    @patch('perma.models.process_perma_payments_transmission', autospec=True)
    @patch('perma.models.requests.post', autospec=True)
    def test_get_subscription_happy_path(self, post, process):
        r = paying_registrar()
        response = spoof_pp_response_subscription(r)
        post.return_value.status_code = 200
        process.return_value = response
        subscription = r.get_subscription()
        self.assertEqual(r.cached_subscription_status, response['subscription']['status'])
        self.assertEqual(subscription, {
            'status': response['subscription']['status'],
            'rate': response['subscription']['rate'],
            'frequency': response['subscription']['frequency'],
            'paid_through': paid_through_date_from_post('1970-01-21T00:00:00.000000Z')
        })
        self.assertEqual(post.call_count, 1)


    def test_annual_rate(self):
        r = paying_registrar()
        self.assertEqual(r.annual_rate() / 12, r.monthly_rate)


    def test_prorated_first_month_cost_full_month(self):
        r = paying_registrar()
        cost = r.prorated_first_month_cost(GENESIS)
        self.assertEqual(r.monthly_rate, cost)


    def test_prorated_first_month_cost_last_day_of_month(self):
        r = paying_registrar()
        cost = r.prorated_first_month_cost(GENESIS.replace(day=31))
        self.assertEqual((r.monthly_rate / 31).quantize(Decimal('.01')), cost)


    def test_prorated_first_month_cost_mid_month(self):
        r = paying_registrar()
        cost = r.prorated_first_month_cost(GENESIS.replace(day=16))
        self.assertEqual((r.monthly_rate / 31 * 16).quantize(Decimal('.01')), cost)


    # Does this have to be tested? It's important, but.....
    # def test_get_subscription_info(self, get_subscription):
    #     pass


    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_link_creation_always_allowed_if_nonpaying(self, get_subscription):
        r = nonpaying_registrar()
        self.assertTrue(r.link_creation_allowed())
        self.assertEqual(get_subscription.call_count, 0)


    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_link_creation_allowed_checks_cached_if_pp_down(self, get_subscription, is_active):
        get_subscription.side_effect = PermaPaymentsCommunicationException
        r = paying_registrar()
        r.link_creation_allowed()
        get_subscription.assert_called_once_with(r)
        is_active.assert_called_once_with({
            'status': 'Sentinel Status',
            'paid_through': '1970-01-21T00:00:00.000000Z'
        })


    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_link_creation_disallowed_if_no_subscription(self, get_subscription):
        get_subscription.return_value = None
        r = paying_registrar()
        self.assertFalse(r.link_creation_allowed())
        get_subscription.assert_called_once_with(r)


    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_link_creation_disallowed_if_subscription_inactive(self, get_subscription, is_active):
        get_subscription.return_value = sentinel.subscription
        is_active.return_value = False
        r = paying_registrar()
        self.assertFalse(r.link_creation_allowed())
        get_subscription.assert_called_once_with(r)
        is_active.assert_called_once_with(sentinel.subscription)


    @patch('perma.models.subscription_is_active', autospec=True)
    @patch('perma.models.Registrar.get_subscription', autospec=True)
    def test_link_creation_allowed_if_subscription_active(self, get_subscription, is_active):
        get_subscription.return_value = sentinel.subscription
        is_active.return_value = True
        r = paying_registrar()
        self.assertTrue(r.link_creation_allowed())
        get_subscription.assert_called_once_with(r)
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
