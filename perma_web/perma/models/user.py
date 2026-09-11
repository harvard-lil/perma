import hashlib
import hmac
import json
import re
import uuid

import django.contrib.auth.models
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.db import models, transaction
from django.db.models import Case, Q, When
from django.utils import timezone
from django.utils.functional import cached_property
import simple_history

from .customer import CustomerModel
from .folder import Folder
from .organization import Organization
from .registrar import Registrar, Sponsorship


class LinkUserManager(BaseUserManager):
    def create_user(self, email, registrar, organization, date_joined, first_name, last_name, authorized_by, password=None):
        """
        Creates and saves a User with the given email, registrar and password.
        """

        if not email:
            raise ValueError('Users must have an email address')
        if registrar and organization:
            raise ValueError('Users may not have both registrar and organization affiliations.')

        user = self.model(
            email=self.normalize_email(email),
            registrar=registrar,
            date_joined = date_joined,
            first_name = first_name,
            last_name = last_name,
            authorized_by = authorized_by,
        )

        user.set_password(password)
        user.save()

        if organization:
            user.organizations.add(organization)

        return user


# This is a temporary workaround for the problem described in
# https://github.com/jazzband/django-model-utils/issues/331#issuecomment-478994563
# where django-model-utils FieldTracker breaks the setter for overridden attributes on abstract base classes
del AbstractBaseUser.is_active

class LinkUser(CustomerModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        db_index=True,
        error_messages={'unique': "A user with that email address already exists.",}
    )
    raw_email = models.CharField(
        verbose_name='raw email address',
        max_length=255,
        null=True
    )
    registrar = models.ForeignKey(Registrar, blank=True, null=True, related_name='users', help_text="If set, this user is a registrar user. This should not be set if org is set!", on_delete=models.CASCADE)
    pending_registrar = models.ForeignKey(Registrar, blank=True, null=True, related_name='pending_users', on_delete=models.CASCADE)
    organizations = models.ManyToManyField(Organization, through='UserOrganizationAffiliation', blank=True, related_name='users',
                                           help_text="If set, this user is an org user. This should not be set if registrar is set!<br><br>"
                                                     "Note: <b>This list will include deleted orgs of which this user is a member.</b> This is a historical"
                                                     " record and deleted org memberships cannot be removed.<br><br>"
                                           )
    sponsoring_registrars = models.ManyToManyField(
        Registrar,
        blank=True,
        related_name='sponsored_users',
        through=Sponsorship,
        through_fields=('user', 'registrar'),
        help_text="If set, this user is sponsored by a registrar. Any user can be sponsored by any registrar."
    )
    is_active = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=45, blank=True)
    last_name = models.CharField(max_length=45, blank=True)
    root_folder = models.OneToOneField('Folder', blank=True, null=True, on_delete=models.CASCADE)
    sponsored_root_folder = models.OneToOneField('Folder', blank=True, null=True, on_delete=models.CASCADE, related_name='sponsored_user')
    requested_account_type = models.CharField(max_length=45, blank=True, null=True)
    requested_account_note = models.CharField(max_length=45, blank=True, null=True)
    link_count = models.IntegerField(default=0) # A cache of the number of links created by this user
    notes = models.TextField(blank=True)

    objects = LinkUserManager()
    # Don't add an unconfigured FieldTracker() to LinkUser: it breaks last_login https://github.com/harvard-lil/perma/issues/3296
    # If tracking is required, enumerate the necessary fields using the fields param https://django-model-utils.readthedocs.io/en/latest/utilities.html#tracking-specific-fields
    # tracker = FieldTracker(fields=[])

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'

        constraints = [
            # We would like to add a case-insensitive uniqueness constraint on `email`
            # like the below, but expressions aren't supported in this version of Django.
            # We are adding the constraint via a SQL migration instead. See 0019_auto_20230424_2134.py
            # We additionally note that in this version of Django, constraints aren't
            # checked during model validation. We are not adding a special case-insensitive
            # validation check, because we downcase email in `clean`: checked against a
            # known-to-be-downcased column, the check from unique=True is sufficient.
            # models.UniqueConstraint(Lower('email'), name='unique_lower_email')
        ]

    def format_email_fields(self):
        self.raw_email = self.email
        self.email = self.email.lower()

    def clean(self, *args, **kwargs):
        self.format_email_fields()
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.pk and not self.raw_email:
            # If objects aren't being created via a model form where `clean` has been called,
            # make sure email is still formatted correctly.
            self.format_email_fields()

        with transaction.atomic():
            super().save(*args, **kwargs)

            # make sure root folder is created for each user.
            if not self.root_folder_id:
                root_folder = Folder.objects.create(
                    name='Personal Links',
                    created_by=self,
                    is_root_folder=True
                )
                self.root_folder = root_folder
                # Save with super again, instead of plain save,
                # so we don't run through our custom logic twice
                super().save()

    def get_full_name(self):
        """ Use either First Last or first half of email address as user's name. """
        return f"{self.first_name} {self.last_name}" if self.first_name or self.last_name else self.email.split('@')[0]

    def get_short_name(self):
        """ Use either First or Last or first half of email address as user's short name. """
        return self.first_name or self.last_name or self.email.split('@')[0]

    def __str__(self):
        return self.email

    def top_level_folders(self):
        """
            Get top level folders for this user, including personal folder, sponsored folder, and shared folders.
            Returns a queryset of Folders, with personal/sponsored folders first, followed by org folders sorted by name.
        """
        # personal folder first, custom_order = 0
        folder_ids = [self.root_folder_id]
        ordering_cases = [When(id=self.root_folder_id, then=0)]

        # sponsored folder second, custom_order = 1
        if self.sponsored_root_folder_id:
            folder_ids.append(self.sponsored_root_folder_id)
            ordering_cases.append(When(id=self.root_folder_id, then=1))

        # then org folders if any, custom_order = 2
        return Folder.objects.filter(
            Q(id__in=folder_ids) |
            Q(id__in=self.get_orgs().values('shared_folder_id'))
        ).annotate(
            custom_order=Case(*ordering_cases, default=2)
        ).order_by('custom_order', 'name')

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

    def create_sponsored_folder(self, registrar):
        with transaction.atomic():
            if not self.sponsored_root_folder_id:
                sponsored_root_folder = Folder.objects.create(
                    name='Sponsored Links',
                    created_by=self,
                    is_sponsored_root_folder=True
                )
                self.sponsored_root_folder = sponsored_root_folder
                self.save()
        Folder.objects.create(
            name=registrar.name,
            created_by=self,
            parent_id=self.sponsored_root_folder_id,
            sponsored_by=registrar
        )

    def as_json(self):
        from api.serializers import LinkUserSerializer  # local import to avoid circular import
        return json.dumps(LinkUserSerializer(self).data)

    def get_api_key(self):
        key = None
        try:
            key = self.api_key.key
        except LinkUser.api_key.RelatedObjectDoesNotExist:
            pass
        return key

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
               the same registrar, sponsored users, and all members of the registrar's orgs.
            Admins share scope with all users.
        """
        if self.is_organization_user:
            return other_user.organizations.filter(
                pk__in=self.organizations.values('pk')
            ).exists()
        elif self.is_registrar_user():
            if self.registrar_id == other_user.registrar_id:
                return True
            if other_user.sponsoring_registrars.filter(pk=self.registrar_id).exists():
                return True
            return other_user.organizations.filter(
                registrar_id=self.registrar_id
            ).exists()
        elif self.is_staff:
            return True
        return False

    def is_individual(self):
        """ Is the user a regular, individual user? """
        return bool(not self.is_staff and not self.is_registrar_user() and not self.is_sponsored_user() and not self.is_organization_user)

    def is_registrar_user(self):
        """ Is the user a member of a registrar? """
        return bool(self.registrar_id)

    def is_sponsored_user(self):
        """ Is the user sponsored by a registrar? """
        return self.sponsorships.exists()

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
               (self.is_organization_user or self.is_sponsored_user())

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
        return not link.user_deleted and not link.is_permanent() and self.can_edit(link)

    def can_toggle_private(self, link):
        if not self.can_edit(link):
            return False
        if link.is_private and not self.is_staff and link.private_reason not in ['user', 'old_policy']:
            return False
        return True

    def can_edit_registrar(self, registrar):
        return self.is_staff or self.registrar == registrar

    def can_edit_organization(self, organization):
        if self.is_staff:
            return True
        elif self.registrar_id:
            return self.registrar_id == organization.registrar_id
        else:
            return self.organizations.filter(pk=organization.pk).exists()


    ### subscriptions ###

    def links_remaining_in_period(self, period, limit, unlimited=None):
        from .link import Link
        today = timezone.now()

        # default to the value of self.unlimited; allow callers to explicitly override
        if unlimited is None:
            unlimited = self.unlimited

        # exclude bonus links, sponsored links and links associated with an org
        personal_links = Link.objects.filter(organization_id=None, folders__sponsored_by=None).exclude(bonus_link=True)

        if unlimited:
            # UNLIMITED (paid or sponsored)
            link_count = float("-inf")
        elif period == 'once':
            # TRIAL: all non-org links ever
            if self.cached_subscription_started:
                link_count = personal_links.filter(creation_timestamp__range=(self.cached_subscription_started, today), created_by_id=self.id).count()
            else:
                link_count = personal_links.filter(created_by_id=self.id, organization_id=None).count()
        elif period == 'monthly':
            # MONTHLY RECURRING
            if self.cached_paid_through:
                # if you have a paid subscription, calculate via its expiry date
                link_count = personal_links.filter(creation_timestamp__range=(self.cached_paid_through - relativedelta(months=1), today), created_by_id=self.id, organization_id=None).count()
            else:
                # else, check the links created this calendar month
                link_count = personal_links.filter(creation_timestamp__year=today.year, creation_timestamp__month__gte=today.month, created_by_id=self.id, organization_id=None).count()
        elif period == 'annually':
            # ANNUAL RECURRING
            if self.cached_paid_through:
                # if you have a paid subscription, calculate via its expiry date
                link_count = personal_links.filter(creation_timestamp__range=(self.cached_paid_through - relativedelta(years=1), today), created_by_id=self.id, organization_id=None).count()
            else:
                # else, check the last 365 days
                link_count = personal_links.filter(creation_timestamp__range=(today - relativedelta(years=1), today), created_by_id=self.id, organization_id=None).count()
        else:
            raise NotImplementedError("User's link_limit_period not yet handled.")
        return max(limit - link_count, 0)

    def get_links_remaining(self):
        """
            Calculate how many personal links remain.
            Returns a tuple: (links, applicable period, bonus links)
        """
        # Special handling for non-trial users who lack active paid subscriptions:
        # apply the same rules that are applied to new users
        if not self.in_trial and not self.nonpaying and self.subscription_status != 'active':
            return (self.links_remaining_in_period(settings.DEFAULT_CREATE_LIMIT_PERIOD, settings.DEFAULT_CREATE_LIMIT, unlimited=False), settings.DEFAULT_CREATE_LIMIT_PERIOD, self.bonus_links or 0)
        return (self.links_remaining_in_period(self.link_limit_period, self.link_limit), self.link_limit_period, self.bonus_links or 0)

    def link_creation_allowed(self):
        if self.frozen:
            return False
        links_remaining, _, bonus_links = self.get_links_remaining()
        return links_remaining > 0 or bonus_links > 0

    def can_view_usage_plan(self):
        """
            Should the user be able to see the usage plan page?
            Special non-paying users should not see the option to make personal purchases.
            Only authorized users should be able to see a paying registrar's subscription options.
        """
        return not self.nonpaying or (self.is_registrar_user() and not self.registrar.nonpaying)

    def can_purchase_bonus_links(self):
        return not self.nonpaying and not self.unlimited

    ### merging accounts ###

    def copy_memberships_from_users(self, users):
        original_orgs = set(self.organizations.all())

        orgs = set()
        registrars = set()
        if self.registrar_id:
            registrars.add(self.registrar_id)
        else:
            orgs.update(original_orgs)
        for user in users:
            if user.registrar_id:
                registrars.add(user.registrar_id)
            else:
                orgs.update(user.organizations.all())

        if orgs or registrars:
            assert not (orgs and registrars), f"This set of users includes both org and registrar users: {self.id}, {', '.join([str(user.id) for user in users])}."
            if registrars:
                assert len(registrars) == 1, f"This set of users includes registrar users from multiple registrars: {self.id}, {', '.join([str(user.id) for user in users])}."
                new_registrar_id = registrars.pop()
                if not self.registrar_id:
                    self.registrar_id = new_registrar_id
                    self.prepend_to_notes(f"Added registrar during the merging of accounts: {new_registrar_id}")
                    self.save(update_fields=['registrar_id', 'notes'])
            else:
                if original_orgs != orgs:
                    self.prepend_to_notes(f"Added organizations during the merging of accounts: {', '.join([str(o.id) for o in orgs - original_orgs])}")
                    self.save(update_fields=['notes'])
                    self.organizations.add(*orgs)

    def soft_delete_after_merge_with_user(self, user):
        original_email = self.email

        self.email = f"merged_users_{self.id}_and_{user.id}@perma.cc"
        self.is_active = False
        self.link_count = 0

        self.prepend_to_notes(f"Original email: { original_email }")
        if self.registrar_id:
            self.prepend_to_notes(f"Original registrar: { self.registrar_id }")
            self.registrar_id = None
        orgs = list(self.organizations.all())
        if orgs:
            self.prepend_to_notes(f"Original orgs: {', '.join([str(o.id) for o in orgs])}")
            self.organizations.remove(*orgs)

        self.save(update_fields=['email', 'is_active', 'link_count', 'notes', 'registrar_id'])
        return (original_email, self.email)

    def prepend_to_notes(self, message):
        if self.notes:
            self.notes = f"{message}\n\n{self.notes}"
        else:
            self.notes = message

    def remove_line_from_notes(self, containing):
        if self.notes:
            self.notes = re.sub(f"\n*{containing}.*", '', self.notes)


class UserOrganizationAffiliation(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(LinkUser, on_delete=models.CASCADE, db_column='linkuser_id')
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'perma_linkuser_organizations'
        constraints = [
            models.UniqueConstraint(fields=['organization', 'user'], name='unique_affiliation'),
        ]
        indexes = [
            models.Index(fields=['expires_at'])
        ]


class ApiKey(models.Model):
    """
        Based on tastypie.models: https://github.com/django-tastypie/django-tastypie/blob/master/tastypie/models.py#L35
    """
    user = models.OneToOneField(LinkUser, related_name='api_key', on_delete=models.CASCADE)
    key = models.CharField(max_length=128, blank=True, default='', db_index=True)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.key} for {self.user}"

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
