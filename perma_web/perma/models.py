import calendar
from decimal import Decimal
from datetime import datetime
from dateutil.relativedelta import relativedelta
import hashlib
import io
import json
import os
import logging
import random
import re
import socket
from urllib.parse import urlencode
from urllib.parse import urlparse
import simple_history
import requests
import itertools
import time
import hmac
import uuid
from time import mktime
from wsgiref.handlers import format_date_time

from mptt.managers import TreeManager
from rest_framework.settings import api_settings
from simple_history.models import HistoricalRecords
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse

from django.core.signing import TimestampSigner, BadSignature
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
import django.contrib.auth.models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Q, Max, Count
from django.db.models.functions import Now
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from django.views.decorators.debug import sensitive_variables
from mptt.models import MPTTModel, TreeForeignKey
from model_utils import FieldTracker
from pywb.cdx.cdxobject import CDXObject
from pywb.warc.cdxindexer import write_cdx_index
from taggit.managers import TaggableManager
from taggit.models import CommonGenericTaggedItemBase, TaggedItemBase

from .exceptions import PermaPaymentsCommunicationException, InvalidTransmissionException, WebrecorderException
from .utils import (tz_datetime, protocol,
    prep_for_perma_payments, process_perma_payments_transmission,
    pp_date_from_post,
    first_day_of_next_month, today_next_year, preserve_perma_warc,
    write_resource_record_from_asset,
    get_wr_session, clear_wr_session, query_wr_api)


logger = logging.getLogger(__name__)

### CONSTANTS
ACTIVE_SUBSCRIPTION_STATUSES = ['Current', 'Cancellation Requested']
PROBLEM_SUBSCRIPTION_STATUSES = ['Hold']

FIELDS_REQUIRED_FROM_PERMA_PAYMENTS = {
    'get_subscription': [
        'customer_pk',
        'customer_type',
        'subscription',
    ]
}

CUSTOMER_TYPE_MAP = {
    'LinkUser': 'Individual',
    'Registrar': 'Registrar'
}


### HELPERS ###

# functions
def link_count_in_time_period(links, start_time=None, end_time=None):
    if start_time and end_time and (start_time > end_time):
        raise ValueError("specified end time is earlier than specified start time")
    elif start_time and end_time and (start_time == end_time):
        links = links.filter(creation_timestamp=start_time)
    else:
        if start_time:
            links = links.filter(creation_timestamp__gte=start_time)
        if end_time:
            links = links.filter(creation_timestamp__lte=end_time)
    return links.count()

def most_active_org_in_time_period(organizations, start_time=None, end_time=None):
    if start_time and end_time and (start_time > end_time):
        raise ValueError("specified end time is earlier than specified start time")
    # unlike 'link_count_in_time_period', no special behavior required
    # if start_time = end_time here. the end result is the same
    else:
        if start_time:
            organizations = organizations.filter(links__creation_timestamp__gte=start_time)
        if end_time:
            organizations = organizations.filter(links__creation_timestamp__lte=end_time)
        return organizations\
            .annotate(num_links=Count('links'))\
            .exclude(num_links=0)\
            .order_by('-num_links')\
            .first()

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


# classes

class DeletableManager(models.Manager):
    """
        Manager that excludes results where user_deleted=True by default.
    """
    def get_queryset(self):
        # exclude deleted entries by default
        return super(DeletableManager, self).get_queryset().filter(user_deleted=False)

    def all_with_deleted(self):
        return super(DeletableManager, self).get_queryset()


class DeletableModel(models.Model):
    """
        Abstract base class that lets a model track deletion.
    """
    user_deleted = models.BooleanField(default=False, verbose_name="Deleted by user")
    user_deleted_timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def safe_delete(self):
        self.user_deleted = True
        self.user_deleted_timestamp = timezone.now()

# django-taggit assumes the model being tagged has an integer primary key.
# per http://django-taggit.readthedocs.io/en/latest/custom_tagging.html,
# tag "through" this class if your model has a string as primary key.
# tags = TaggableManager(through=GenericStringTaggedItem)
# (copied straight from their docs)
class GenericStringTaggedItem(CommonGenericTaggedItemBase, TaggedItemBase):
    object_id = models.CharField(max_length=50, db_index=True)


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

    @cached_property
    def customer_type(self):
        return CUSTOMER_TYPE_MAP[type(self).__name__]

    @sensitive_variables()
    def get_subscription(self):
        if self.nonpaying:
            return None

        try:
            r = requests.post(
                settings.SUBSCRIPTION_STATUS_URL,
                data={
                    'encrypted_data': prep_for_perma_payments({
                        'timestamp': datetime.utcnow().timestamp(),
                        'customer_pk':  self.pk,
                        'customer_type': self.customer_type
                    })
                }
            )
            assert r.ok
        except (requests.RequestException, AssertionError) as e:
            msg = "Communication with Perma-Payments failed: {}".format(str(e))
            logger.error(msg)
            raise PermaPaymentsCommunicationException(msg)

        post_data = process_perma_payments_transmission(r.json(), FIELDS_REQUIRED_FROM_PERMA_PAYMENTS['get_subscription'])

        if post_data['customer_pk'] != self.pk or post_data['customer_type'] != self.customer_type:
            msg = "Unexpected response from Perma-Payments."
            logger.error(msg)
            raise InvalidTransmissionException(msg)

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

        pending_change = None
        if subscription_change_effective <= timezone.now():
            self.link_limit_period = post_data['subscription']['frequency']
            self.cached_subscription_rate = Decimal(post_data['subscription']['rate'])
            if post_data['subscription']['link_limit'] == 'unlimited':
                self.unlimited = True
            else:
                self.unlimited = False
                self.link_limit = int(post_data['subscription']['link_limit'])
        else:
            pending_change = {
                'rate': post_data['subscription']['rate'],
                'link_limit': post_data['subscription']['link_limit'],
                'effective': subscription_change_effective
            }
        self.save(update_fields=['in_trial', 'cached_subscription_started', 'cached_subscription_status', 'cached_paid_through', 'cached_subscription_rate', 'unlimited', 'link_limit', 'link_limit_period'])
        self.refresh_from_db()

        return {
            'status': self.cached_subscription_status,
            'frequency': self.link_limit_period,
            'paid_through': self.cached_paid_through,
            'rate': str(self.cached_subscription_rate),
            'link_limit': 'unlimited' if self.unlimited else str(self.link_limit),
            'pending_change': pending_change
        }

    def annotate_tier(self, tier, current_subscription, now, next_month, next_year):
        '''
        Mutates the passed-in tier dictionary, adding time- and subscription-specific details.
        '''

        # Calculate when, after today, the customer will/should next be charged.
        # Calculate what fraction of the current subscription period remains,
        # to use when determining how much to charge them today.
        if tier['period'] == 'monthly':
            # monthly subscriptions are paid on the first of the next month
            next_payment = next_month
            days_in_month = calendar.monthrange(now.year, now.month)[1]
            prorated_ratio = Decimal((next_payment - now).days / days_in_month)
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
            raise NotImplementedError('Paid "{}" tiers not yet supported'.format(tier['frequency']))

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
                    logger.error("{} is being overcharged subsequent to new Perma subscription tiers.".format(str(self)))
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
                    # the Perma admin, the Perma Payments admin, and/or CyberSource Business Center
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
        next_month = first_day_of_next_month(now)
        next_year = today_next_year(now)
        subscription = self.get_subscription()

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
                'encrypted_data': prep_for_perma_payments(required_fields)
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
                tiers.append({
                    'type': tier['type'],
                    'period': tier['period'],
                    'limit': tier['link_limit'],
                    'rate': tier['recurring_amount'],
                    'next_payment': tier['next_payment'],
                    'required_fields': required_fields,
                    'encrypted_data': prep_for_perma_payments(required_fields)
                })

        return {
            'customer': self,
            'subscription': subscription,
            'tiers': tiers,
            'can_change_tiers': any(tier['type'] in ['upgrade', 'downgrade', 'cancel_downgrade'] for tier in tiers)
        }

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


### MODELS ###

class RegistrarQuerySet(QuerySet):
    def approved(self):
        return self.filter(status="approved")

class Registrar(CustomerModel):
    """
    This is a library, a court, a firm, or similar.
    """
    name = models.CharField(max_length=400)
    email = models.EmailField(max_length=254)
    website = models.URLField(max_length=500)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    status = models.CharField(max_length=20, default='pending', choices=(('pending','pending'),('approved','approved'),('denied','denied')))

    show_partner_status = models.BooleanField(default=False, help_text="Whether to show this registrar in our list of partners.")
    partner_display_name = models.CharField(max_length=400, blank=True, null=True, help_text="Optional. Use this to override 'name' for the partner list.")
    logo = models.ImageField(upload_to='registrar_logos', blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    link_count = models.IntegerField(default=0) # A cache of the number of links under this registrars's purview (sum of all associated org links)

    objects = RegistrarQuerySet.as_manager()
    tracker = FieldTracker()
    history = HistoricalRecords()
    tags = TaggableManager(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def link_count_in_time_period(self, start_time=None, end_time=None):
        links = Link.objects.filter(organization__registrar=self)
        return link_count_in_time_period(links, start_time, end_time)

    def link_count_this_year(self):
        return self.link_count_in_time_period(tz_datetime(timezone.now().year, 1, 1))

    def most_active_org_in_time_period(self, start_time=None, end_time=None):
        return most_active_org_in_time_period(self.organizations, start_time, end_time)

    def most_active_org_this_year(self):
        return most_active_org_in_time_period(self.organizations, tz_datetime(timezone.now().year, 1, 1))

    def active_registrar_users(self):
        return self.users.filter(is_active=True)

    def link_creation_allowed(self):
        # No logic yet for handling paid Registrar customers with limits:
        # all paid-up Registrar customers get unlimited links.
        assert self.unlimited
        if self.nonpaying:
            return True
        return self.subscription_status == 'active'

Registrar._meta.get_field('nonpaying').default = True
Registrar._meta.get_field('unlimited').default = True
Registrar._meta.get_field('base_rate').default = Decimal(settings.DEFAULT_BASE_RATE_REGISTRAR)


class OrganizationQuerySet(QuerySet):
    def accessible_to(self, user):
        qset = self.user_access_filter(user)
        if qset is None:
            return self.none()
        else:
            return self.filter(qset)

    def user_access_filter(self, user):
        if user.is_organization_user:
            return Q(id__in=user.organizations.all())
        elif user.is_registrar_user():
            return Q(registrar_id=user.registrar_id)
        elif user.is_staff:
            return Q()  # all
        else:
            return None


OrganizationManager = DeletableManager.from_queryset(OrganizationQuerySet)


class Organization(DeletableModel):
    """
    This is generally a journal.
    """
    name = models.CharField(max_length=400)
    registrar = models.ForeignKey(Registrar, null=True, related_name="organizations", on_delete=models.CASCADE)
    shared_folder = models.OneToOneField('Folder', blank=True, null=True, related_name="top_level_for_org")
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    default_to_private = models.BooleanField(default=False)
    link_count = models.IntegerField(default=0) # A cache of the number of links under this org's purview

    objects = OrganizationManager()
    tracker = FieldTracker()
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        name_has_changed = self.tracker.has_changed('name')
        super(Organization, self).save(*args, **kwargs)
        if not self.shared_folder:
            # Make sure shared folder is created for each org.
            self.create_shared_folder()
        elif name_has_changed:
            # Rename shared folder if org name changes.
            self.shared_folder.name = self.name
            self.shared_folder.save()

    def __str__(self):
        return self.name

    def create_shared_folder(self):
        if self.shared_folder:
            return
        shared_folder = Folder(name=self.name, organization=self, is_shared_folder=True)
        shared_folder.save()
        self.shared_folder = shared_folder
        self.save()

    def link_count_in_time_period(self, start_time=None, end_time=None):
        links = Link.objects.filter(organization=self)
        return link_count_in_time_period(links, start_time, end_time)

    def link_count_this_year(self):
        return self.link_count_in_time_period(tz_datetime(timezone.now().year, 1, 1))

    def accessible_to(self, user):
        if user.is_staff:
            return True
        if user.is_registrar_user():
            return self.registrar_id == user.registrar_id
        return self.users.filter(pk=user.pk).exists()


class LinkUserManager(BaseUserManager):
    def create_user(self, email, registrar, organization, date_joined, first_name, last_name, authorized_by, confirmation_code, password=None):
        """
        Creates and saves a User with the given email, registrar and password.
        """

        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            registrar=registrar,
            date_joined = date_joined,
            first_name = first_name,
            last_name = last_name,
            authorized_by = authorized_by,
            confirmation_code = confirmation_code
        )

        user.set_password(password)
        user.save()

        user.organizations.add(organization)
        user.save()

        user.create_root_folder()

        return user


class LinkUser(CustomerModel, AbstractBaseUser):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        db_index=True,
        error_messages={'unique': u"A user with that email address already exists.",}
    )

    registrar = models.ForeignKey(Registrar, blank=True, null=True, related_name='users', help_text="If set, this user is a registrar user. This should not be set if org is set!", on_delete=models.CASCADE)
    pending_registrar = models.ForeignKey(Registrar, blank=True, null=True, related_name='pending_users')
    organizations = models.ManyToManyField(Organization, blank=True, related_name='users',
                                           help_text="If set, this user is an org user. This should not be set if registrar is set!<br><br>"
                                                     "Note: <b>This list will include deleted orgs of which this user is a member.</b> This is a historical"
                                                     " record and deleted org memberships cannot be removed.<br><br>"
                                           )
    is_active = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=45, blank=True)
    last_name = models.CharField(max_length=45, blank=True)
    confirmation_code = models.CharField(max_length=45, blank=True)
    root_folder = models.OneToOneField('Folder', blank=True, null=True)
    requested_account_type = models.CharField(max_length=45, blank=True, null=True)
    requested_account_note = models.CharField(max_length=45, blank=True, null=True)
    link_count = models.IntegerField(default=0) # A cache of the number of links created by this user
    notes = models.TextField(blank=True)

    objects = LinkUserManager()
    tracker = FieldTracker()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'

    def save(self, *args, **kwargs):
        super(LinkUser, self).save(*args, **kwargs)

        # make sure root folder is created for each user.
        if not self.root_folder:
            self.create_root_folder()

    def get_full_name(self):
        """ Use either First Last or first half of email address as user's name. """
        return "%s %s" % (self.first_name, self.last_name) if self.first_name or self.last_name else \
            self.email.split('@')[0]

    def get_short_name(self):
        """ Use either First or Last or first half of email address as user's short name. """
        return self.first_name or self.last_name or self.email.split('@')[0]

    def __str__(self):
        return self.email

    def save_new_confirmation_code(self):
        self.confirmation_code = get_random_string(length=30)
        self.save()

    def top_level_folders(self):
        """
            Get top level folders for this user, including personal folder and shared folders.
        """
        orgs = self.get_orgs().select_related('shared_folder')
        return [self.root_folder] + [org.shared_folder for org in orgs if org]

    def all_folder_trees(self):
        """
            Get all folders for this user, including personal folders and shared folders.
        """
        return [folder.get_descendants(include_self=True) for folder in self.top_level_folders()]

    def get_orgs(self):
        """
            Get organizations in which this user is a member
        """

        if self.is_organization_user:
            return self.organizations.all()
        if self.is_registrar_user():
            return self.registrar.organizations.all()
        if self.is_staff:
            return Organization.objects.all()

        return Organization.objects.none()

    def create_root_folder(self):
        if self.root_folder:
            return
        try:
            # this branch only used during transition to root folders -- should be removed eventually
            root_folder = Folder.objects.filter(created_by=self, name=u"Personal Links", parent=None)[0]
            root_folder.is_root_folder = True
        except IndexError:
            root_folder = Folder(name=u'Personal Links', created_by=self, is_root_folder=True)
        root_folder.save()
        self.root_folder = root_folder
        self.save()

    def as_json(self):
        from api.serializers import LinkUserSerializer  # local import to avoid circular import
        return json.dumps(LinkUserSerializer(self).data)

    ### permissions ###

    def has_perm(self, perm, obj=None):
        """
            Does the user have a specific permission?
            Simplest possible answer: Yes, always
            This is only used by the django admin for is_staff=True users.
        """
        return True

    def has_module_perms(self, app_label):
        """
            Does the user have permissions to view the app `app_label`?
            Simplest possible answer: Yes, always
            This is only used by the django admin for is_staff=True users.
        """
        return True

    def shares_scope_with_user(self, other_user):
        """
            Does the user share a scope with another user?

            Org users share scope with other members of their orgs.
            Registrar users share scope with others registrar users from
               the same registrar, as well as all members of the registrar's orgs.
            Admins share scope with all users.
        """
        if self.is_organization_user:
            orgs = other_user.organizations.all() & self.organizations.all()
            return len(orgs) > 0
        elif self.is_registrar_user():
            if self.registrar == other_user.registrar:
                return True
            orgs = other_user.organizations.all() & Organization.objects.filter(registrar=self.registrar)
            return len(orgs) > 0
        elif self.is_staff:
            return True
        return False

    def is_individual(self):
        """ Is the user a regular, individual user? """
        return bool(not self.is_staff and not self.is_registrar_user() and not self.is_organization_user)

    def is_registrar_user(self):
        """ Is the user a member of a registrar? """
        return bool(self.registrar_id)

    def has_registrar_pending(self):
        """ Has requested creation of registrar """
        return bool(self.pending_registrar)

    @cached_property
    def is_organization_user(self):
        """ Is the user a member of an org? """
        if self.is_anonymous:
            return False
        return self.organizations.exists()

    def is_supported_by_registrar(self):
        """ Should the user's support requests be forwarded to their registrar?"""
        if self.is_anonymous:
            return False
        return settings.CONTACT_REGISTRARS and \
               self.is_organization_user

    ### link permissions ###

    def can_view(self, link):
        """
            Not all links are viewable by all users -- some users
            have privileged access to view private links. For example,
            a user can view their own private links.
        """
        if not link.is_private:
            return True
        return self.can_edit(link)

    def can_edit(self, link):
        """ Link is editable if it is in a folder accessible to this user. """
        if self.is_anonymous:
            return False
        if self.is_staff:
            return True
        return Folder.objects.accessible_to(self).filter(links=link).exists()

    def can_delete(self, link):
        """
            An archive can be deleted if it is less than 24 hours old-style
            and it was created by a user or someone in the org.
        """
        return not link.is_archive_eligible() and self.can_edit(link)

    def can_toggle_private(self, link):
        if not self.can_edit(link):
            return False
        if link.is_private and not self.is_staff and link.private_reason not in ['user', 'old_policy']:
            return False
        return True

    def can_edit_registrar(self, registrar):
        return self.is_staff or self.registrar == registrar

    def can_edit_organization(self, organization):
        return self.organizations.filter(pk=organization.pk).exists()

    ### subscriptions ###

    def links_remaining_in_period(self, period, limit, unlimited=None):
        today = timezone.now()

        # default to the value of self.unlimited; allow callers to explicitly override
        if unlimited is None:
            unlimited = self.unlimited

        if unlimited:
            # UNLIMITED (paid or sponsored)
            link_count = float("-inf")
        elif period == 'once':
            # TRIAL: all non-org links ever
            if self.cached_subscription_started:
                link_count = Link.objects.filter(creation_timestamp__range=(self.cached_subscription_started, today), created_by_id=self.id, organization_id=None).count()
            else:
                link_count = Link.objects.filter(created_by_id=self.id, organization_id=None).count()
        elif period == 'monthly':
            # MONTHLY RECURRING: links this calendar month (or, for new customers, links this month from the moment you started paying us)
            if self.cached_subscription_started and \
               self.cached_subscription_started.year == today.year and \
               self.cached_subscription_started.month == today.month:
                link_count = Link.objects.filter(creation_timestamp__range=(self.cached_subscription_started, today), created_by_id=self.id, organization_id=None).count()
            else:
                link_count = Link.objects.filter(creation_timestamp__year=today.year, creation_timestamp__month__gte=today.month, created_by_id=self.id, organization_id=None).count()
        elif period == 'annually':
            # ANNUAL RECURRING
            # if you have a paid subscription, calculate via its expiry date
            if self.cached_paid_through:
                link_count = Link.objects.filter(creation_timestamp__range=(self.cached_paid_through - relativedelta(years=1), today), created_by_id=self.id, organization_id=None).count()
            # else, check the last 365 days
            link_count = Link.objects.filter(creation_timestamp__range=(today - relativedelta(years=1), today), created_by_id=self.id, organization_id=None).count()
        else:
            raise NotImplementedError("User's link_limit_period not yet handled.")
        return max(limit - link_count, 0)

    def get_links_remaining(self):
        """
            Calculate how many personal links remain.
            Returns a tuple: (links, applicable period)
        """
        # Special handling for non-trial users who lack active paid subscriptions:
        # apply the same rules that are applied to new users
        if not self.in_trial and not self.nonpaying and self.subscription_status != 'active':
            return (self.links_remaining_in_period(settings.DEFAULT_CREATE_LIMIT_PERIOD, settings.DEFAULT_CREATE_LIMIT, unlimited=False), settings.DEFAULT_CREATE_LIMIT_PERIOD)
        return (self.links_remaining_in_period(self.link_limit_period, self.link_limit), self.link_limit_period)

    def link_creation_allowed(self):
        return self.get_links_remaining()[0] > 0

    def can_view_subscription(self):
        """
            Should the user be able to see the subscription page?
            Special non-paying users should not see the option to upgrade their personal account.
            Only authorized users should be able to see a paying registrar's subscription.
        """
        return not self.nonpaying or (self.is_registrar_user() and not self.registrar.nonpaying)


class ApiKey(models.Model):
    """
        Based on tastypie.models: https://github.com/django-tastypie/django-tastypie/blob/master/tastypie/models.py#L35
    """
    user = models.OneToOneField(LinkUser, related_name='api_key', on_delete=models.CASCADE)
    key = models.CharField(max_length=128, blank=True, default='', db_index=True)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return u"%s for %s" % (self.key, self.user)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ApiKey, self).save(*args, **kwargs)

    def generate_key(self):
        # Get a random UUID.
        new_uuid = uuid.uuid4()
        # Hmac that beast.
        return hmac.new(new_uuid.bytes, digestmod=hashlib.sha1).hexdigest()


# special history tracking for custom user object -- see http://django-simple-history.readthedocs.org/en/latest/reference.html
simple_history.register(LinkUser)

# This ugly business makes these functions available on logged-out users as well as logged-in,
# by monkeypatching Django's AnonymousUser object.
# See https://code.djangoproject.com/ticket/20313
for func_name in ['can_view', 'can_edit', 'can_delete', 'can_toggle_private', 'is_supported_by_registrar']:
    setattr(django.contrib.auth.models.AnonymousUser, func_name, getattr(LinkUser, func_name))
for prop_name in ['is_organization_user']:
    setattr(django.contrib.auth.models.AnonymousUser, prop_name, getattr(LinkUser, prop_name))

class FolderQuerySet(QuerySet):
    def user_access_filter(self, user):
        # personal folders
        filter = Q(owned_by=user)

        # folders owned by orgs in which the user a member
        orgs = user.get_orgs()
        if orgs:
            filter |= Q(organization__in=orgs)

        return filter

    def accessible_to(self, user):
        return self.filter(self.user_access_filter(user))


FolderManager = TreeManager.from_queryset(FolderQuerySet)


class Folder(MPTTModel):
    name = models.CharField(max_length=255, null=False, blank=False)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    creation_timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='folders_created', on_delete=models.CASCADE)

    # this may be null if this is the shared folder for a org
    owned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='folders', on_delete=models.CASCADE)

    # this will be set if this is inside a shared folder
    organization = models.ForeignKey(Organization, null=True, blank=True, related_name='folders', on_delete=models.CASCADE)

    # true if this is the apex shared folder (not subfolder) for a org
    is_shared_folder = models.BooleanField(default=False)

    # true if this is the apex folder for a user
    is_root_folder = models.BooleanField(default=False)

    objects = FolderManager()
    tracker = FieldTracker()

    def save(self, *args, **kwargs):
        # set defaults
        if not self.pk:
            # set ownership same as parent
            if self.parent:
                if self.parent.organization:
                    self.organization = self.parent.organization
                else:
                    self.owned_by = self.parent.owned_by
            if self.created_by and not self.owned_by and not self.organization:
                self.owned_by = self.created_by

        parent_has_changed = self.tracker.has_changed('parent_id')

        super(Folder, self).save(*args, **kwargs)

        if parent_has_changed:
            # make sure that child folders share organization and owned_by with new parent folder
            # (one or the other should be set, but not both)
            if self.parent.organization_id:
                self.get_descendants(include_self=True).update(organization=self.parent.organization_id, owned_by=None)
            else:
                self.get_descendants(include_self=True).update(owned_by=self.parent.owned_by_id, organization=None)

    class MPTTMeta:
        order_insertion_by = ['name']

    def is_empty(self):
        return not self.children.exists() and not self.links.exists()

    def __str__(self):
        return self.name

    def contained_links(self):
        return Link.objects.filter(folders__in=self.get_descendants(include_self=True))

    def display_level(self):
        """
            Get hierarchical level for this folder. If this is a shared folder, level should be one higher
            because it is displayed below user's root folder.
        """
        return self.level + (1 if self.organization_id else 0)

    def accessible_to(self, user):
        # staff can access any folder
        if user.is_staff:
            return True

        # private folders
        if self.owned_by_id == user.pk:
            return True

        # shared folders
        elif self.organization_id:
            if user.is_registrar_user():
                # if user is registrar, must be registrar for this org
                return user.registrar_id == self.organization.registrar_id
            else:
                # else, user must belong to this org
                return user.organizations.filter(pk=self.organization_id).exists()

class LinkQuerySet(QuerySet):
    def user_access_filter(self, user):
        """
            User can see/modify a link if they created it or it is in an org folder they belong to.
        """
        # personal links
        filter = Q(folders__owned_by=user)

        # links owned by orgs in which the user a member
        orgs = user.get_orgs()
        if orgs:
            filter |= Q(folders__organization__in=orgs)

        return filter

    def accessible_to(self, user):
        return self.filter(self.user_access_filter(user))

    def discoverable(self):
        """ Limit queryset to Links that can be publicly found by searching. """
        return self.filter(is_unlisted=False, is_private=False)

    def visible_to_lockss(self):
        """
            expose the bundled WARC if any non-favicon capture succeeded
        """
        capture_filter = (Q(role="primary") & Q(status="success")) | (Q(role="screenshot") & Q(status="success"))
        return self.filter(
            archive_timestamp__lte=timezone.now(),
            user_deleted=False,
            captures__in=Capture.objects.filter(capture_filter)
        ).exclude(
            private_reason__in=['user', 'takedown']
        ).distinct()


LinkManager = DeletableManager.from_queryset(LinkQuerySet)

class Link(DeletableModel):
    """
    This is the core of the Perma link.
    """
    guid = models.CharField(max_length=255, null=False, blank=False, primary_key=True, editable=False)
    GUID_CHARACTER_SET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    submitted_url = models.URLField(max_length=2100, null=False, blank=False)
    creation_timestamp = models.DateTimeField(default=timezone.now, editable=False)
    submitted_title = models.CharField(max_length=2100, null=False, blank=False)
    submitted_description = models.CharField(max_length=300, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='created_links', on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, null=True, blank=True, related_name='links', on_delete=models.CASCADE)
    folders = models.ManyToManyField(Folder, related_name='links', blank=True)
    notes = models.TextField(blank=True)
    internet_archive_upload_status = models.CharField(max_length=20,
                                                      default='not_started',
                                                      choices=(('not_started','not_started'),('completed','completed'),('failed','failed'),('failed_permanently','failed_permanently'),('deleted','deleted')))

    warc_size = models.IntegerField(blank=True, null=True)

    is_private = models.BooleanField(default=False)
    private_reason = models.CharField(max_length=10, blank=True, null=True, choices=(('policy','Perma-specific robots.txt or meta tag'), ('old_policy','Generic robots.txt or meta tag'),('user','At user direction'),('takedown','At request of content owner'),('failure','Analysis of meta tags failed')))
    is_unlisted = models.BooleanField(default=False)

    archive_timestamp = models.DateTimeField(blank=True, null=True, help_text="Date after which this link is eligible to be copied by the mirror network.")

    thumbnail_status = models.CharField(max_length=10, null=True, blank=True, choices=(
        ('generating', 'generating'), ('generated', 'generated'), ('failed', 'failed')))

    replacement_link = models.ForeignKey("Link", blank=True, null=True, help_text="New link to which readers should be forwarded when trying to view this link.", on_delete=models.CASCADE)

    objects = LinkManager()
    tracker = FieldTracker()
    history = HistoricalRecords()
    tags = TaggableManager(through=GenericStringTaggedItem, blank=True)

    @cached_property
    def ascii_safe_url(self):
        """ Encoded URL as string rather than unicode. """
        return requests.utils.requote_uri(self.submitted_url)

    @cached_property
    def url_details(self):
        return urlparse(self.ascii_safe_url)

    @cached_property
    def ip(self):
        try:
            return socket.gethostbyname(self.url_details.netloc.split(':')[0])
        except socket.gaierror:
            return False

    @cached_property
    def headers(self):
        try:
            return requests.get(
                self.ascii_safe_url,
                verify=False,  # don't check SSL cert?
                headers={'User-Agent': settings.CAPTURE_USER_AGENT, 'Accept-Encoding': '*'},
                timeout=settings.RESOURCE_LOAD_TIMEOUT,
                stream=True  # we're only looking at the headers
            ).headers
        except (requests.ConnectionError, requests.Timeout):
            return False


    # header values for memento: https://mementoweb.org/guide/rfc/

    @cached_property
    def memento(self):
        """
        http://perma.test:8000/23W3-NDSB
        """
        return protocol() + settings.HOST + '/' + self.guid

    @cached_property
    def timegate(self):
        """
        http://perma-archives.test:8000/warc/timegate/http://example.com
        """
        return protocol() + settings.PLAYBACK_HOST + settings.TIMEGATE_WARC_ROUTE + '/' + self.ascii_safe_url

    @cached_property
    def timemap(self):
        """
        http://perma-archives.test:8000/warc/timemap/*/http://example.com
        """
        return protocol() + settings.PLAYBACK_HOST + settings.WARC_ROUTE + '/timemap/*/' + self.ascii_safe_url

    @cached_property
    def memento_formatted_date(self):
        return format_date_time(mktime(self.creation_timestamp.timetuple()))

    def get_default_title(self):
        return self.url_details.netloc

    def save(self, *args, **kwargs):
        # Set a default title if one is missing
        if not self.submitted_title:
            self.submitted_title = self.get_default_title()

        initial_folder = kwargs.pop('initial_folder', None)

        if self.tracker.has_changed('is_unlisted') or self.tracker.has_changed('is_private'):
            CDXLine.objects.filter(link_id=self.pk).update(is_unlisted=self.is_unlisted, is_private=self.is_private)

        if not self.pk:
            if not self.archive_timestamp:
                self.archive_timestamp = self.creation_timestamp + settings.ARCHIVE_DELAY
            if not kwargs.pop("pregenerated_guid", False):
                # not self.pk => not created yet
                # only try 100 attempts at finding an unused GUID
                # (100 attempts should never be necessary, since we'll expand the keyspace long before
                # there are frequent collisions)
                r = random.SystemRandom()
                for i in range(100):
                    # Generate an 8-character random string like "1A2B3C4D"
                    guid = ''.join(r.choice(self.GUID_CHARACTER_SET) for _ in range(8))

                    # apply standard formatting (hyphens)
                    guid = Link.get_canonical_guid(guid)

                    # Avoid GUIDs starting with four letters (in case we need those later)
                    match = re.search(r'^[A-Z]{4}', guid)

                    if not match and not Link.objects.filter(guid=guid).exists():
                        break
                else:
                    raise Exception("No valid GUID found in 100 attempts.")
                self.guid = guid

        if self.is_private and not self.private_reason:
            self.private_reason = 'user'

        super(Link, self).save(*args, **kwargs)

        if not self.folders.count():
            if not initial_folder:
                if self.created_by and self.created_by.root_folder:
                    initial_folder = self.created_by.root_folder
            if initial_folder:
                self.folders.add(initial_folder)

    def __str__(self):
        return self.guid

    @classmethod
    def get_canonical_guid(self, guid):
        """
        Given a GUID, return the canonical version, with hyphens every 4 chars and all caps.
        So "a2b3c4d5" becomes "A2B3-C4D5".
        """
        # handle legacy 9/10/11-char GUIDs
        if '-' not in guid and len(guid) >= 9:
            # handle common typo because legacy URLs start with zero
            if guid[0] == 'O':
                guid = guid.replace('O', '0', 1)
            return guid

        # uppercase and remove non-alphanumerics
        canonical_guid = re.sub('[^0-9A-Z]+', '', guid.upper())

        # split guid into 4-char chunks, starting from the end
        guid_parts = [canonical_guid[max(i - 4, 0):i] for i in
                      range(len(canonical_guid), 0, -4)]

        # stick together parts with '-'
        return "-".join(reversed(guid_parts))

    def move_to_folder_for_user(self, folder, user):
        """
            Move this link to the given folder for the given user.
            If folder is None, link is moved to root (no folder).
        """
        # remove this link from any folders it's in for this user
        self.folders.remove(*self.folders.accessible_to(user))
        # add it back to the given folder
        if folder:
            self.folders.add(folder)
            if not folder.organization:
                self.organization = None
            else:
                self.organization = folder.organization
            self.save(update_fields=['organization'])

    def can_upload_to_internet_archive(self):
        """ Return True if this link is appropriate for upload to IA. """
        return self.is_discoverable()

    def guid_as_path(self):
        # For a GUID like ABCD-1234, return a path like AB/CD/12.
        stripped_guid = re.sub('[^0-9A-Za-z]+', '', self.guid)
        guid_parts = [stripped_guid[i:i + 2] for i in range(0, len(stripped_guid), 2)]
        return '/'.join(guid_parts[:-1])

    def warc_storage_file(self):
        return os.path.join(settings.WARC_STORAGE_DIR, self.guid_as_path(), '%s.warc.gz' % self.guid)

    # def get_thumbnail(self, image_data=None):
    #     if self.thumbnail_status == 'failed' or self.thumbnail_status == 'generating':
    #         return None
    #
    #     thumbnail_path = os.path.join(settings.THUMBNAIL_STORAGE_PATH, self.guid_as_path(), 'thumbnail.png')
    #
    #     if self.thumbnail_status == 'generated' and default_storage.exists(thumbnail_path):
    #         return default_storage.open(thumbnail_path)
    #
    #     try:
    #
    #         warc_url = None
    #         image = None
    #
    #         if image_data:
    #             image = Image(blob=image_data)
    #         else:
    #
    #             if self.screenshot_capture and self.screenshot_capture.status == 'success':
    #                 warc_url = self.screenshot_capture.url
    #             else:
    #                 pdf_capture = self.captures.filter(content_type__istartswith='application/pdf').first()
    #                 if pdf_capture:
    #                     warc_url = pdf_capture.url
    #
    #             if warc_url:
    #                 self.thumbnail_status = 'generating'
    #                 self.save(update_fields=['thumbnail_status'])
    #
    #                 headers, data = self.replay_url(warc_url)
    #                 temp_file = tempfile.NamedTemporaryFile(suffix='.' + warc_url.rsplit('.', 1)[-1])
    #                 for chunk in data:
    #                     temp_file.write(chunk)
    #                 temp_file.flush()
    #                 image = Image(filename=temp_file.name + "[0]")  # [0] limits ImageMagick to first page of PDF
    #
    #         if image:
    #             with imagemagick_temp_dir():
    #                 with image as opened_img:
    #                     opened_img.transform(resize='600')
    #                     # opened_img.resize(600,600)
    #                     with Image(width=600, height=600) as dst_image:
    #                         dst_image.composite(opened_img, 0, 0)
    #                         dst_image.compression_quality = 60
    #                         default_storage.store_data_to_file(dst_image.make_blob('png'), thumbnail_path, overwrite=True)
    #
    #             self.thumbnail_status = 'generated'
    #             self.save(update_fields=['thumbnail_status'])
    #
    #             return default_storage.open(thumbnail_path)
    #
    #     except Exception as e:
    #         print "Thumbnail generation failed for %s: %s" % (self.guid, e)
    #
    #     self.thumbnail_status = 'failed'
    #     self.save(update_fields=['thumbnail_status'])

    def delete_related(self):
        CDXLine.objects.filter(link_id=self.pk).delete()
        Capture.objects.filter(link_id=self.pk).delete()

    def is_archive_eligible(self):
        """
            True if it's older than 24 hours
        """
        return self.archive_timestamp < timezone.now()

    @cached_property
    def screenshot_capture(self):
        return self.captures.filter(role='screenshot').first()

    @cached_property
    def primary_capture(self):
        return self.captures.filter(role='primary').first()

    @cached_property
    def favicon_capture(self):
        return self.captures.filter(role='favicon').first()

    def write_uploaded_file(self, uploaded_file, cache_break=False):
        """
            Given a file uploaded by a user, create a Capture record and warc.
        """
        from api.utils import get_mime_type, mime_type_lookup  # local import to avoid circular import

        # normalize file name to upload.jpg, upload.png, upload.gif, or upload.pdf
        mime_type = get_mime_type(uploaded_file.name)
        file_name = 'upload.%s' % mime_type_lookup[mime_type]['new_extension']
        warc_url = "file:///%s/%s" % (self.guid, file_name)

        # append a random number to warc_url if we're replacing a file, to avoid browser cache
        if cache_break:
            r = random.SystemRandom()
            warc_url += "?version=%s" % (str(r.random()).replace('.', ''))

        capture = Capture(link=self,
                          role='primary',
                          status='success',
                          record_type='resource',
                          user_upload='True',
                          content_type=mime_type,
                          url=warc_url)
        with preserve_perma_warc(self.guid, self.creation_timestamp, self.warc_storage_file()) as warc:
            uploaded_file.file.seek(0)
            write_resource_record_from_asset(uploaded_file.file.read(), warc_url, mime_type, warc)
        capture.save()

    def safe_delete_warc(self):
        old_name = self.warc_storage_file()
        if default_storage.exists(old_name):
            new_name = old_name.replace('.warc.gz', '_replaced_%d.warc.gz' % timezone.now().timestamp())
            default_storage.store_file(default_storage.open(old_name), new_name)
            default_storage.delete(old_name)

    def replay_url(self, url, wsgi_application=None, follow_redirects=True):
        """
            Given a URL contained in this WARC, return a werkzeug BaseResponse for the URL as played back by pywb.
        """
        # By default, play back from our pywb wsgi app.
        if not wsgi_application:
            from warc_server.app import application as pywb_application  # local to avoid circular imports
            wsgi_application = pywb_application

        # Set up a werkzeug wsgi client.
        client = Client(wsgi_application, BaseResponse)

        # Set a cookie to allow replay of private links.
        if self.is_private:
            client.set_cookie('localhost', self.guid, self.create_access_token())

        # Return pywb's response as a BaseResponse.
        full_url = '/%s/%s' % (self.guid, url)
        return client.get(full_url, follow_redirects=follow_redirects)

    def base_playback_url(self, host=None):
        host = host or settings.PLAYBACK_HOST
        return u"%s/warc/%s/" % (("//" + host if host else ''), self.guid)

    def create_access_token(self):
        """
            Return an access token for accessing this link.
            Access token consists of the link GUID, signed by Django with the current timestamp.
        """
        return TimestampSigner().sign(self.pk)

    def validate_access_token(self, token, max_age=60):
        """
            Validate an access token for this link.
            Access token should be the link GUID, signed by Django no more than max_age seconds ago.
        """
        try:
            return TimestampSigner().unsign(token, max_age=max_age) == self.pk
        except BadSignature:
            return False

    def is_discoverable(self):
        return not self.is_private and not self.is_unlisted

    ### functions to deal with link-specific caches ###

    @classmethod
    def get_cdx_cache_key(cls, guid):
        return "cdx-"+guid

    @classmethod
    def get_warc_cache_key(cls, warc_storage_file):
        return "warc-"+re.sub(r'[^\w-]', '', warc_storage_file)

    def clear_cache(self):
        cache.delete(Link.get_cdx_cache_key(self.guid))
        cache.delete(Link.get_warc_cache_key(self.warc_storage_file()))

    def accessible_to(self, user):
        return user.can_edit(self)

    ###
    ### Methods for playback via Webrecorder
    ###

    @cached_property
    def wr_collection_slug(self):
        return self.guid.lower()

    def wr_iframe_prefix(self, wr_username):
        return "{}/{}/{}/".format(settings.PLAYBACK_HOST, wr_username, self.wr_collection_slug)

    def init_replay_for_user(self, request):
        result = get_wr_session(request, self.is_private, self.wr_collection_slug)

        wr_username, wr_session_cookie, collection_is_empty = result

        if collection_is_empty:
            try:
                self.upload_to_wr(wr_username, wr_session_cookie)
            except WebrecorderException:
                clear_wr_session(request)
                raise

        return wr_username

    def upload_to_wr(self, wr_username, wr_session_cookie):
        """
        Upload warc to a temporary Webrecorder per-user collection for playback
        (The collection is unique per user and per GUID)
        """

        warc_path = self.warc_storage_file()
        upload_data = None
        start_time = time.time()

        with default_storage.open(warc_path, 'rb') as warc_file:
            _, upload_data = query_wr_api(
                method='put',
                path='/upload?force-coll={coll}&filename={coll}.warc.gz'.format(coll=self.wr_collection_slug),
                data=warc_file,
                cookie=wr_session_cookie,
                valid_if=lambda code, data: code == 200 and data.get('upload_id')
            )

        # wait for WR to finish uploading the WARC
        while True:
            if time.time() - start_time > settings.WR_REPLAY_UPLOAD_TIMEOUT:
                raise WebrecorderException("Upload timed out; check Webrecorder logs.")

            _, upload_data = query_wr_api(
                method='get',
                path='/upload/{upload_id}?user={user}'.format(user=wr_username, upload_id=upload_data.get('upload_id')),
                cookie=wr_session_cookie,
                valid_if=lambda code, data: code == 200)

            if upload_data.get('done'):
                break

            time.sleep(0.5)


class Capture(models.Model):
    link = models.ForeignKey(Link, null=False, related_name='captures', on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=(('primary','primary'),('screenshot','screenshot'),('favicon','favicon')))
    status = models.CharField(max_length=10, choices=(('pending','pending'),('failed','failed'),('success','success')))
    url = models.CharField(max_length=2100, blank=True, null=True)
    record_type = models.CharField(max_length=10, choices=(
        ('response','WARC Response record -- recorded from web'),
        ('resource','WARC Resource record -- file without web headers')))
    content_type = models.CharField(max_length=255, null=False, default='', help_text="HTTP Content-type header.")
    user_upload = models.BooleanField(default=False, help_text="True if the user uploaded this capture.")

    def __str__(self):
        return "%s %s" % (self.role, self.status)

    def replay(self):
        """ Replay this capture through pywb. Returns a werkzeug BaseResponse object. """
        return self.link.replay_url(self.url)

    def mime_type(self):
        """
            Return normalized mime type from content_type.
            Stuff after semicolon is stripped, type is lowercased, and x- prefix is removed.
        """
        return self.content_type.split(";", 1)[0].lower().replace('/x-', '/')

    def use_sandbox(self):
        """
            Whether the iframe we use to display this capture should be sandboxed.
            Answer is yes unless we're playing back a PDF, which currently can't
            be sandboxed in Chrome.
        """
        return not self.mime_type().startswith("application/pdf")

    INLINE_TYPES = {'image/jpeg', 'image/gif', 'image/png', 'image/tiff', 'text/html', 'text/plain', 'application/pdf',
                    'application/xhtml', 'application/xhtml+xml'}

    def show_interstitial(self):
        """
            Whether we should show an interstitial view/download button instead of showing the content directly.
            True unless we recognize the mime type as something that should be shown inline (PDF/HTML/image).
        """
        return self.mime_type() not in self.INLINE_TYPES

    def url_fragment(self):
        return ("id_/" if self.record_type == 'resource' else "") + self.url

    def playback_url(self):
        if not self.url:
            return None
        return self.link.base_playback_url() + self.url_fragment()

    def playback_url_with_access_token(self):
        """
            Return a URL that will allow playback of a private link.
            If link is not private, returns regular playback URL.

            IMPORTANT: Links returned by this function should only be displayed to authorized users.
        """
        if not self.link.is_private:
            return self.playback_url()
        return mark_safe("//%s%s?%s" % (
            settings.PLAYBACK_HOST,
            reverse('user_management_set_access_token_cookie'),
            urlencode({
                'token': self.link.create_access_token(),
                'guid': self.link_id,
                'next': self.url_fragment().encode('utf-8'),
            })
        ))


class CaptureJob(models.Model):
    """
        This class tracks capture jobs for purposes of:
            (1) sorting the capture queue fairly and
            (2) reporting status during a capture.
    """
    link = models.OneToOneField(Link, related_name='capture_job', null=True, blank=True, on_delete=models.CASCADE)
    status = models.CharField(max_length=15,
                              default='invalid',
                              choices=(('pending','pending'),('in_progress','in_progress'),('completed','completed'),('deleted','deleted'),('failed','failed'),('invalid', 'invalid')),
                              db_index=True)
    message = models.TextField(null=True, blank=True) #if we move to postgres, can be a json field
    human = models.BooleanField(default=False)
    order = models.FloatField(db_index=True)
    submitted_url = models.CharField(max_length=2100, blank=True, null=False)
    created_by = models.ForeignKey(LinkUser, blank=False, null=False, related_name='capture_jobs', on_delete=models.CASCADE)
    link_batch = models.ForeignKey('LinkBatch', blank=True, null=True, related_name='capture_jobs', on_delete=models.CASCADE)

    # reporting
    attempt = models.SmallIntegerField(default=0)
    step_count = models.FloatField(default=0)
    step_description = models.CharField(max_length=255, blank=True, null=True)
    capture_start_time = models.DateTimeField(blank=True, null=True)
    capture_end_time = models.DateTimeField(blank=True, null=True)

    # settings to allow our tests to draw out race conditions
    TEST_PAUSE_TIME = 0
    TEST_ALLOW_RACE = False

    def __str__(self):
        return u"CaptureJob %s: %s" % (self.pk, self.link_id)

    def save(self, *args, **kwargs):

        # If this job does not have an order yet (just created),
        # examine all pending jobs to place this one in a fair position in the queue.
        # "Fair" means round robin: this job will be processed after every other job submitted by this user,
        # and then after every other user waiting in line has had at least one job done.
        if not self.order:

            # get all pending jobs, in reverse priority order
            pending_jobs = CaptureJob.objects.filter(status='pending', human=self.human).order_by('-order').select_related('link')
            # narrow down to just the jobs that come *after* the most recent job submitted by this user
            pending_jobs = list(itertools.takewhile(lambda x: x.created_by_id != self.created_by_id, pending_jobs))
            # flip the list of jobs back around to the order they'll be processed in
            pending_jobs = list(reversed(pending_jobs))

            # Go through pending jobs until we find two jobs submitted by the same user.
            # It's not fair for another user to run two jobs after all of ours are done,
            # so this new job should come right before that user's second job.
            next_jobs = {}
            last_job = None
            for pending_job in pending_jobs:
                pending_job_created_by_id = pending_job.link.created_by_id
                if pending_job_created_by_id in next_jobs:
                    # pending_job is the other user's second job, so this one goes in between that and last_job
                    self.order = last_job.order + (pending_job.order - last_job.order)/2
                    break
                next_jobs[pending_job_created_by_id] = pending_job
                last_job = pending_job

            # If order isn't set yet, that means we should go last. Find the highest current order and add 1.
            if not self.order:
                if pending_jobs:
                    self.order = pending_jobs[-1].order + 1
                else:
                    self.order = (CaptureJob.objects.filter(human=self.human).aggregate(Max('order'))['order__max'] or 0) + 1

        super(CaptureJob, self).save(*args, **kwargs)

    @classmethod
    def get_next_job(cls, reserve=False):
        """
            Return the next job to work on, looking first at the human queue and then at the robot queue.

            If `reserve=True`, mark the returned job with `status=in_progress` and remove from queue so the
            same job can't be returned twice. Caller must make sure the job is actually processed once returned.
        """

        # cleanup: mark any captures as deleted where link has been deleted before capture
        CaptureJob.objects.filter(link__user_deleted=True, status='pending').update(status='deleted')

        while True:
            next_job = cls.objects.filter(status='pending').order_by('-human', 'order', 'pk').first()

            if reserve and next_job:
                if cls.TEST_PAUSE_TIME:
                    time.sleep(cls.TEST_PAUSE_TIME)

                # update the returned job to be in_progress instead of pending, so it won't be returned again
                # set time using database time, so timeout comparisons will be consistent across worker servers
                update_count = CaptureJob.objects.filter(
                    status='pending',
                    pk=next_job.pk
                ).update(
                    status='in_progress',
                    capture_start_time=Now()
                )

                # if no rows were updated, another worker claimed this job already -- try again
                if not update_count and not cls.TEST_ALLOW_RACE:
                    continue

                # load up-to-date time from database
                next_job.refresh_from_db()

            return next_job

    def queue_position(self):
        """
            Search job_queues to calculate the queue position for this job -- how many pending jobs have to be processed
            before this one?

            Returns 0 if job is not pending.
        """
        if self.status != 'pending':
            return 0

        queue_position = CaptureJob.objects.filter(status='pending', order__lte=self.order, human=self.human).count()
        if not self.human:
            queue_position += CaptureJob.objects.filter(status='pending', human=True).count()

        return queue_position

    def inc_progress(self, inc, description):
        self.step_count = int(self.step_count) + inc
        self.step_description = description
        self.save(update_fields=['step_count', 'step_description'])

    def mark_completed(self, status='completed'):
        """
            Record completion time and status for this job.
        """
        self.status = status
        self.capture_end_time = timezone.now()
        self.save(update_fields=['status', 'capture_end_time', 'message'])

    def mark_failed(self, message):
        """ Mark job as failed, and record message in format for front-end display. """
        self.message = json.dumps({api_settings.NON_FIELD_ERRORS_KEY: [message]})
        self.mark_completed('failed')

    def accessible_to(self, user):
        return self.link.accessible_to(user)

class LinkBatch(models.Model):
    created_by = models.ForeignKey(LinkUser, blank=False, null=False, related_name='link_batches', on_delete=models.CASCADE)
    started_on = models.DateTimeField(auto_now=True, blank=False, null=False, db_index=True)
    target_folder = models.ForeignKey(Folder, blank=False, null=False, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "link batches"

    def accessible_to(self, user):
        return user.is_staff or self.created_by == user

    # In Python 3: def __str__(self):
    def __unicode__(self):
        return u"LinkBatch %s" % (self.pk,)


#########################
# Stats related models
#########################

class WeekStats(models.Model):
    """
    Our stats dashboard displays weekly stats. Let's house those here.
    """

    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True)


    links_sum = models.IntegerField(default=0)
    users_sum = models.IntegerField(default=0)
    organizations_sum = models.IntegerField(default=0)
    registrars_sum = models.IntegerField(default=0)


class MinuteStats(models.Model):
    """
    To see how the flag is blowing in Perma land, we log sums
    for key points activity each minute
    """

    creation_timestamp = models.DateTimeField(auto_now_add=True)

    links_sum = models.IntegerField(default=0)
    users_sum = models.IntegerField(default=0)
    organizations_sum = models.IntegerField(default=0)
    registrars_sum = models.IntegerField(default=0)


class CDXLineManager(models.Manager):
    def create_all_from_link(self, link):
        warc_path = link.warc_storage_file()
        with default_storage.open(warc_path, 'rb') as warc_file, io.BytesIO() as cdx_io:
            write_cdx_index(cdx_io, warc_file, warc_path)
            cdx_io.seek(0)
            next(cdx_io) # first line is a header so skip it
            lines = []
            for line in cdx_io:
                lines.append(CDXLine(raw=str(line, 'utf-8'), link_id=link.guid, is_unlisted=link.is_unlisted, is_private=link.is_private))
            # Delete any existing rows to reduce the likelihood of a race condition,
            # if someone hits the link before the capture process has written the CDXLine db.
            CDXLine.objects.filter(link_id=link.guid).delete()
            results = CDXLine.objects.bulk_create(lines, batch_size=999)
        return results


class CDXLine(models.Model):
    link_id = models.CharField(null=True, max_length=255, db_index=True)
    urlkey = models.CharField(max_length=2100, null=False, blank=False)
    raw = models.TextField(null=False, blank=False)
    is_unlisted = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)

    objects = CDXLineManager()

    def __init__(self, *args, **kwargs):
        super(CDXLine, self).__init__(*args, **kwargs)
        if self.raw:
            self.__set_defaults()

    @cached_property
    def parsed(self):
        return CDXObject(bytes(self.raw, 'utf-8'))

    def __set_defaults(self):
        if not self.urlkey:
            self.urlkey = self.parsed['urlkey']

    @cached_property
    def timestamp(self):
        return self.parsed['timestamp']

    def is_revisit(self):
        return self.parsed.is_revisit()


class UncaughtError(models.Model):
    current_url = models.TextField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    stack = models.TextField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    user = models.ForeignKey(LinkUser, null=True, blank=True, related_name="errors_triggered", on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    resolved = models.BooleanField(default=False)
    resolved_by_user = models.ForeignKey(LinkUser, null=True, blank=True, related_name="errors_resolved", on_delete=models.CASCADE)

    # In Python 3: def __str__(self):
    def __unicode__(self):
        return "%s: %s" % (self.id, self.message)

    def format_for_reading(self):
        formatted = {
            'id': self.id,
            'user_agent': self.user_agent,
            'created_at': self.created_at,
            'message': self.message,
            'current_url': self.current_url,
        }

        if self.stack:
            try:
                formatted['stack'] = json.loads(self.stack)[0]
            except IndexError:
                logger.warn("No stacktrace for js error {}".format(self.id))
            except ValueError:
                logger.warn("Stacktrace for js error {} is invalid json".format(self.id))
        if self.user:
            formatted['user'] = self.user.id

        return formatted
