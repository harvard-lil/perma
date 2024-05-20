from collections import defaultdict
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
    Link, Organization, Registrar, Folder,
    Sponsorship,
    link_count_in_time_period,
    most_active_org_in_time_period,
    subscription_is_active
)
from perma.utils import pp_date_from_post, tz_datetime, first_day_of_next_month, today_next_year, years_ago_today

from conftest import GENESIS
import pytest


#
# Related to Perma Payments
#

@patch('perma.models.requests.post', autospec=True)
def test_get_subscription_none_and_no_network_call_if_nonpaying(post, noncustomers):
    # also verify that their value of in_trial is unchanged by the call
    for noncustomer in noncustomers:
        in_trial = noncustomer.in_trial
        assert noncustomer.get_subscription() is None
        noncustomer.refresh_from_db()
        assert in_trial == noncustomer.in_trial
        assert post.call_count == 0


@patch('perma.models.requests.post', autospec=True)
def test_get_subscription_raises_on_non_200(post, customers):
    post.return_value.ok = False
    for customer in customers:
        with pytest.raises(PermaPaymentsCommunicationException):
            customer.get_subscription()
        assert post.call_count == 1
        post.reset_mock()


@patch('perma.models.process_perma_payments_transmission', autospec=True)
@patch('perma.models.requests.post', autospec=True)
def test_get_subscription_verifies_transmission_valid(post, process, customers):
    post.return_value.status_code = 200
    post.return_value.json.return_value = sentinel.json
    for customer in customers:
        # This will raise an exception further down in the function;
        # we don't care at this point
        with pytest.raises(Exception):
            customer.get_subscription()
        assert post.call_count == 1
        process.assert_called_once_with(sentinel.json, FIELDS_REQUIRED_FROM_PERMA_PAYMENTS['get_subscription'])
        post.reset_mock()
        process.reset_mock()


@patch('perma.models.process_perma_payments_transmission', autospec=True)
@patch('perma.models.requests.post', autospec=True)
def test_get_subscription_raises_if_unexpected_customer_pk(post, process, customers, spoof_pp_response_wrong_pk):
    post.return_value.status_code = 200
    for customer in customers:
        process.return_value = spoof_pp_response_wrong_pk(customer)
        with pytest.raises(InvalidTransmissionException):
            customer.get_subscription()
        assert post.call_count == 1
        post.reset_mock()


@patch('perma.models.process_perma_payments_transmission', autospec=True)
@patch('perma.models.requests.post', autospec=True)
def test_get_subscription_raises_if_unexpected_registrar_type(post, process, customers, spoof_pp_response_wrong_type):
    post.return_value.status_code = 200
    for customer in customers:
        process.return_value = spoof_pp_response_wrong_type(customer)
        with pytest.raises(InvalidTransmissionException):
            customer.get_subscription()
        assert post.call_count == 1
        post.reset_mock()


@patch('perma.models.process_perma_payments_transmission', autospec=True)
@patch('perma.models.requests.post', autospec=True)
def test_get_subscription_no_subscription(post, process, customers, spoof_pp_response_no_subscription):
    post.return_value.status_code = 200
    for customer in customers:
        with patch.object(customer, 'credit_for_purchased_links', autospec=True, wraps=True) as credited:
            # artificially set this for the purpose of this test
            customer.cached_subscription_started = timezone.now()
            customer.save()
            customer.refresh_from_db()
            assert customer.cached_subscription_started

            process.return_value = spoof_pp_response_no_subscription(customer)
            assert customer.get_subscription() is None
            assert not customer.cached_subscription_started
            assert post.call_count == 1
            assert credited.call_count == 0
            post.reset_mock()


@patch('perma.models.process_perma_payments_transmission', autospec=True)
@patch('perma.models.requests.post', autospec=True)
def test_get_subscription_no_subscription_purchased_bonus(post, process, customers, spoof_pp_response_no_subscription_two_purchases):
    post.return_value.status_code = 200
    for customer in customers:
        with patch.object(customer, 'credit_for_purchased_links', autospec=True, wraps=True) as credited:
            from_pp = spoof_pp_response_no_subscription_two_purchases(customer)
            process.return_value = from_pp
            assert customer.get_subscription() is None
            assert not customer.cached_subscription_started
            assert post.call_count == 1
            credited.assert_called_once_with(from_pp['purchases'])
            post.reset_mock()


@patch('perma.models.process_perma_payments_transmission', autospec=True)
@patch('perma.models.requests.post', autospec=True)
def test_get_subscription_happy_path_sets_customer_trial_period_to_false(post, process, paying_limited_registrar, paying_user, spoof_pp_response_subscription):
    post.return_value.status_code = 200
    for customer in [paying_limited_registrar, paying_user]:
        # artificially set this for the purpose of this test
        customer.in_trial = True
        customer.cached_subscription_started = None
        customer.save()
        customer.refresh_from_db()
        assert customer.in_trial
        assert not customer.cached_subscription_started

        response = spoof_pp_response_subscription(customer)
        process.return_value = response
        customer.get_subscription()
        customer.refresh_from_db()

        assert not customer.in_trial
        assert customer.cached_subscription_started


@patch('perma.models.process_perma_payments_transmission', autospec=True)
@patch('perma.models.requests.post', autospec=True)
def test_get_subscription_happy_path_no_change_pending(post, process, paying_limited_registrar, paying_user, spoof_pp_response_subscription):
    post.return_value.status_code = 200
    for customer in [paying_limited_registrar, paying_user]:
        with patch.object(customer, 'credit_for_purchased_links', autospec=True, wraps=True) as credited:
            response = spoof_pp_response_subscription(customer)
            process.return_value = response
            subscription = customer.get_subscription()
            customer.refresh_from_db()
            assert customer.cached_subscription_status == response['subscription']['status']
            assert subscription == {
                'status': response['subscription']['status'],
                'link_limit': response['subscription']['link_limit'],
                'rate': response['subscription']['rate'],
                'frequency': response['subscription']['frequency'],
                'paid_through': pp_date_from_post('1970-01-21T00:00:00.000000Z'),
                'pending_change': None,
                'reference_number': response['subscription']['reference_number']
            }
            assert post.call_count == 1
            assert credited.call_count == 0
            post.reset_mock()


@patch('perma.models.process_perma_payments_transmission', autospec=True)
@patch('perma.models.requests.post', autospec=True)
def test_get_subscription_happy_path_with_pending_change(post, process, paying_limited_registrar, paying_user, spoof_pp_response_subscription_with_pending_change):
    post.return_value.status_code = 200
    for customer in [paying_limited_registrar, paying_user]:
        with patch.object(customer, 'credit_for_purchased_links', autospec=True, wraps=True) as credited:
            response = spoof_pp_response_subscription_with_pending_change(customer)
            process.return_value = response
            subscription = customer.get_subscription()
            customer.refresh_from_db()
            assert customer.cached_subscription_status == response['subscription']['status']
            assert subscription == {
                'status': response['subscription']['status'],
                'link_limit': str(customer.link_limit),
                'rate': str(customer.cached_subscription_rate),
                'frequency': customer.link_limit_period,
                'paid_through': pp_date_from_post('9999-01-21T00:00:00.000000Z'),
                'reference_number': response['subscription']['reference_number'],
                'pending_change': {
                    'rate': response['subscription']['rate'],
                    'link_limit': response['subscription']['link_limit'],
                    'effective': pp_date_from_post(response['subscription']['link_limit_effective_timestamp'])
                }
            }
            assert str(customer.link_limit) != response['subscription']['link_limit']
            assert str(customer.cached_subscription_rate) != response['subscription']['rate']
            assert post.call_count == 1
            assert credited.call_count == 0
            post.reset_mock()


#
# Link limits and bonus links
#

def test_bonus_links_arent_counted_against_personal_total(link_user, link_factory):
    remaining, _, bonus = link_user.get_links_remaining()

    personal_links = 5
    bonus_links = 2
    for _ in range(personal_links):
        link_factory(created_by=link_user)
    for _ in range(bonus_links):
        link_factory(created_by=link_user, bonus_link=True)
    now_remaining, _, now_bonus = link_user.get_links_remaining()
    assert now_remaining == remaining - personal_links
    assert now_remaining == 5
    assert now_remaining != remaining - personal_links - bonus_links
    assert remaining - personal_links - bonus_links == 3


#
# Link limit / subscription related tests for individual (non-sponsored) users
#

def test_new_user_gets_default_link_limit(link_user):
    assert link_user.link_limit == settings.DEFAULT_CREATE_LIMIT
    assert link_user.link_limit_period == settings.DEFAULT_CREATE_LIMIT_PERIOD


def test_one_time_link_limit_new(user_with_links):
    assert not user_with_links.unlimited
    assert not user_with_links.cached_subscription_started
    assert user_with_links.links_remaining_in_period('once', 6) ==  1
    assert user_with_links.links_remaining_in_period('once', 5) ==  0


@patch('perma.models.timezone', autospec=True)
def test_one_time_link_limit_with_midmonth_subscription1(mocked_timezone, user_with_links_this_month_before_the_15th):
    fifteenth_of_month = timezone.now().replace(day=15)
    mocked_timezone.now.return_value = fifteenth_of_month

    u = user_with_links_this_month_before_the_15th
    u.cached_subscription_started = fifteenth_of_month
    u.save()
    u.refresh_from_db()

    assert not u.unlimited
    assert u.links_remaining_in_period('once', 6) == 6
    assert u.links_remaining_in_period('once', 5) == 5
    assert mocked_timezone.now.call_count == 2


@patch('perma.models.timezone', autospec=True)
def test_one_time_link_limit_with_midmonth_subscription2(mocked_timezone, user_with_links_this_month_before_the_15th):
    fifteenth_of_month = timezone.now().replace(day=15)
    fifth_of_month = timezone.now().replace(day=5)
    mocked_timezone.now.return_value = fifteenth_of_month

    u = user_with_links_this_month_before_the_15th
    u.cached_subscription_started = fifth_of_month
    u.save()
    u.refresh_from_db()

    assert not u.unlimited
    assert u.links_remaining_in_period('once', 6) == 5
    assert u.links_remaining_in_period('once', 5) == 4
    assert mocked_timezone.now.call_count == 2


def test_monthly_link_limit(user_with_links):
    assert not user_with_links.unlimited
    assert user_with_links.links_remaining_in_period('monthly', 3) == 1
    assert user_with_links.links_remaining_in_period('monthly', 2) == 0


@patch('perma.models.timezone', autospec=True)
def test_monthly_link_limit_with_midmonth_subscription1(mocked_timezone, user_with_links_this_month_before_the_15th):
    fifteenth_of_month = timezone.now().replace(day=15)
    mocked_timezone.now.return_value = fifteenth_of_month

    u = user_with_links_this_month_before_the_15th
    u.cached_subscription_started = fifteenth_of_month
    u.save()

    assert not u.unlimited
    assert u.links_remaining_in_period('monthly', 3) == 3
    assert u.links_remaining_in_period('monthly', 2) == 2
    assert mocked_timezone.now.call_count == 2


@patch('perma.models.timezone', autospec=True)
def test_monthly_link_limit_with_midmonth_subscription2(mocked_timezone, user_with_links_this_month_before_the_15th):
    fifteenth_of_month = timezone.now().replace(day=15)
    fifth_of_month = timezone.now().replace(day=5)
    mocked_timezone.now.return_value = fifteenth_of_month

    u = user_with_links_this_month_before_the_15th
    u.cached_subscription_started = fifth_of_month
    u.save()

    assert not u.unlimited
    assert u.links_remaining_in_period('monthly', 3) == 2
    assert u.links_remaining_in_period('monthly', 2) == 1
    assert mocked_timezone.now.call_count == 2


def test_annual_link_limit(user_with_links):
    assert not user_with_links.unlimited
    assert user_with_links.links_remaining_in_period('annually', 4) == 1
    assert user_with_links.links_remaining_in_period('annually', 3) == 0


def test_unlimited_user_link_limit(user_with_links):
    user_with_links.unlimited = True
    assert user_with_links.links_remaining_in_period('once', 1) == float("inf")
    assert user_with_links.links_remaining_in_period('monthly', 1) == float("inf")
    assert user_with_links.links_remaining_in_period('annually', 1) == float("inf")

    user_with_links.unlimited = False
    assert user_with_links.links_remaining_in_period('once', 1) != float("inf")
    assert user_with_links.links_remaining_in_period('monthly', 1) != float("inf")
    assert user_with_links.links_remaining_in_period('annually', 1) != float("inf")


def test_override_for_unlimited_user_link_limit(user_with_links):
    user_with_links.unlimited = True

    assert user_with_links.links_remaining_in_period('once', 1) == float("inf")
    assert user_with_links.links_remaining_in_period('monthly', 1) == float("inf")
    assert user_with_links.links_remaining_in_period('annually', 1) == float("inf")

    assert user_with_links.links_remaining_in_period('once', 1, False) != float("inf")
    assert user_with_links.links_remaining_in_period('monthly', 1, False) != float("inf")
    assert user_with_links.links_remaining_in_period('annually', 1, False) != float("inf")


@patch('perma.models.LinkUser.get_links_remaining', autospec=True)
@patch('perma.models.LinkUser.get_subscription', autospec=True)
def test_user_link_creation_allowed_if_nonpaying_and_under_limit(get_subscription, get_links_remaining, nonpaying_user):
    get_links_remaining.return_value = (1, 'some period', 0)

    assert nonpaying_user.link_creation_allowed()
    assert get_subscription.call_count == 0
    assert get_links_remaining.call_count == 1


@patch('perma.models.LinkUser.get_links_remaining', autospec=True)
@patch('perma.models.LinkUser.get_subscription', autospec=True)
def test_user_link_creation_denied_if_nonpaying_and_over_limit(get_subscription, get_links_remaining, nonpaying_user):
    get_links_remaining.return_value = (0, 'some period', 0)

    assert not nonpaying_user.link_creation_allowed()
    assert get_subscription.call_count == 0
    assert get_links_remaining.call_count == 1


@patch('perma.models.subscription_is_active', autospec=True)
@patch('perma.models.LinkUser.get_subscription', autospec=True)
def test_user_link_creation_allowed_checks_cached_if_pp_down(get_subscription, is_active, paying_user):
    get_subscription.side_effect = PermaPaymentsCommunicationException

    assert paying_user.link_creation_allowed()
    get_subscription.assert_called_once_with(paying_user)
    is_active.assert_called_once_with({
        'status': 'Sentinel Status',
        'paid_through': GENESIS
    })


@patch('perma.models.LinkUser.links_remaining_in_period', autospec=True)
@patch('perma.models.LinkUser.get_subscription', autospec=True)
def test_user_link_creation_allowed_if_no_subscription_and_under_limit(get_subscription, links_remaining_in_period, paying_user):
    get_subscription.return_value = None
    links_remaining_in_period.return_value = 1
    assert paying_user.link_creation_allowed()
    assert get_subscription.call_count == 1
    links_remaining_in_period.assert_called_once_with(paying_user, settings.DEFAULT_CREATE_LIMIT_PERIOD, settings.DEFAULT_CREATE_LIMIT, False)


@patch('perma.models.LinkUser.links_remaining_in_period', autospec=True)
@patch('perma.models.LinkUser.get_subscription', autospec=True)
def test_user_link_creation_denied_if_no_subscription_and_over_limit(get_subscription, links_remaining_in_period, paying_user):
    get_subscription.return_value = None
    links_remaining_in_period.return_value = 0
    assert not paying_user.link_creation_allowed()
    assert get_subscription.call_count == 1
    links_remaining_in_period.assert_called_once_with(paying_user, settings.DEFAULT_CREATE_LIMIT_PERIOD, settings.DEFAULT_CREATE_LIMIT, False)


@patch('perma.models.LinkUser.links_remaining_in_period', autospec=True)
@patch('perma.models.subscription_is_active', autospec=True)
@patch('perma.models.subscription_has_problem', autospec=True)
@patch('perma.models.LinkUser.get_subscription', autospec=True)
def test_user_link_creation_disallowed_if_subscription_inactive_and_over_limit(get_subscription, has_problem, is_active, links_remaining_in_period, paying_user):
    get_subscription.return_value = sentinel.subscription
    is_active.return_value = False
    has_problem.return_value = True
    links_remaining_in_period.return_value = 0

    assert not paying_user.link_creation_allowed()
    get_subscription.assert_called_once_with(paying_user)
    is_active.assert_called_once_with(sentinel.subscription)
    links_remaining_in_period.assert_called_once_with(paying_user, settings.DEFAULT_CREATE_LIMIT_PERIOD, settings.DEFAULT_CREATE_LIMIT, False)


@patch('perma.models.LinkUser.links_remaining_in_period', autospec=True)
@patch('perma.models.subscription_is_active', autospec=True)
@patch('perma.models.subscription_has_problem', autospec=True)
@patch('perma.models.LinkUser.get_subscription', autospec=True)
def test_user_link_creation_allowed_if_subscription_inactive_and_under_limit(get_subscription, has_problem, is_active, links_remaining_in_period, paying_user):
    get_subscription.return_value = sentinel.subscription
    is_active.return_value = False
    has_problem.return_value = True
    links_remaining_in_period.return_value = paying_user.link_limit + 1

    assert paying_user.link_creation_allowed()
    get_subscription.assert_called_once_with(paying_user)
    is_active.assert_called_once_with(sentinel.subscription)
    links_remaining_in_period.assert_called_once_with(paying_user, settings.DEFAULT_CREATE_LIMIT_PERIOD, settings.DEFAULT_CREATE_LIMIT, False)


@patch('perma.models.LinkUser.links_remaining_in_period', autospec=True)
@patch('perma.models.subscription_is_active', autospec=True)
@patch('perma.models.LinkUser.get_subscription', autospec=True)
def test_user_link_creation_allowed_if_subscription_active_and_under_limit(get_subscription, is_active, links_remaining_in_period, paying_user):
    get_subscription.return_value = sentinel.subscription
    is_active.return_value = True
    links_remaining_in_period.return_value = 1

    assert paying_user.link_creation_allowed()
    get_subscription.assert_called_once_with(paying_user)
    is_active.assert_called_once_with(sentinel.subscription)
    links_remaining_in_period.assert_called_once_with(paying_user, paying_user.link_limit_period, paying_user.link_limit)


@patch('perma.models.LinkUser.links_remaining_in_period', autospec=True)
@patch('perma.models.subscription_is_active', autospec=True)
@patch('perma.models.LinkUser.get_subscription', autospec=True)
def test_user_link_creation_disallowed_if_subscription_active_and_under_limit(get_subscription, is_active, links_remaining_in_period, paying_user):
    get_subscription.return_value = sentinel.subscription
    is_active.return_value = True
    links_remaining_in_period.return_value = 0

    assert not paying_user.link_creation_allowed()
    get_subscription.assert_called_once_with(paying_user)
    is_active.assert_called_once_with(sentinel.subscription)
    links_remaining_in_period.assert_called_once_with(paying_user, paying_user.link_limit_period, paying_user.link_limit)


#
# Link limit / subscription related tests for registrars
#

@patch('perma.models.Registrar.get_subscription', autospec=True)
def test_registrar_link_creation_always_allowed_if_nonpaying(get_subscription, nonpaying_registrar):
    assert nonpaying_registrar.link_creation_allowed()
    assert get_subscription.call_count == 0


@patch('perma.models.subscription_is_active', autospec=True)
@patch('perma.models.Registrar.get_subscription', autospec=True)
def test_registrar_link_creation_allowed_checks_cached_if_pp_down(get_subscription, is_active, paying_registrar):
    get_subscription.side_effect = PermaPaymentsCommunicationException
    paying_registrar.link_creation_allowed()
    get_subscription.assert_called_once_with(paying_registrar)
    is_active.assert_called_once_with({
        'status': 'Sentinel Status',
        'paid_through': GENESIS
    })


@patch('perma.models.Registrar.get_subscription', autospec=True)
def test_registrar_link_creation_disallowed_if_no_subscription(get_subscription, paying_registrar):
    get_subscription.return_value = None
    assert not paying_registrar.link_creation_allowed()
    get_subscription.assert_called_once_with(paying_registrar)


@patch('perma.models.subscription_is_active', autospec=True)
@patch('perma.models.subscription_has_problem', autospec=True)
@patch('perma.models.Registrar.get_subscription', autospec=True)
def test_registrar_link_creation_disallowed_if_subscription_inactive(get_subscription, has_problem, is_active, paying_registrar):
    get_subscription.return_value = sentinel.subscription
    is_active.return_value = False
    has_problem.return_value = True
    assert not paying_registrar.link_creation_allowed()
    get_subscription.assert_called_once_with(paying_registrar)
    is_active.assert_called_once_with(sentinel.subscription)


@patch('perma.models.subscription_is_active', autospec=True)
@patch('perma.models.Registrar.get_subscription', autospec=True)
def test_registrar_link_creation_allowed_if_subscription_active(get_subscription, is_active, paying_registrar):
    get_subscription.return_value = sentinel.subscription
    is_active.return_value = True
    assert paying_registrar.link_creation_allowed()
    get_subscription.assert_called_once_with(paying_registrar)
    is_active.assert_called_once_with(sentinel.subscription)


#
# Annotating Tiers with Prices and Dates
#

# check monthly tiers for customers with no subscriptions

def test_annotate_tier_monthly_no_subscription_first_of_month(customers):
    now = GENESIS.replace(day=1)
    next_month = first_day_of_next_month(now)
    next_year = today_next_year(now)
    subscription = None
    for customer in customers:
        tier = {
            'period': 'monthly',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'upgrade'
        assert tier['link_limit_effective_timestamp'] == now.timestamp()
        assert Decimal(tier['todays_charge']) == customer.base_rate * tier['rate_ratio']
        assert tier['recurring_amount'] == tier['todays_charge']
        assert tier['next_payment'] == next_month


def test_annotate_tier_monthly_no_subscription_mid_month(customers):
    now = GENESIS.replace(day=16)
    next_month = first_day_of_next_month(now)
    next_year = today_next_year(now)
    subscription = None
    for customer in customers:
        tier = {
            'period': 'monthly',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'upgrade'
        assert tier['link_limit_effective_timestamp'] == now.timestamp()
        assert Decimal(tier['todays_charge']) == (customer.base_rate * tier['rate_ratio'] / 31 * 16).quantize(Decimal('.01'))
        assert tier['recurring_amount'] != tier['todays_charge']
        assert tier['next_payment'] == next_month


@patch('perma.models.subscription_is_active', autospec=True)
def test_annotate_tier_monthly_no_subscription_last_of_month(is_active, customers):
    is_active.return_value = True

    now = GENESIS.replace(day=31)
    next_month = first_day_of_next_month(now)
    next_year = today_next_year(now)
    subscription = None
    for customer in customers:
        tier = {
            'period': 'monthly',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'upgrade'
        assert tier['link_limit_effective_timestamp'] == now.timestamp()
        assert Decimal(tier['todays_charge']) == (customer.base_rate * tier['rate_ratio'] / 31).quantize(Decimal('.01'))
        assert tier['recurring_amount'] != tier['todays_charge']
        assert tier['next_payment'] == next_month


# check upgrading/downgrading not allowed if you have a non-active subscription
# (for instance, on hold due to lapsed payments), whatever the tier

def test_annotate_tier_change_disallowed_with_inactive_monthly_subscription(customers):
    now = GENESIS.replace(day=31)
    next_month = first_day_of_next_month(now)
    next_year = today_next_year(now)
    subscription = {
        'status': 'Sentinel Status',
        'rate': '0.10',
        'frequency': 'monthly',
        'paid_through': next_month
    }

    for customer in customers:
        for tier in settings.TIERS[customer.customer_type]:
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            assert tier['type'] == 'unavailable'


def test_annotate_tier_change_disallowed_with_inactive_annual_subscription(customers):
    now = GENESIS.replace(day=31)
    next_month = first_day_of_next_month(now)
    next_year = today_next_year(now)
    subscription = {
        'status': 'Sentinel Status',
        'rate': '0.10',
        'frequency': 'annually',
        'paid_through': next_year
    }

    for customer in customers:
        for tier in settings.TIERS[customer.customer_type]:
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            assert tier['type'] == 'unavailable'


@patch('perma.models.subscription_is_active', autospec=True)
def test_annotate_tier_change_disallowed_with_pending_downgrade(is_active, customers):
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

    for customer in customers:
        for tier in settings.TIERS[customer.customer_type]:
            customer.annotate_tier(tier, subscription, now, next_month, next_year)
            assert tier['type'] == 'unavailable'


# check upgrade monthly tiers for customers with subscriptions

def test_annotate_tier_monthly_active_subscription_upgrade_first_of_month(customers):
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
    for customer in customers:
        tier = {
            'period': 'monthly',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'upgrade'
        assert tier['link_limit_effective_timestamp'] == now.timestamp()
        assert Decimal(tier['todays_charge']) == customer.base_rate * tier['rate_ratio'] - Decimal(subscription['rate'])
        assert tier['recurring_amount'] != tier['todays_charge']
        assert tier['next_payment'] == next_month


def test_annotate_tier_monthly_active_subscription_upgrade_mid_month(customers):
    now = GENESIS.replace(day=16)
    next_month = first_day_of_next_month(now)
    next_year = today_next_year(now)
    subscription = {
        'status': 'Current',
        'rate': '0.10',
        'frequency': 'monthly',
        'link_limit': 0
    }
    for customer in customers:
        tier = {
            'period': 'monthly',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'upgrade'
        assert tier['link_limit_effective_timestamp'] == now.timestamp()
        assert Decimal(tier['todays_charge']) == ((customer.base_rate * tier['rate_ratio'] / 31 * 16) - (Decimal(subscription['rate']) / 31 * 16)).quantize(Decimal('.01'))
        assert tier['recurring_amount'] != tier['todays_charge']
        assert tier['next_payment'] == next_month


def test_annotate_tier_monthly_active_subscription_upgrade_last_of_month(customers):
    now = GENESIS.replace(day=31)
    next_month = first_day_of_next_month(now)
    next_year = today_next_year(now)
    subscription = {
        'status': 'Current',
        'rate': '0.10',
        'frequency': 'monthly',
        'link_limit': 0
    }
    for customer in customers:
        tier = {
            'period': 'monthly',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'upgrade'
        assert tier['link_limit_effective_timestamp'] == now.timestamp()
        assert Decimal(tier['todays_charge']) == ((customer.base_rate * tier['rate_ratio'] / 31) - (Decimal(subscription['rate']) / 31 )).quantize(Decimal('.01'))
        assert tier['recurring_amount'] != tier['todays_charge']
        assert tier['next_payment'] == next_month


# check downgrade monthly tiers for customers with subscriptions, amount and recurring not equal, amount == 0

def test_annotate_tier_monthly_active_subscription_downgrade_first_of_month(customers):
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
    for customer in customers:
        tier = {
            'period': 'monthly',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'downgrade'
        assert tier['link_limit_effective_timestamp'] == next_month.timestamp()
        assert Decimal(tier['todays_charge']) == Decimal('0')
        assert tier['recurring_amount'] != tier['todays_charge']
        assert tier['next_payment'] == next_month


def test_annotate_tier_monthly_active_subscription_downgrade_mid_month(customers):
    now = GENESIS.replace(day=16)
    next_month = first_day_of_next_month(now)
    next_year = today_next_year(now)
    subscription = {
        'status': 'Current',
        'rate': '9999.10',
        'frequency': 'monthly',
        'link_limit': 9999
    }
    for customer in customers:
        tier = {
            'period': 'monthly',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'downgrade'
        assert tier['link_limit_effective_timestamp'] == next_month.timestamp()
        assert Decimal(tier['todays_charge']) == Decimal('0')
        assert tier['recurring_amount']!= tier['todays_charge']
        assert tier['next_payment'] == next_month


def test_annotate_tier_monthly_active_subscription_downgrade_last_of_month(customers):
    now = GENESIS.replace(day=31)
    next_month = first_day_of_next_month(now)
    next_year = today_next_year(now)
    subscription = {
        'status': 'Current',
        'rate': '9999.10',
        'frequency': 'monthly',
        'link_limit': 9999
    }
    for customer in customers:
        tier = {
            'period': 'monthly',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'downgrade'
        assert tier['link_limit_effective_timestamp'] == next_month.timestamp()
        assert Decimal(tier['todays_charge']) == Decimal('0')
        assert tier['recurring_amount'] != tier['todays_charge']
        assert tier['next_payment'] == next_month


# check annual tiers for customers with no subscriptions

def test_annotate_tier_annually_no_subscription(customers):
    now = GENESIS.replace(day=1)
    next_month = first_day_of_next_month(now)
    next_year = today_next_year(now)
    subscription = None
    for customer in customers:
        tier = {
            'period': 'annually',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'upgrade'
        assert tier['link_limit_effective_timestamp'] == now.timestamp()
        assert Decimal(tier['todays_charge']) == customer.base_rate * tier['rate_ratio']
        assert tier['recurring_amount'] == tier['todays_charge']
        assert tier['next_payment'] == next_year


# check upgrade annual tiers for customers with current subscriptions, amount and recurring not equal, amount correct

def test_annotate_tier_annually_active_subscription_upgrade_same_day(customers):
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
    for customer in customers:
        tier = {
            'period': 'annually',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'upgrade'
        assert tier['link_limit_effective_timestamp'] == now.timestamp()
        assert Decimal(tier['todays_charge']) == customer.base_rate * tier['rate_ratio'] - Decimal(subscription['rate'])
        assert tier['recurring_amount'] != tier['todays_charge']
        assert tier['next_payment'] == subscription['paid_through']


def test_annotate_tier_annually_active_subscription_upgrade_midyear(customers):
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
    for customer in customers:
        tier = {
            'period': 'annually',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'upgrade'
        assert tier['link_limit_effective_timestamp'] == now.timestamp()
        assert Decimal(tier['todays_charge']) == ((customer.base_rate * tier['rate_ratio'] / 365 * 2) - (Decimal(subscription['rate']) / 365 * 2 )).quantize(Decimal('.01'))
        assert tier['recurring_amount'] != tier['todays_charge']
        assert tier['next_payment'] == subscription['paid_through']


def test_annotate_tier_annually_active_subscription_upgrade_on_anniversary(customers):
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
    for customer in customers:
        tier = {
            'period': 'annually',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'upgrade'
        assert tier['link_limit_effective_timestamp'] == now.timestamp()
        assert Decimal(tier['todays_charge']) == Decimal('0.00')
        assert tier['recurring_amount'] != tier['todays_charge']
        assert tier['next_payment'] == subscription['paid_through']


# check downgrade annual tiers for customers with subscriptions

def test_annotate_tier_annually_active_subscription_downgrade_same_day(customers):
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
    for customer in customers:
        tier = {
            'period': 'annually',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'downgrade'
        assert tier['link_limit_effective_timestamp'] == subscription['paid_through'].timestamp()
        assert Decimal(tier['todays_charge']) == Decimal('0.00')
        assert tier['recurring_amount'] != tier['todays_charge']
        assert tier['next_payment'] == subscription['paid_through']


def test_annotate_tier_annually_active_subscription_downgrade_midyear(customers):
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
    for customer in customers:
        tier = {
            'period': 'annually',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'downgrade'
        assert tier['link_limit_effective_timestamp'] == subscription['paid_through'].timestamp()
        assert Decimal(tier['todays_charge']) == Decimal('0.00')
        assert tier['recurring_amount'] != tier['todays_charge']
        assert tier['next_payment'] == subscription['paid_through']


def test_annotate_tier_annually_active_subscription_downgrade_on_anniversary(customers):
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
    for customer in customers:
        tier = {
            'period': 'annually',
            'link_limit': 500,
            'rate_ratio': 10
        }
        customer.annotate_tier(tier, subscription, now, next_month, next_year)
        assert tier['type'] == 'downgrade'
        assert tier['link_limit_effective_timestamp'] == subscription['paid_through'].timestamp()
        assert Decimal(tier['todays_charge']) == Decimal('0.00')
        assert tier['recurring_amount']!= tier['todays_charge']
        assert tier['next_payment'] == subscription['paid_through']


# check warnings

def test_annotate_tier_hides_more_expensive_option_from_grandfathered_customer(customers):
    now = GENESIS.replace(day=1)
    next_month = first_day_of_next_month(now)
    next_year = today_next_year(now)
    for customer in customers:
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
        assert tier['type'] == 'unavailable'


def test_annotate_tier_hides_similar_tier_from_higher_paying_customer(customers):
    now = GENESIS.replace(day=1)
    next_month = first_day_of_next_month(now)
    next_year = today_next_year(now)
    for customer in customers:
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
        assert tier['type'] == 'unavailable'


@override_settings(TIERS={
    'Individual': [defaultdict(str) for i in range(3)],
    'Registrar': [defaultdict(str) for i in range(3)]
})
@patch('perma.models.LinkUser.annotate_tier', autospec=True)
@patch('perma.models.LinkUser.get_subscription', autospec=True)
def test_get_subscription_info_normal(get_subscription, annotate_tier, paying_user):
    now = GENESIS.replace(day=1)
    subscription = {
        'status': 'Current',
        'rate': str(paying_user.base_rate * 5),
        'frequency': 'monthly',
        'paid_through': now.replace(day=15),
        'link_limit': 500
    }
    get_subscription.return_value = subscription
    account = paying_user.get_subscription_info(now)
    assert 'customer' in account
    assert subscription == account['subscription']
    assert 'tiers' in account
    assert annotate_tier.call_count == len(settings.TIERS[paying_user.customer_type])
    assert 'can_change_tiers' in account


@patch('perma.models.LinkUser.annotate_tier', autospec=True)
@patch('perma.models.LinkUser.get_subscription', autospec=True)
def test_get_subscription_info_downgrade_pending(get_subscription, annotate_tier, paying_user):
    now = GENESIS.replace(day=1)
    subscription = {
        'status': 'Current',
        'rate': str(paying_user.base_rate * 5),
        'frequency': 'monthly',
        'paid_through': now.replace(day=15),
        'link_limit': 500,
        'pending_change': {
            'rate': str(paying_user.base_rate * 1),
            'link_limit': 100,
            'effective': now.replace(day=31)
        }
    }
    get_subscription.return_value = subscription
    account = paying_user.get_subscription_info(now)
    assert 'customer' in account
    assert subscription == account['subscription']
    assert len(account['tiers']) == 1
    assert account['tiers'][0]['limit'] == subscription['link_limit']
    assert account['tiers'][0]['rate'] == subscription['rate']
    assert account['tiers'][0]['required_fields']['amount'] == '0.00'
    assert account['tiers'][0]['required_fields']['link_limit_effective_timestamp'] == now.timestamp()
    assert annotate_tier.call_count == 0
    assert account['can_change_tiers']


def test_subscription_is_active_with_active_status():
    for status in ACTIVE_SUBSCRIPTION_STATUSES:
        assert subscription_is_active({
            'status': status,
            'paid_through': 'some datetime'
        })


def test_subscription_is_active_with_paid_up_canceled(active_cancelled_subscription):
    assert subscription_is_active(active_cancelled_subscription)


def test_subscription_is_active_with_expired_canceled(expired_cancelled_subscription):
    assert not subscription_is_active(expired_cancelled_subscription)


#
# crediting users for one-time purchases
#

@patch('perma.models.requests.post', autospec=True)
def test_credit_for_purchased_links_increments_for_all(post, paying_user, spoof_pp_response_no_subscription_two_purchases):
    post.return_value.ok = True

    purchases = spoof_pp_response_no_subscription_two_purchases(paying_user)["purchases"]
    credited = paying_user.credit_for_purchased_links(purchases)
    assert post.call_count == 2

    assert credited == 60


@patch('perma.models.requests.post', autospec=True)
def test_credit_for_purchased_links_reverses_if_acknowledgment_fails(post, paying_user, spoof_pp_response_no_subscription_two_purchases):
    post.return_value.ok = False

    purchases = spoof_pp_response_no_subscription_two_purchases(paying_user)["purchases"]
    credited = paying_user.credit_for_purchased_links(purchases)
    assert post.call_count == 2

    assert credited == 0
    assert post.call_count == 2


#
# Bonus packages info
#

@patch.object(perma.models, 'datetime')
@patch('perma.models.prep_for_perma_payments', autospec=True)
def test_get_bonus_packages(prep, mock_datetime, paying_user):
    perma.models.datetime.utcnow.return_value = GENESIS
    prep.return_value.decode.return_value = sentinel.string

    packages = paying_user.get_bonus_packages()

    prep.assert_any_call({'timestamp': 0.0, 'customer_pk': paying_user.pk, 'customer_type': 'Individual', 'amount': '15.00', 'link_quantity': 10})
    prep.assert_any_call({'timestamp': 0.0, 'customer_pk': paying_user.pk, 'customer_type': 'Individual', 'amount': '30.00', 'link_quantity': 100})
    prep.assert_any_call({'timestamp': 0.0, 'customer_pk': paying_user.pk, 'customer_type': 'Individual', 'amount': '125.00', 'link_quantity': 500})
    assert packages == [
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
    ]


#
# Organization privacy
#

def test_new_orgs_are_public_by_default(db):
    r = Registrar()
    r.save()
    o = Organization(registrar=r)
    o.save()
    r.refresh_from_db()
    o.refresh_from_db()
    assert not r.orgs_private_by_default
    assert not o.default_to_private

def test_new_orgs_respect_registrar_default_privacy_policy(db):
    r = Registrar(orgs_private_by_default=True)
    r.save()
    o = Organization(registrar=r)
    o.save()
    r.refresh_from_db()
    o.refresh_from_db()
    assert r.orgs_private_by_default
    assert o.default_to_private

def test_existing_org_privacy_unaffected_by_registrar_change(db):
    r = Registrar()
    r.save()
    o = Organization(registrar=r)
    o.save()
    r.refresh_from_db()
    o.refresh_from_db()
    assert not r.orgs_private_by_default
    assert not o.default_to_private

    r.orgs_private_by_default = True
    r.save()
    r.refresh_from_db()
    o.refresh_from_db()
    assert r.orgs_private_by_default
    assert not o.default_to_private

    r.orgs_private_by_default = False
    r.save()
    r.refresh_from_db()
    o.refresh_from_db()
    assert not r.orgs_private_by_default
    assert not o.default_to_private

def test_org_privacy_does_not_revert_to_registrar_default_on_save(db):
    r = Registrar(orgs_private_by_default=True)
    r.save()
    o = Organization(registrar=r)
    o.save()
    r.refresh_from_db()
    o.refresh_from_db()
    assert r.orgs_private_by_default
    assert o.default_to_private

    o.default_to_private = False
    o.save()
    o.refresh_from_db()
    assert not o.default_to_private

    o.name = 'A New Name'
    o.save()
    o.refresh_from_db()
    assert o.name == 'A New Name'
    assert not o.default_to_private


#
# Cached folder paths
#

def test_new_folder_path_is_cached(db):
    f1 = Folder()
    f1.save()
    f1.refresh_from_db()
    assert str(f1.pk) == f1.cached_path
    f2 = Folder(parent=f1)
    f2.save()
    f2.refresh_from_db()
    assert f'{f1.pk}-{f2.pk}' == f2.cached_path

def test_folders_cached_paths_updated_when_moved(db):
    # f1
    # f2
    # f3 -> f3_1
    f1 = Folder(name=1)
    f1.save()
    f2 = Folder(parent=f1, name='2')
    f2.save()
    f3 = Folder(parent=f1, name='3')
    f3.save()
    f3_1 = Folder(parent=f3, name='3_1')
    f3_1.save()
    f1.refresh_from_db()
    f2.refresh_from_db()
    f3.refresh_from_db()
    f3_1.refresh_from_db()
    assert f'{f1.pk}-{f3.pk}' == f3.cached_path
    assert f'{f1.pk}-{f3.pk}-{f3_1.pk}' == f3_1.cached_path

    # f1
    # f2 -> f3 -> f3_1
    f3.parent_id = f2.pk
    f3.save()
    f3.refresh_from_db()
    f3_1.refresh_from_db()
    assert f'{f1.pk}-{f2.pk}-{f3.pk}' == f3.cached_path
    assert f'{f1.pk}-{f2.pk}-{f3.pk}-{f3_1.pk}' == f3_1.cached_path

    # and back
    f3.parent_id = f1.pk
    f3.save()
    f3.refresh_from_db()
    f3_1.refresh_from_db()
    assert f'{f1.pk}-{f3.pk}' == f3.cached_path
    assert f'{f1.pk}-{f3.pk}-{f3_1.pk}' == f3_1.cached_path

def test_cached_path_is_set_for_new_orgs(db):
    r = Registrar()
    r.save()
    o = Organization(registrar=r)
    o.save()
    o.refresh_from_db()
    assert o.shared_folder.cached_path


#
# Assess Link Counts
#

def test_link_count_in_time_period_no_links():
    '''
        If no links in period, should return 0
    '''
    no_links = Link.objects.none()
    assert link_count_in_time_period(no_links) == 0


def test_link_count_period_invalid_dates():
    '''
        If end date is before start date, should raise an exception
    '''
    no_links = Link.objects.none()
    now = tz_datetime(timezone.now().year, 1, 1)
    later = today_next_year(now)
    with pytest.raises(ValueError):
        link_count_in_time_period(no_links, later, now)


def test_link_count_period_equal_dates(link_user, link_factory):
    '''
        If end date = start date, links are only counted once
    '''
    now = tz_datetime(timezone.now().year, 1, 1)
    link = link_factory(creation_timestamp=now, guid="AAAA-AAAA", created_by=link_user)

    links = Link.objects.filter(pk=link.pk)
    assert len(links) == 1
    assert link_count_in_time_period(links, now, now) == len(links)


def test_link_count_valid_period(link_user, link_factory):
    '''
        Should include links created only in the target year
    '''
    now = tz_datetime(timezone.now().year, 1, 1)
    two_years_ago = years_ago_today(now, 2)
    three_years_ago = years_ago_today(now, 3)
    link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC", "DDDD-DDDD", "EEEE-EEEE"]
    # older
    link_factory(creation_timestamp=three_years_ago, guid=link_pks[0], created_by=link_user)
    # old
    link_factory(creation_timestamp=two_years_ago, guid=link_pks[1], created_by=link_user)
    # now
    link_factory(creation_timestamp=now, guid=link_pks[2], created_by=link_user)
    link_factory(creation_timestamp=now, guid=link_pks[3], created_by=link_user)
    link_factory(creation_timestamp=now, guid=link_pks[4], created_by=link_user)

    links = Link.objects.filter(pk__in=link_pks)
    assert len(links) == 5
    assert link_count_in_time_period(links, three_years_ago, two_years_ago) == 2


def test_org_link_count_this_year(registrar, organization_factory, link_user, link_factory):
    '''
        Should include links created this year and exclude links
        older than that.
    '''
    o = organization_factory(registrar=registrar)
    assert o.link_count_this_year() == 0

    now = tz_datetime(timezone.now().year, 1, 1)
    two_years_ago = years_ago_today(now, 2)
    link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC"]
    # too early
    link_factory(creation_timestamp=two_years_ago, guid=link_pks[0], created_by=link_user, organization=o)
    # now
    link_factory(creation_timestamp=now, guid=link_pks[1], created_by=link_user, organization=o)
    link_factory(creation_timestamp=now, guid=link_pks[2], created_by=link_user, organization=o)
    links = Link.objects.filter(pk__in=link_pks)
    assert len(links) == 3
    assert o.link_count_this_year() == 2


def test_registrar_link_count_this_year(registrar, organization_factory, link_user, link_factory):
    '''
        Should include links created this year and exclude links
        older than that. Should work across all its orgs.
    '''
    o1 = organization_factory(registrar=registrar)
    o2 = organization_factory(registrar=registrar)

    now = tz_datetime(timezone.now().year, 1, 1)
    two_years_ago = years_ago_today(now, 2)
    link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC", "DDDD-DDDD"]
    # too early
    link_factory(creation_timestamp=two_years_ago, guid=link_pks[0], created_by=link_user, organization=o1)
    # now
    link_factory(creation_timestamp=now, guid=link_pks[1], created_by=link_user, organization=o1)
    link_factory(creation_timestamp=now, guid=link_pks[2], created_by=link_user, organization=o1)
    link_factory(creation_timestamp=now, guid=link_pks[3], created_by=link_user, organization=o2)

    links = Link.objects.filter(pk__in=link_pks)
    assert len(links) == 4
    assert registrar.link_count_this_year() == 3


#
# Assess org activity
#

def test_most_active_org_in_time_period_no_links(registrar, organization_factory):
    '''
        If no orgs with links in period, should return None
    '''
    organization_factory(registrar=registrar)
    organization_factory(registrar=registrar)
    assert most_active_org_in_time_period(registrar.organizations) is None


def test_most_active_org_in_time_period_invalid_dates(registrar):
    '''
        If end date is before start date, should raise an exception
    '''
    now = tz_datetime(timezone.now().year, 1, 1)
    later = tz_datetime(now.year + 1, 1, 1)
    with pytest.raises(ValueError):
        most_active_org_in_time_period(registrar.organizations, later, now)


def test_most_active_org_in_time_period_valid_period(registrar, organization_factory, link_user, link_factory):
    '''
        Should include links created only in the target year
    '''
    now = tz_datetime(timezone.now().year, 1, 1)
    two_years_ago = years_ago_today(now, 2)
    three_years_ago = years_ago_today(now, 3)

    o1 = organization_factory(registrar=registrar)
    o2 = organization_factory(registrar=registrar)
    link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC", "DDDD-DDDD", "EEEE-EEEE"]

    # too early
    link_factory(creation_timestamp=three_years_ago, guid=link_pks[0], organization=o1, created_by=link_user)
    link_factory(creation_timestamp=three_years_ago, guid=link_pks[1], organization=o1, created_by=link_user)

    # now
    link_factory(creation_timestamp=now, guid=link_pks[2], organization=o1, created_by=link_user)
    link_factory(creation_timestamp=now, guid=link_pks[3], organization=o2, created_by=link_user)
    link_factory(creation_timestamp=now, guid=link_pks[4], organization=o2, created_by=link_user)

    # organization 1 was more active in the past
    assert most_active_org_in_time_period(registrar.organizations, three_years_ago, two_years_ago) == o1
    # but organization 2 was more active during the period in question
    assert most_active_org_in_time_period(registrar.organizations, two_years_ago) == o2
    # with a total of three links, organization 1 has been more active over all
    assert most_active_org_in_time_period(registrar.organizations) == o1


def test_registrar_most_active_org_this_year(registrar, organization_factory, link_user, link_factory):
    '''
        Should return the org (whole object)with the most links
        created this year, or None if it has no orgs with links
        created this year.
    '''
    assert registrar.most_active_org_this_year() is None

    o1 = organization_factory(registrar=registrar)
    o2 = organization_factory(registrar=registrar)

    now = tz_datetime(timezone.now().year, 1, 1)
    two_years_ago = years_ago_today(now, 2)
    link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC", "DDDD-DDDD", "EEEE-EEEE", "FFFF-FFFF"]
    # too early
    link_factory(creation_timestamp=two_years_ago, guid=link_pks[0], created_by=link_user, organization=o1)
    assert registrar.most_active_org_this_year() is None

    # now
    link_factory(creation_timestamp=now, guid=link_pks[1], created_by=link_user, organization=o1)
    link_factory(creation_timestamp=now, guid=link_pks[2], created_by=link_user, organization=o1)
    link_factory(creation_timestamp=now, guid=link_pks[3], created_by=link_user, organization=o2)

    assert registrar.most_active_org_this_year() == o1

    # now
    link_factory(creation_timestamp=now, guid=link_pks[4], created_by=link_user, organization=o2)
    link_factory(creation_timestamp=now, guid=link_pks[5], created_by=link_user, organization=o2)

    assert registrar.most_active_org_this_year() == o2


#
# Link limit for sponsored users
#

def test_sponsored_links_not_counted_against_personal_total(sponsored_user, link_factory):
    assert sponsored_user.get_links_remaining()[0] == 10
    link = link_factory(creation_timestamp=timezone.now().replace(day=1), guid="AAAA-AAAA", created_by=sponsored_user)

    assert sponsored_user.get_links_remaining()[0] == 9
    link.move_to_folder_for_user(sponsored_user.sponsorships.first().folders.first(), sponsored_user)
    assert sponsored_user.get_links_remaining()[0] == 10


#
# Link limit / subscription related tests for registrars
#


def test_renaming_registrar_renames_top_level_sponsored_folders(registrar, sponsorship_factory):
    new_name = 'A New Name'
    sponsorship_factory(registrar=registrar)
    sponsored_folders = Folder.objects.filter(sponsored_by=registrar).prefetch_related('parent')
    assert registrar.name != new_name and sponsored_folders
    for folder in sponsored_folders:
        if folder.parent.is_sponsored_root_folder:
            assert folder.name == registrar.name
        else:
            assert folder.name != registrar.name
    registrar.name = new_name
    # You need to save if you use refresh_from_db
    registrar.save()
    registrar.refresh_from_db()
    sponsored_folders = sponsored_folders.all()  # hack to refresh queryset
    assert registrar.name == new_name and sponsored_folders
    for folder in sponsored_folders:
        if folder.parent.is_sponsored_root_folder:
            assert folder.name == registrar.name
        else:
            assert folder.name == registrar.name

#
# Moving bonus links around
#

def test_move_bonus_link_to_another_personal_subfolder(complex_user_with_bonus_link):
    user, bonus_link = complex_user_with_bonus_link
    subfolder = user.folders.get(name="Subfolder")

    # establish baseline
    links_remaining, _ , bonus_links = user.get_links_remaining()
    assert links_remaining == 2
    assert bonus_links == 0

    bonus_link.move_to_folder_for_user(subfolder, user)
    user.refresh_from_db()

    # assert that nothing changed
    links_remaining, _ , bonus_links = user.get_links_remaining()
    assert links_remaining == 2
    assert bonus_links == 0


def test_move_bonus_link_to_sponsored_folder(complex_user_with_bonus_link):
    user, bonus_link = complex_user_with_bonus_link
    sponsorship = Sponsorship.objects.get(user=user)
    sponsored_folder = Folder.objects.get(name=sponsorship.registrar)

    # establish baseline
    links_remaining, _ , bonus_links = user.get_links_remaining()
    assert links_remaining == 2
    assert bonus_links == 0

    bonus_link.move_to_folder_for_user(sponsored_folder, user)
    user.refresh_from_db()

    # the user should be credited for the bonus link
    links_remaining, _ , bonus_links = user.get_links_remaining()
    assert links_remaining == 2
    assert bonus_links == 1

    # the link should no longer be a bonus link
    bonus_link.refresh_from_db()
    assert not bonus_link.bonus_link

def test_move_bonus_link_to_org_folder(complex_user_with_bonus_link):
    user, bonus_link = complex_user_with_bonus_link
    org_folder = Folder.objects.get(name="Test Journal")

    # establish baseline
    links_remaining, _ , bonus_links = user.get_links_remaining()
    assert links_remaining == 2
    assert bonus_links == 0

    bonus_link.move_to_folder_for_user(org_folder, user)
    user.refresh_from_db()

    # the user should be credited for the bonus link
    links_remaining, _ , bonus_links = user.get_links_remaining()
    assert links_remaining == 2
    assert bonus_links == 1

    # the link should no longer be a bonus link
    bonus_link.refresh_from_db()
    assert not bonus_link.bonus_link

def test_move_subfolder_with_bonus_links_to_sponsored_folder(complex_user_with_bonus_link):
    user, bonus_link = complex_user_with_bonus_link
    subfolder = user.folders.get(name="Subfolder")
    bonus_link.move_to_folder_for_user(subfolder, user)
    sponsorship = Sponsorship.objects.get(user=user)
    sponsored_folder = Folder.objects.get(name=sponsorship.registrar)

    # establish baseline
    links_remaining, _ , bonus_links = user.get_links_remaining()
    assert links_remaining == 2
    assert bonus_links == 0

    subfolder.parent = sponsored_folder
    subfolder.save()
    user.refresh_from_db()

    # the user should be credited for the bonus link
    links_remaining, _ , bonus_links = user.get_links_remaining()
    assert links_remaining == 2
    assert bonus_links == 1

    # the link should no longer be a bonus link
    bonus_link.refresh_from_db()
    assert not bonus_link.bonus_link

def test_move_subfolder_with_bonus_links_to_org_folder(complex_user_with_bonus_link):
    user, bonus_link = complex_user_with_bonus_link
    subfolder = user.folders.get(name="Subfolder")
    bonus_link.move_to_folder_for_user(subfolder, user)
    org_folder = Folder.objects.get(name="Test Journal")

    # establish baseline
    links_remaining, _ , bonus_links = user.get_links_remaining()
    assert links_remaining == 2
    assert bonus_links == 0

    subfolder.parent = org_folder
    subfolder.save()
    user.refresh_from_db()

    # the user should be credited for the bonus link
    links_remaining, _ , bonus_links = user.get_links_remaining()
    assert links_remaining == 2
    assert bonus_links == 1

    # the link should no longer be a bonus link
    bonus_link.refresh_from_db()
    assert not bonus_link.bonus_link
