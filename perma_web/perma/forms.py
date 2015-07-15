import logging

from django import forms
from django.forms import ModelForm
from django.forms.widgets import flatatt
from django.utils.html import mark_safe

from perma.models import Registrar, Organization, LinkUser

logger = logging.getLogger(__name__)

class RegistrarForm(ModelForm):
    class Meta:
        model = Registrar
        fields = ['name', 'email', 'website']
        
        
class OrganizationWithRegistrarForm(ModelForm):

    registrar = forms.ModelChoiceField(queryset=Registrar.objects.all().order_by('name'), empty_label=None)
    
    class Meta:
        model = Organization
        fields = ['name', 'registrar']

        
class OrganizationForm(ModelForm):
    
    class Meta:
        model = Organization
        fields = ['name']
        
        
class CreateUserForm(forms.ModelForm):

    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm
    """

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email"]


    error_messages = {
        'duplicate_email': "A user with that email address already exists.",
    }

    email = forms.EmailField()

    def clean_email(self):
        # Since User.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM.

        email = self.cleaned_data["email"]
        try:
            LinkUser.objects.get(email=email)
        except LinkUser.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

        
class CreateUserFormWithRegistrar(CreateUserForm):
    """
    add registrar to the create user form
    """

    registrar = forms.ModelChoiceField(queryset=Registrar.objects.all().order_by('name'), empty_label=None)

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "registrar"]

    def clean_registrar(self):
        registrar = self.cleaned_data["registrar"]
        return registrar


class CustomSelectSingleAsList(forms.SelectMultiple):
    # Thank you, http://stackoverflow.com/a/14971139
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<select %s>' % flatatt(final_attrs)] # NOTE removed the multiple attribute
        options = self.render_options(choices, value)
        if options:
            output.append(options)
        output.append('</select>')
        return mark_safe(u'\n'.join(output))


class CreateUserFormWithOrganization(CreateUserForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm
    """
    def __init__(self, *args, **kwargs):
        registrar_id = False
        org_member_id = False

        if 'registrar_id' in kwargs:
            registrar_id = kwargs.pop('registrar_id')

        if 'org_member_id' in kwargs:
            org_member_id = kwargs.pop('org_member_id')

        super(CreateUserFormWithOrganization, self).__init__(*args, **kwargs)

        if registrar_id:
            self.fields['organization'].queryset = Organization.objects.filter(registrar_id=registrar_id).order_by('name')
        elif org_member_id:
            user = LinkUser.objects.get(id=org_member_id)
            self.fields['organization'].queryset = user.organizations.all()
        else:
            self.fields['organization'].queryset = Organization.objects.all().order_by('name')

    
    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "organization"]

    org = forms.ModelMultipleChoiceField(queryset=Organization.objects.all().order_by('name'),label="Organization", widget=CustomSelectSingleAsList)


    def clean_organization(self):
        org = self.cleaned_data["organization"]
        return org


class UserFormEdit(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is the edit form, so we strip it down even more
    """
    error_messages = {

    }

    email = forms.EmailField()

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email"]
        

class RegistrarMemberFormEdit(UserFormEdit):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is the edit form, so we strip it down even more
    """

    registrar = forms.ModelChoiceField(queryset=Registrar.objects.all().order_by('name'), empty_label=None)

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "registrar"]
    

class OrganizationMemberWithOrganizationFormEdit(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is stripped down even further to match out editing needs
    """
    
    def __init__(self, *args, **kwargs):
        registrar_id = False
        if 'registrar_id' in kwargs:
            registrar_id = kwargs.pop('registrar_id')
        super(OrganizationMemberWithOrganizationFormEdit, self).__init__(*args, **kwargs)
        if registrar_id:
            self.fields['organization'].queryset = Organization.objects.filter(registrar_id=registrar_id).order_by('name')

    class Meta:
        model = LinkUser
        fields = ["organization"]

    org = forms.ModelMultipleChoiceField(queryset=Organization.objects.all().order_by('name'),label="Organization", required=False,)
    

class OrganizationMemberWithOrganizationOrgAsOrganizationMemberFormEdit(forms.ModelForm):
    """
    TODO: this form has a gross name. rename it.
    """
    
    def __init__(self, *args, **kwargs):
        user_id = False
        if 'organization_user_id' in kwargs:
            organization_user_id = kwargs.pop('organization_user_id')
        super(OrganizationMemberWithOrganizationOrgAsOrganizationMemberFormEdit, self).__init__(*args, **kwargs)
        if organization_user_id:
            editing_user = LinkUser.objects.get(pk=organization_user_id)
            self.fields['organization'].queryset = editing_user.organizations.all().order_by('name')

    class Meta:
        model = LinkUser
        fields = ["organization"]

    org = forms.ModelMultipleChoiceField(queryset=Organization.objects.all().order_by('name'),label="Organization", required=False,)

        
class OrganizationMemberWithGroupFormEdit(UserFormEdit):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is stripped down even further to match out editing needs
    """
                         
    def __init__(self, *args, **kwargs):
        registrar_id = False
        if 'registrar_id' in kwargs:
            registrar_id = kwargs.pop('registrar_id')
        super(OrganizationMemberWithGroupFormEdit, self).__init__(*args, **kwargs)
        if registrar_id:
            self.fields['organization'].queryset = Organization.objects.filter(registrar_id=registrar_id).order_by('name')
        
    class Meta:
        model = LinkUser
        fields = ("first_name", "last_name", "email", "organization",)

    org = forms.ModelChoiceField(queryset=Organization.objects.all().order_by('name'), empty_label=None, label="Organization", required=False,)

        
class UserAddRegistrarForm(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is stripped down even further to match out editing needs
    """

    class Meta:
        model = LinkUser
        fields = ("registrar",)         

    registrar = forms.ModelChoiceField(queryset=Registrar.objects.all().order_by('name'), empty_label=None)
        
        
class UserAddOrganizationForm(forms.ModelForm):
    """
    add an org when a regular user is promoted to an org user
    """

    def __init__(self, *args, **kwargs):
        registrar_id = False
        org_member_id = False
        target_user_id = False

        if 'registrar_id' in kwargs:
            registrar_id = kwargs.pop('registrar_id')

        if 'org_member_id' in kwargs:
            org_member_id = kwargs.pop('org_member_id')

        if 'target_user_id' in kwargs:
            target_user_id = kwargs.pop('target_user_id')

        super(UserAddOrganizationForm, self).__init__(*args, **kwargs)

        target_user = LinkUser.objects.get(pk=target_user_id)

        # Registrars can only edit their own organization members
        if registrar_id:
            # Get the orgs the logged in user admins. Exclude the ones
            # the target user is already in
            orgs = Organization.objects.filter(registrar_id=registrar_id).exclude(pk__in=target_user.organizations.all())
        elif org_member_id:
            # Get the orgs the logged in user admins. Exclude the ones
            # the target user is already in
            org_member = LinkUser.objects.get(pk=org_member_id)
            orgs = org_member.organizations.all().exclude(pk__in=target_user.organizations.all())

        else:
            # Must be registry member.
            orgs = Organization.objects.all().exclude(pk__in=target_user.organizations.all())

        self.fields['organization'] = forms.ModelMultipleChoiceField(queryset=orgs.order_by('name'), label="Organization", widget=CustomSelectSingleAsList)


    class Meta:
        model = LinkUser
        fields = ("organization",)         

    
    
    def save(self, commit=True):
        user = super(UserAddOrganizationForm, self).save(commit=False)

        if commit:
            user.save()

        return user


class UserRegForm(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm
    """
    error_messages = {
        'duplicate_email': "A user with that email address already exists.",
    }

    email = forms.EmailField()

    #password = forms.CharField(label="Password", widget=forms.PasswordInput)

    class Meta:
        model = LinkUser
        fields = ("email", "first_name", "last_name")

    def clean_email(self):
        # Since User.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM.

        email = self.cleaned_data["email"]
        try:
            LinkUser.objects.get(email=email)
        except LinkUser.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])


class UserFormSelfEdit(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is stripped down even further to match our editing needs
    """

    class Meta:
        model = LinkUser
        fields = ("first_name", "last_name", "email")

    email = forms.EmailField()


class SetPasswordForm(forms.Form):
    """
A form that lets a user change set his/her password without entering the
old password
"""
    error_messages = {
        'password_mismatch': "The two password fields didn't match.",
    }

    new_password1 = forms.CharField(label="New password",
                                    widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="New password confirmation",
                                    widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SetPasswordForm, self).__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                logger.debug('mismatch')
                raise forms.ValidationError(self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user


class UploadFileForm(forms.Form):
    title = forms.CharField(required=True)
    url = forms.URLField(required=True)
    file  = forms.FileField(required=True)


class ContactForm(forms.Form):
    """
    The form we use on the contact page. Just an email (optional)
    and a message
    """

    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
