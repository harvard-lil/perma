import calendar
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models, transaction
from django.utils import timezone
from django.utils.functional import cached_property
from django.views.decorators.debug import sensitive_variables
import requests
import logging

from perma.exceptions import InvalidTransmissionException, PermaPaymentsCommunicationException
from perma.utils import (
    pp_date_from_post,
    prep_for_perma_payments,
    process_perma_payments_transmission,
    today_next_month,
    today_next_year,
)

logger = logging.getLogger(__name__)


### CONSTANTS
ACTIVE_SUBSCRIPTION_STATUSES = ['Current', 'Cancellation Requested']
PROBLEM_SUBSCRIPTION_STATUSES = ['Hold']

FIELDS_REQUIRED_FROM_PERMA_PAYMENTS = {
    'get_subscription': [
        'customer_pk',
        'customer_type',
        'subscription',
        'purchases'
    ],
    'get_purchase_history': [
        'customer_pk',
        'customer_type',
        'purchase_history'
    ]
}

CUSTOMER_TYPE_MAP = {
    'LinkUser': 'Individual',
    'Registrar': 'Registrar'
}

def subscription_is_active(subscription):
    return subscription and (
        subscription['status'] in ACTIVE_SUBSCRIPTION_STATUSES or (
            subscription['status'] == "Canceled" and
            subscription['paid_through'] and
            subscription['paid_through'] >= timezone.now()
        )
    )

def subscription_has_problem(subscription):
    return subscription and subscription['status'] in PROBLEM_SUBSCRIPTION_STATUSES



class CustomerModel(models.Model):
    """
        Abstract base class that lets a model upgrade to a paid account.
    """
    class Meta:
        abstract = True

    nonpaying = models.BooleanField(default=False, help_text="Whether this customer qualifies for a free account.")
    in_trial = models.BooleanField(default=True, help_text="Is this customer in their trial period?")
    base_rate =  models.DecimalField(
        max_digits=19,
        decimal_places=2,
        default=Decimal(settings.DEFAULT_BASE_RATE),
        help_text="Base rate for calculating subscription cost."
    )
    # Local subscription descriptions are a temporary measure for improving user experience.
    # See LIL-5430.
    local_subscription_description = models.TextField(
        default="",
        blank=True,
        help_text="Special text that appears on the usage plan page, describing this customer's subscription."
    )
    # "Offer" display options are a temporary measure for controlling which products are offered to particular customers.
    # See LIL-5472.
    offer_monthly = models.BooleanField(default=True)
    offer_annual = models.BooleanField(default=True)
    cached_subscription_started = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Used to help calculate how many links have been created against a paying customer's link limit."
    )
    cached_subscription_status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="The last known status of customer's paid subscription, from Perma Payments"
    )
    cached_paid_through = models.DateTimeField(
        null=True,
        blank=True
    )
    cached_subscription_rate = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Local record of what the customer last paid."
    )
    unlimited = models.BooleanField(default=False, help_text="If unlimited, link_limit and related fields are ignored.")
    link_limit = models.IntegerField(default=settings.DEFAULT_CREATE_LIMIT)
    link_limit_period = models.CharField(max_length=8, default=settings.DEFAULT_CREATE_LIMIT_PERIOD, choices=(('once','once'),('monthly','monthly'),('annually','annually')))
    bonus_links = models.PositiveIntegerField(blank=True, null=True)
    frozen = models.BooleanField(
        default=False,
        help_text="If frozen, this account cannot create links regardless of subscription or "
                  "bonus links. Set when enforcing a dispute or refund; clear to restore access."
    )

    @cached_property
    def customer_type(self):
        return CUSTOMER_TYPE_MAP[type(self).__name__]

    def payments_customer_name(self):
        """
        The name to send to the payments service, so Stripe invoices and
        receipts show it under "Bill to" instead of an internal customer
        description (LIL-5399).

        Registrars only: an organization name is not personal data, while an
        individual's name is, and the payments service deliberately holds no
        individual PII. Individuals supply a name themselves at Stripe Checkout.
        """
        if self.customer_type != 'Registrar':
            return None
        return (getattr(self, 'name', '') or '').strip() or None

    @sensitive_variables()
    def get_purchase_history(self):
        if self.nonpaying:
            return None

        try:
            r = requests.post(
                settings.PAYMENTS_APP_URLS['purchase_history'],
                timeout=settings.PERMA_PAYMENTS_TIMEOUT,
                data={
                    'encrypted_data': prep_for_perma_payments({
                        'timestamp': datetime.utcnow().timestamp(),
                        'customer_pk':  self.pk,
                        'customer_type': self.customer_type
                    })
                }
            )
            assert r.ok, r.status_code
        except (requests.RequestException, AssertionError, ImproperlyConfigured) as e:
            msg = f"Communication with Perma-Payments failed: {e}"
            if settings.PERMA_PAYMENTS_IN_MAINTENANCE:
                logger.info(msg)
            else:
                logger.error(msg)
            raise PermaPaymentsCommunicationException(msg)

        post_data = process_perma_payments_transmission(r.json(), FIELDS_REQUIRED_FROM_PERMA_PAYMENTS['get_purchase_history'])

        if post_data['customer_pk'] != self.pk or post_data['customer_type'] != self.customer_type:
            msg = "Unexpected response from Perma-Payments."
            logger.error(msg)
            raise InvalidTransmissionException(msg)

        return {
            'purchases': [
                {
                    'link_quantity': item['link_quantity'],
                    'date': pp_date_from_post(item['date']),
                    'reference_number': item['reference_number']
                } for item in post_data['purchase_history']
            ],
            'total_links': sum(int(purchase['link_quantity']) for purchase in post_data['purchase_history'])
        }


    @sensitive_variables()
    def get_subscription(self):
        if self.nonpaying:
            return None

        try:
            r = requests.post(
                settings.PAYMENTS_APP_URLS['subscription_status'],
                timeout=settings.PERMA_PAYMENTS_TIMEOUT,
                data={
                    'encrypted_data': prep_for_perma_payments({
                        'timestamp': datetime.utcnow().timestamp(),
                        'customer_pk':  self.pk,
                        'customer_type': self.customer_type
                    })
                }
            )
            assert r.ok, r.status_code
        except (requests.RequestException, AssertionError, ImproperlyConfigured) as e:
            msg = f"Communication with Perma-Payments failed: {e}"
            if settings.PERMA_PAYMENTS_IN_MAINTENANCE:
                logger.info(msg)
            else:
                logger.error(msg)
            raise PermaPaymentsCommunicationException(msg)

        post_data = process_perma_payments_transmission(r.json(), FIELDS_REQUIRED_FROM_PERMA_PAYMENTS['get_subscription'])

        if post_data['customer_pk'] != self.pk or post_data['customer_type'] != self.customer_type:
            msg = "Unexpected response from Perma-Payments."
            logger.error(msg)
            raise InvalidTransmissionException(msg)

        #
        # First, credit the user for any bonus links they have purchased.
        #
        if post_data['purchases']:
            self.credit_for_purchased_links(post_data['purchases'])

        #
        # Then, handle subscription-related concerns
        #

        if post_data['subscription'] is None:
            if self.cached_subscription_started:
                # reset this, so that link counts work properly if the customer
                # purchases a new subscription in the future
                self.cached_subscription_started = None
                self.save(update_fields=['cached_subscription_started'])
                self.refresh_from_db()
            return None

        # Alert Perma that this user is no longer in their trial period.
        # Store the subscription status locally, for use if Perma Payments is unavailable
        # and update local link limit and rate to match Perma Payments' records
        subscription_change_effective = pp_date_from_post(post_data['subscription']['link_limit_effective_timestamp'])
        self.in_trial = False
        if not self.cached_subscription_started:
            self.cached_subscription_started = subscription_change_effective
        self.cached_subscription_status = post_data['subscription']['status']
        self.cached_paid_through = pp_date_from_post(post_data['subscription']['paid_through'])

        # Perma Payments reports any scheduled downgrade in pending_change.
        # While one is pending, leave the local tier fields alone: they
        # already hold the current tier.
        pending_change = post_data['subscription']['pending_change']
        if pending_change:
            pending_change = {
                'rate': pending_change['rate'],
                'link_limit': pending_change['link_limit'],
                # downgrades can't switch between monthly and annual billing,
                # so the pending change keeps the subscription's frequency
                'frequency': post_data['subscription']['frequency'],
                'effective': pp_date_from_post(pending_change['effective']),
            }
        else:
            self.link_limit_period = post_data['subscription']['frequency']
            self.cached_subscription_rate = Decimal(post_data['subscription']['rate'])
            if post_data['subscription']['link_limit'] == 'unlimited':
                self.unlimited = True
            else:
                self.unlimited = False
                self.link_limit = int(post_data['subscription']['link_limit'])
        self.save(update_fields=['in_trial', 'cached_subscription_started', 'cached_subscription_status', 'cached_paid_through', 'cached_subscription_rate', 'unlimited', 'link_limit', 'link_limit_period'])
        self.refresh_from_db()

        return {
            'status': self.cached_subscription_status,
            'frequency': self.link_limit_period,
            'paid_through': self.cached_paid_through,
            'rate': str(self.cached_subscription_rate),
            'link_limit': 'unlimited' if self.unlimited else str(self.link_limit),
            'pending_change': pending_change,
            'reference_number': post_data['subscription']['reference_number'],
        }

    def annotate_tier(self, tier, current_subscription, now, next_month, next_year):
        '''
        Mutates the passed-in tier dictionary, adding time- and subscription-specific details.
        '''

        # Calculate when, after today, the customer will/should next be charged.
        if tier['period'] == 'monthly':
            # montly subscriptions are now paid on the anniversary of their creation.
            # historically, monthly subscriptions were all paid on the first of the month.
            if current_subscription:
                # n.b. these values are nonsensical if the current subscription is not active.
                # there is no good answer in that case.... so updating a non-active
                # subscription is forbidden below. continuing to calculate the nonsensical values
                # for these fields since.... that at least avoids type errors.
                next_payment = current_subscription['paid_through']
                days_in_month = calendar.monthrange(now.year, now.month)[1]
                prorated_ratio = Decimal((next_payment - now).days / days_in_month)
            else:
                next_payment = next_month
                prorated_ratio  = Decimal(1)
        elif tier['period'] == 'annually':
            # annual subscriptions are paid on the anniversary of their creation
            if current_subscription:
                # n.b. these values are nonsensical if the current subscription is not active.
                # there is no good answer in that case.... so updating a non-active
                # subscription is forbidden below. continuing to calculate the nonsensical values
                # for these fields since.... that at least avoids type errors.
                next_payment = current_subscription['paid_through']
                prorated_ratio  = Decimal((next_payment - now).days / 365)  # ignore leap year
            else:
                next_payment = next_year
                prorated_ratio  = Decimal(1)
        else:
            raise NotImplementedError(f'Paid "{tier["frequency"]}" tiers not yet supported')

        # Customers without subscriptions may upgrade to any tier.
        #
        # Customers with existing non-active subscriptions may not upgrade or downgrade.
        #
        # Customers with existing active subscriptions may upgrade/downgrade
        # to another tier with the same link limit period/payment frequency.
        #
        # Upgrades are effective immediately. Today, customers should be
        # charged the prorated cost of the difference between their current
        # subscription tier and tier they are upgrading to.
        #
        # Downgrades are effective the next time their subscription renews.
        # The current subscription period will not be affected: customers
        # should not be charged today.
        #
        # If a customer has already scheduled a downgrade for the next
        # subscription period, all tiers should be unavailable;
        # the cancellation of scheduled downgrades is handled elsewhere.
        tier_rate = self.base_rate * Decimal(tier['rate_ratio'])

        if not current_subscription:
            tier_type = 'upgrade'
            todays_charge = prorated_ratio * tier_rate
        elif not current_subscription['status'] == 'Current' \
             or tier['period'] != current_subscription['frequency'] \
             or current_subscription.get('pending_change'):
            tier_type = 'unavailable'
            todays_charge = Decimal(0)
        else:
            current_limit = float('Inf') if current_subscription['link_limit'] == 'unlimited' else float(current_subscription['link_limit'])
            tier_limit = float('Inf') if tier['link_limit'] == 'unlimited' else float(tier['link_limit'])
            current_rate = Decimal(current_subscription['rate'])

            if tier_rate == current_rate and tier_limit == current_limit:
                tier_type = 'selected'
                todays_charge = Decimal(0)
            elif tier_rate <= current_rate:
                if tier_limit >= current_limit:
                    # This means the customer is overpaying, by today's standards.
                    # We should not let this happen: solve by granting the user
                    # more links for their money, via the Perma Payments admin,
                    # when we lower our tier prices.
                    logger.error(f"{str(self)} is being overcharged subsequent to new Perma subscription tiers.")
                    tier_type = 'unavailable'
                    todays_charge = Decimal(0)
                else:
                    tier_type = 'downgrade'
                    todays_charge = Decimal(0)
            else:
                if tier_limit <= current_limit:
                    # This means the customer is underpaying, by today's standards.
                    # We should not let them upgrade in the normal way.
                    # If we don't want this to happen, we should work it out via
                    # the Perma admin, the Perma Payments admin, and/or Stripe Dashboard.
                    tier_type = 'unavailable'
                    todays_charge = Decimal(0)
                else:
                    tier_type = 'upgrade'
                    todays_charge = prorated_ratio * (tier_rate - current_rate)

        tier.update({
            'type': tier_type,
            'link_limit': str(tier['link_limit']),
            'link_limit_effective_timestamp': now.timestamp() if tier_type == 'upgrade' else next_payment.timestamp(),
            'todays_charge': "{0:.2f}".format(todays_charge.quantize(Decimal('.01'))),
            'recurring_amount': "{0:.2f}".format(tier_rate),
            'recurring_start_date': next_payment.strftime("%Y-%m-%d"),
            'next_payment': next_payment
        })

    def get_subscription_info(self, now):
        timestamp = now.timestamp()
        next_month = today_next_month(now)
        next_year = today_next_year(now)
        subscription = self.get_subscription()
        customer_name = self.payments_customer_name()

        tiers = []
        if subscription and subscription.get('pending_change'):
            # allow the user to effective cancel the pending change,
            # reverting to / rescheduling whatever is on record as
            # their "current" subscription, in Perma
            required_fields = {
                'customer_pk': self.pk,
                'customer_type': self.customer_type,
                'timestamp': timestamp,
                'amount': '0.00',
                'recurring_amount': subscription['rate'],
                'recurring_frequency': subscription['frequency'],
                'recurring_start_date': subscription['paid_through'].strftime("%Y-%m-%d"),
                'link_limit': subscription['link_limit'],
                'link_limit_effective_timestamp': now.timestamp()
            }
            tiers.append({
                'type': 'cancel_downgrade',
                'period': subscription['frequency'],
                'limit': subscription['link_limit'],
                'rate': subscription['rate'],
                'next_payment': subscription['paid_through'].strftime("%Y-%m-%d"),
                'required_fields': required_fields,
                'encrypted_data': prep_for_perma_payments(required_fields).decode('utf-8')
            })
        else:
            for tier in settings.TIERS[self.customer_type]:
                self.annotate_tier(tier, subscription, now, next_month, next_year)
                required_fields = {
                    'customer_pk': self.pk,
                    'customer_type': self.customer_type,
                    'timestamp': timestamp,
                    'amount': tier['todays_charge'],
                    'recurring_amount': tier['recurring_amount'],
                    'recurring_frequency': tier['period'],
                    'recurring_start_date': tier['recurring_start_date'],
                    'link_limit': tier['link_limit'],
                    'link_limit_effective_timestamp': tier['link_limit_effective_timestamp']
                }
                if customer_name:
                    required_fields['customer_name'] = customer_name
                tiers.append({
                    'type': tier['type'],
                    'period': tier['period'],
                    'limit': tier['link_limit'],
                    'rate': tier['recurring_amount'],
                    'next_payment': tier['next_payment'],
                    'required_fields': required_fields,
                    'encrypted_data': prep_for_perma_payments(required_fields).decode('utf-8')
                })

        return {
            'customer': self,
            'subscription': subscription,
            'tiers': tiers,
            'can_change_tiers': any(tier['type'] in ['upgrade', 'downgrade', 'cancel_downgrade'] for tier in tiers)
        }

    def credit_for_purchased_links(self, purchases):
        credited_link_count = 0
        for purchase in purchases:
            try:
                with transaction.atomic():
                    link_quantity = int(purchase["link_quantity"])
                    self.bonus_links = (self.bonus_links or 0) + link_quantity
                    self.save(update_fields=['bonus_links'])
                    try:
                        r = requests.post(
                            settings.PAYMENTS_APP_URLS['acknowledge_purchase'],
                            timeout=settings.PERMA_PAYMENTS_TIMEOUT,
                            data={
                                'encrypted_data': prep_for_perma_payments({
                                    'timestamp': datetime.utcnow().timestamp(),
                                    'purchase_pk':  purchase['id']
                                })
                            }
                        )
                        assert r.ok, r.status_code
                    except (requests.RequestException, AssertionError, ImproperlyConfigured) as e:
                        msg = f"Communication with Perma-Payments failed: {str(e)}"
                        if settings.PERMA_PAYMENTS_IN_MAINTENANCE:
                            logger.info(msg)
                        else:
                            logger.error(msg)
                        raise PermaPaymentsCommunicationException(msg)
                    credited_link_count += link_quantity
            except PermaPaymentsCommunicationException:
                # I think we want the function to return even if it fails...
                # We'll be notified via the error message, and the calling
                # can do its best to proceed... having failed to credit the user
                # for their links. (Presumably, the customer will also complain if failure persists.)
                pass
        return credited_link_count

    def get_bonus_packages(self):
        bonus_packages = []
        customer_name = self.payments_customer_name()
        for package in settings.BONUS_PACKAGES:
            required_fields = {
                'timestamp': datetime.utcnow().timestamp(),
                'customer_pk':  self.pk,
                'customer_type': self.customer_type,
                'amount': package['price'],
                'link_quantity': package['link_quantity']
            }
            if customer_name:
                required_fields['customer_name'] = customer_name
            bonus_packages.append({
                'amount': required_fields['amount'],
                'link_quantity': required_fields['link_quantity'],
                'unit_cost': float(required_fields['amount']) / int(required_fields['link_quantity']),
                'encrypted_data': prep_for_perma_payments(required_fields).decode('utf-8')
            })
        return bonus_packages


    @cached_property
    def subscription_status(self):
        try:
            subscription = self.get_subscription()
        except PermaPaymentsCommunicationException:
            subscription = {
                'status': self.cached_subscription_status,
                'paid_through': self.cached_paid_through
            }
        if subscription_is_active(subscription):
            return 'active'
        if subscription_has_problem(subscription):
            return 'problem'
        return None

    def link_creation_allowed(self):
        """
        Must be implemented by children
        """
        raise NotImplementedError
