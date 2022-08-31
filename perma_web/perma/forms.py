from axes.utils import reset as reset_login_attempts

from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.forms import ModelForm
from django.utils.html import mark_safe

from perma.models import Registrar, Organization, LinkUser, Sponsorship

import logging
logger = logging.getLogger(__name__)

### HELPERS ###

class OrganizationField(forms.ModelMultipleChoiceField):
    def __init__(self,
                 queryset=Organization.objects.order_by('name'),
                 label="Organization",
                 **kwargs
                 ):
        super(OrganizationField, self).__init__(queryset, label=label, **kwargs)

class SelectMultipleWithSingleWidget(forms.SelectMultiple):
    """
        Form widget that shows a single dropdown, but works with many-to-many fields.
        Thank you, http://stackoverflow.com/a/14971139
    """
    def render(self, *args, **kwargs):
        html = super(SelectMultipleWithSingleWidget, self).render(*args, **kwargs)
        return mark_safe(html.replace(' multiple="multiple"', '', 1))

class OrgMembershipWidget(SelectMultipleWithSingleWidget):
    """
        This is a select widget for organizations that disables organizations where the target user is already a
        member. Requires `instance=some_user` to be passed to the form.
    """
    def render_option(self, selected_choices, option_value, option_label):
        if not hasattr(self, 'current_orgs'):
            target_user = self.form_instance.instance
            self.current_orgs = [o.pk for o in target_user.organizations.all()] if target_user and target_user.id else []
        if option_value in self.current_orgs:
            option_label += " - already a member"
        html = super(OrgMembershipWidget, self).render_option(selected_choices, option_value, option_label)
        if option_value in self.current_orgs:
            html = html.replace('>', ' disabled="disabled">', 1)
        return html

### REGISTRAR FORMS ###

class RegistrarForm(ModelForm):
    class Meta:
        model = Registrar
        fields = ['name', 'email', 'website', 'orgs_private_by_default']
        labels = {
            'orgs_private_by_default': 'New organizations should have their links set to "Private" by default.'
        }
        help_texts={
            'orgs_private_by_default': 'Note: privacy settings can be overridden for individual organizations and links.'
        }


class LibraryRegistrarForm(ModelForm):
    class Meta:
        model = Registrar
        fields = ['name', 'email', 'website', 'address']  #, 'logo', 'show_partner_status']

    def __init__(self, *args, **kwargs):
        super(LibraryRegistrarForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "Library name"
        self.fields['email'].label = "Library email"
        self.fields['website'].label = "Library website"
        self.fields['address'].label = "Library physical address"
        # self.fields['logo'].label = "Library/University logo"
        # # If you change here, please also change in clean_logo below
        # self.fields['logo'].widget.attrs['accept'] = ".png,.jpg,.jpeg,.gif"
        # self.fields['show_partner_status'].label = "Display us in the list of Perma.cc partners"
        # self.fields['show_partner_status'].initial = True

    # def clean(self):
    #     logo = self.cleaned_data['logo']
    #     if not logo or imghdr.what(logo) not in ['png', 'jpg', 'gif']:
    #         if self.cleaned_data.get('show_partner', None):
    #           msg = "Please include a logo (.png, .jpg, .gif)."
    #           self.add_error('logo', msg)
    #     return logo

### ORGANIZATION FORMS ###

class OrganizationWithRegistrarForm(ModelForm):

    registrar = forms.ModelChoiceField(queryset=Registrar.objects.approved().order_by('name'), empty_label=None)

    class Meta:
        model = Organization
        fields = ['name', 'registrar']


class OrganizationForm(ModelForm):

    class Meta:
        model = Organization
        fields = ['name']

### USER CREATION FORMS ###

class SetPasswordForm(SetPasswordForm):
    def save(self, commit=True):
        """
        When allowing user to set their password via an email link, we may be in a new-user flow with
        email_confirmed=False, or a forgot-password flow with email_confirmed=True.
        """
        if not self.user.is_confirmed:
            self.user.is_active = True
            self.user.is_confirmed = True
        user = super().save(commit)
        reset_login_attempts(username=user.email)
        return user


class UserForm(forms.ModelForm):
    """
    User add/edit form.
    """
    telephone = forms.CharField(label="Do not fill out this box", required=False)  # field to fool bots

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "telephone"]

    def add_prefix(self, field_name):
        # rename the email field in the HTML to foil bots that are spamming us
        field_name = "e-address" if field_name == "email" else field_name
        return super().add_prefix(field_name)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        # From Sept 2022 onwards: all email addresses are lowercase
        if self.instance.email:
            self.instance.email = self.instance.email.lower()

        # save user, and set a password so that the password_reset flow can be
        # used for email confirmation
        self.instance.set_password(LinkUser.objects.make_random_password(length=20))
        user = forms.ModelForm.save(self, commit)
        return user

class UserFormWithAdmin(UserForm):
    """
        User form that causes the created user to be an admin.
    """
    def save(self, commit=True):
        self.instance.is_staff = True
        return super(UserFormWithAdmin, self).save(commit)

class UserFormWithRegistrar(UserForm):
    """
    add registrar to the create user form
    """
    registrar = forms.ModelChoiceField(queryset=Registrar.objects.approved().order_by('name'), empty_label=None)

    def __init__(self, data=None, current_user=None, **kwargs):
        super(UserFormWithRegistrar, self).__init__(data, **kwargs)

        # filter available registrars based on current user
        query = self.fields['registrar'].queryset
        if current_user.is_registrar_user():
            query = query.filter(pk=current_user.registrar_id)
        self.fields['registrar'].queryset = query

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "registrar"]

class UserFormWithSponsoringRegistrar(UserForm):
    """
    add sponsoring registrar to the create user form
    """
    sponsoring_registrars = forms.ModelChoiceField(label='Sponsoring Registrar', queryset=Registrar.objects.approved().order_by('name'))

    def __init__(self, data=None, current_user=None, **kwargs):
        self.current_user = current_user
        super(UserFormWithSponsoringRegistrar, self).__init__(data, **kwargs)

        query = self.fields['sponsoring_registrars'].queryset
        if self.instance and self.instance.pk:
            query = query.exclude(pk__in=self.instance.sponsoring_registrars.all())
        if current_user and current_user.is_registrar_user():
            query = query.filter(pk=current_user.registrar_id)
            self.initial['sponsoring_registrars'] = str(query.first().id)

        self.fields['sponsoring_registrars'].queryset = query

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "sponsoring_registrars"]

    def clean(self):
        super().clean()
        if self.instance.pk and self.cleaned_data.get('sponsoring_registrars') and self.cleaned_data['sponsoring_registrars'].id in self.instance.sponsoring_registrars.values_list('id', flat=True):
            raise forms.ValidationError(
                '%(user)s is already sponsored by %(registrar)s',
                code='non-unique-sponsorship',
                params={'user': self.instance.email, 'registrar': self.cleaned_data['sponsoring_registrars'].name},
            )

    def save(self, commit=True):
        """ Override save so we add the new sponsor rather than replacing all existing sponsorships for this user. """
        # Adapted from https://stackoverflow.com/a/2264722
        instance = forms.ModelForm.save(self, False)
        def save_m2m():
            Sponsorship.objects.create(registrar=self.cleaned_data['sponsoring_registrars'], user=instance, created_by=self.current_user)
        self.save_m2m = save_m2m
        if commit:
            instance.save()
            self.save_m2m()

        return instance


class CreateUserFormWithCourt(UserForm):
    """
    add court to the create user form
    """

    requested_account_note = forms.CharField(required=True)

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "requested_account_note"]

    def __init__(self, *args, **kwargs):
        super(CreateUserFormWithCourt, self).__init__(*args, **kwargs)
        self.fields['requested_account_note'].label = "Your court"
        self.fields['first_name'].label = "Your first name"
        self.fields['last_name'].label = "Your last name"
        self.fields['email'].label = "Your email"

class CreateUserFormWithFirm(UserForm):
    """
    add firm to the create user form
    """

    requested_account_note = forms.CharField(required=True)

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "requested_account_note"]

    def __init__(self, *args, **kwargs):
        super(CreateUserFormWithFirm, self).__init__(*args, **kwargs)
        self.fields['requested_account_note'].label = "Your firm"
        self.fields['first_name'].label = "Your first name"
        self.fields['last_name'].label = "Your last name"
        self.fields['email'].label = "Your email"


class CreateUserFormWithUniversity(UserForm):
    """
    add university to the create user form
    """

    requested_account_note = forms.CharField(required=True)

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "requested_account_note"]

    def __init__(self, *args, **kwargs):
        super(CreateUserFormWithUniversity, self).__init__(*args, **kwargs)
        self.fields['requested_account_note'].label = "Your university"


class UserFormWithOrganization(UserForm):
    """
    add organization to the create user form
    """
    organizations = OrganizationField(widget=SelectMultipleWithSingleWidget)

    def __init__(self, data=None, current_user=None, **kwargs):
        super(UserFormWithOrganization, self).__init__(data, **kwargs)

        # filter available organizations based on current user
        query = self.fields['organizations'].queryset
        if current_user.is_registrar_user():
            query = query.filter(registrar_id=current_user.registrar_id)
        elif current_user.is_organization_user:
            query = query.filter(users=current_user.pk)
        self.fields['organizations'].queryset = query

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "organizations"]


### USER EDIT FORMS ###

class UserAddRegistrarForm(UserFormWithRegistrar):
    """
    User form that just lets you change the registrar.
    """

    class Meta:
        model = LinkUser
        fields = ("registrar",)

    def save(self, commit=True):
        """ Override save to remove any organizations before upgrading to registrar. """
        self.instance.organizations.clear()
        return super(UserAddRegistrarForm, self).save(commit)


class UserAddSponsoringRegistrarForm(UserFormWithSponsoringRegistrar):
    """
    User form that just lets you change the sponsoring registrars.
    """

    class Meta:
        model = LinkUser
        fields = ("sponsoring_registrars",)


class UserAddOrganizationForm(UserFormWithOrganization):
    """
        User form that just lets you add an organization.
        This is based on CreateUserFormWithOrganization, but only shows the org field, and uses a widget that
        disables organizations where the user is already a member.
    """
    email = None  # hide inherited email field
    organizations = OrganizationField(widget=OrgMembershipWidget)

    def __init__(self, *args, **kwargs):
        """ Let orgs widget access target user so we can disable orgs they already belong to. """
        super(UserAddOrganizationForm, self).__init__(*args, **kwargs)
        self.fields['organizations'].widget.form_instance = self

    class Meta(UserFormWithOrganization.Meta):
        fields = ("organizations",)

    def save(self, commit=True):
        """ Override save so we *add* the new organization rather than replacing all existing orgs for this user. """
        self.instance.organizations.add(self.cleaned_data['organizations'][0])
        return self.instance

class UserAddAdminForm(forms.ModelForm):
    """
        Form that just upgrades user to staff on submit.
    """
    class Meta:
        model = LinkUser
        fields = []

    def save(self, commit=True):
        self.instance.is_staff = True
        self.instance.registrar = None
        self.instance.organizations.clear()
        if commit:
            self.instance.save()
        return self.instance


### CONTACT FORMS ###

class ContactForm(forms.Form):
    """
    The form we use on the contact page. Just an email (optional)
    and a message
    """

    def clean_subject(self):
        return self.cleaned_data['subject'] or "New message from Perma contact form"

    email = forms.EmailField(label="Your email address")
    registrar = forms.ChoiceField(choices = (), label = 'Your library')
    subject = forms.CharField(widget=forms.HiddenInput, required=False)
    telephone = forms.CharField(label="Do not fill out this box", required=False, widget=forms.Textarea)  # fake message box to fool bots
    box2 = forms.CharField(label="Message", widget=forms.Textarea)
    referer = forms.URLField(widget=forms.HiddenInput, required=False)
