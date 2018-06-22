import logging

from django import forms
from django.forms import ModelForm
from django.utils.html import mark_safe

from perma.models import Registrar, Organization, LinkUser

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
    class Meta(object):
        model = Registrar
        fields = ['name', 'email', 'website']


class LibraryRegistrarForm(ModelForm):
    class Meta(object):
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

    class Meta(object):
        model = Organization
        fields = ['name', 'registrar']


class OrganizationForm(ModelForm):

    class Meta(object):
        model = Organization
        fields = ['name']

### USER CREATION FORMS ###

class UserForm(forms.ModelForm):
    """
    User add/edit form.
    """
    class Meta(object):
        model = LinkUser
        fields = ["first_name", "last_name", "email"]

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

    class Meta(object):
        model = LinkUser
        fields = ["first_name", "last_name", "email", "registrar"]


class CreateUserFormWithCourt(UserForm):
    """
    add court to the create user form
    """

    requested_account_note = forms.CharField(required=True)

    class Meta(object):
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

    class Meta(object):
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

    class Meta(object):
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

    class Meta(object):
        model = LinkUser
        fields = ["first_name", "last_name", "email", "organizations"]


### USER EDIT FORMS ###

class UserAddRegistrarForm(UserFormWithRegistrar):
    """
    User form that just lets you change the registrar.
    """

    class Meta(object):
        model = LinkUser
        fields = ("registrar",)

    def save(self, commit=True):
        """ Override save to remove any organizations before upgrading to registrar. """
        self.instance.organizations.clear()
        return super(UserAddRegistrarForm, self).save(commit)


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
    class Meta(object):
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
    message = forms.CharField(widget=forms.Textarea)
    referer = forms.URLField(widget=forms.HiddenInput, required=False)
