import logging

from django import forms
from django.contrib.auth.models import User, Group
from django.forms import ModelForm

from perma.models import Registrar, VestingOrg, LinkUser

logger = logging.getLogger(__name__)


class RegistrarForm(ModelForm):
    class Meta:
        model = Registrar
        fields = ['name', 'email', 'website']
        
        
class VestingOrgWithRegistrarForm(ModelForm):

    registrar = forms.ModelChoiceField(queryset=Registrar.objects.all(), empty_label=None)
    
    class Meta:
        model = VestingOrg
        fields = ['name', 'registrar']
        
        
class VestingOrgForm(ModelForm):
    
    class Meta:
        model = VestingOrg
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


class CreateUserFormWithVestingOrg(CreateUserForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm
    """
    def __init__(self, *args, **kwargs):
      registrar_id = False
      if 'registrar_id' in kwargs:
        registrar_id = kwargs.pop('registrar_id')
      super(CreateUserFormWithVestingOrg, self).__init__(*args, **kwargs)
      if registrar_id:
        self.fields['vesting_org'].queryset = VestingOrg.objects.filter(registrar_id=registrar_id).order_by('name')
    
    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "vesting_org"]

    vesting_org = forms.ModelChoiceField(queryset=VestingOrg.objects.all().order_by('name'), empty_label=None, label="Vesting organization")

    def clean_vesting_org(self):
        vesting_org = self.cleaned_data["vesting_org"]
        return vesting_org


class UserFormEdit(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is the edit form, so we strip it down even more
    """
    error_messages = {

    }

    email = forms.EmailField()
                         
    group = forms.ModelChoiceField(queryset=Group.objects.all(), empty_label=None)

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email"]

    def save(self, commit=True):
        user = super(UserFormEdit, self).save(commit=False)
        group = self.cleaned_data['group']
        all_groups = Group.objects.all()
        for ag in all_groups:
          user.groups.remove(ag)
        user.groups.add(group)

        if commit:
            user.save()

        return user
        

class RegistrarMemberFormEdit(UserFormEdit):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is the edit form, so we strip it down even more
    """

    registrar = forms.ModelChoiceField(queryset=Registrar.objects.all().order_by('name'), empty_label=None)
    
    group = forms.ModelChoiceField(queryset=Group.objects.all(), empty_label=None)

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "registrar"]

        
class VestingMemberFormEdit(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is stripped down even further to match out editing needs
    """

    class Meta:
        model = LinkUser
        fields = ("first_name", "last_name", "email")

    email = forms.EmailField()
    

class VestingMemberWithVestingOrgFormEdit(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is stripped down even further to match out editing needs
    """
    
    def __init__(self, *args, **kwargs):
      registrar_id = False
      if 'registrar_id' in kwargs:
        registrar_id = kwargs.pop('registrar_id')
      super(VestingMemberWithVestingOrgFormEdit, self).__init__(*args, **kwargs)
      if registrar_id:
        self.fields['vesting_org'].queryset = VestingOrg.objects.filter(registrar_id=registrar_id).order_by('name')

    class Meta:
        model = LinkUser
        fields = ("first_name", "last_name", "email", "vesting_org")


    email = forms.EmailField()

    vesting_org = forms.ModelChoiceField(queryset=VestingOrg.objects.all().order_by('name'), empty_label=None, label="Vesting organization")
    
        
class VestingMemberWithGroupFormEdit(VestingMemberFormEdit):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is stripped down even further to match out editing needs
    """
                         
    def __init__(self, *args, **kwargs):
      registrar_id = False
      if 'registrar_id' in kwargs:
        registrar_id = kwargs.pop('registrar_id')
      super(VestingMemberWithGroupFormEdit, self).__init__(*args, **kwargs)
      if registrar_id:
        self.fields['group'].queryset = Group.objects.filter(name__startswith='vesting')
        self.fields['vesting_org'].queryset = VestingOrg.objects.filter(registrar_id=registrar_id).order_by('name')
        
    class Meta:
        model = LinkUser
        fields = ("first_name", "last_name", "email", "vesting_org", "group")
    
    group = forms.ModelChoiceField(queryset=Group.objects.all(), empty_label=None, label="Role")
    vesting_org = forms.ModelChoiceField(queryset=VestingOrg.objects.all().order_by('name'), empty_label=None, label="Vesting organization")

    def save(self, commit=True):
        user = super(VestingMemberWithGroupFormEdit, self).save(commit=False)
        group = self.cleaned_data['group']
        all_groups = Group.objects.all()
        for ag in all_groups:
          user.groups.remove(ag)
        user.groups.add(group)

        if commit:
            user.save()

        return user

        
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
        
        
class UserAddVestingOrgForm(forms.ModelForm):
    """
    add a vesting org when a regular user is promoted to a vesting user or vesting manager
    """

    class Meta:
        model = LinkUser
        fields = ("vesting_org",)         

    vesting_org = forms.ModelChoiceField(queryset=VestingOrg.objects.all().order_by('name'), empty_label=None, label="Vesting organization")
    
    def save(self, commit=True):
        user = super(UserAddVestingOrgForm, self).save(commit=False)

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

    This is stripped down even further to match out editing needs
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
