import logging

from django import forms
from django.forms import ModelForm
from django.forms.widgets import flatatt
from django.utils.html import mark_safe

from perma.models import Registrar, VestingOrg, LinkUser

logger = logging.getLogger(__name__)

class RegistrarForm(ModelForm):
    class Meta:
        model = Registrar
        fields = ['name', 'email', 'website']
        
        
class VestingOrgWithRegistrarForm(ModelForm):

    registrar = forms.ModelChoiceField(queryset=Registrar.objects.all().order_by('name'), empty_label=None)
    
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


class CreateUserFormWithVestingOrg(CreateUserForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm
    """
    def __init__(self, *args, **kwargs):
        registrar_id = False
        vesting_org_member_id = False

        if 'registrar_id' in kwargs:
            registrar_id = kwargs.pop('registrar_id')

        if 'vesting_org_member_id' in kwargs:
            vesting_org_member_id = kwargs.pop('vesting_org_member_id')

        super(CreateUserFormWithVestingOrg, self).__init__(*args, **kwargs)

        if registrar_id:
            self.fields['vesting_org'].queryset = VestingOrg.objects.filter(registrar_id=registrar_id).order_by('name')

        if vesting_org_member_id:
            user = LinkUser.objects.get(id=vesting_org_member_id)
            self.fields['vesting_org'].queryset = user.vesting_org.all()

    
    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "vesting_org"]

    vesting_org = forms.ModelMultipleChoiceField(queryset=VestingOrg.objects.all().order_by('name'),label="Vesting organization", widget=CustomSelectSingleAsList)


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
        fields = ["vesting_org"]

    vesting_org = forms.ModelMultipleChoiceField(queryset=VestingOrg.objects.all().order_by('name'),label="Vesting organization", required=False,)
    

class VestingMemberWithVestingOrgAsVestingMemberFormEdit(forms.ModelForm):
    """
    TODO: this form has a gross name. rename it.
    """
    
    def __init__(self, *args, **kwargs):
        vesting_user_id = False
        if 'vesting_user_id' in kwargs:
            vesting_user_id = kwargs.pop('vesting_user_id')
        super(VestingMemberWithVestingOrgAsVestingMemberFormEdit, self).__init__(*args, **kwargs)
        if vesting_user_id:
            editing_user = LinkUser.objects.get(pk=vesting_user_id)
            self.fields['vesting_org'].queryset = editing_user.vesting_org.all().order_by('name')

    class Meta:
        model = LinkUser
        fields = ["vesting_org"]

    vesting_org = forms.ModelMultipleChoiceField(queryset=VestingOrg.objects.all().order_by('name'),label="Vesting organization", required=False,)

        
class VestingMemberWithGroupFormEdit(UserFormEdit):
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
            self.fields['vesting_org'].queryset = VestingOrg.objects.filter(registrar_id=registrar_id).order_by('name')
        
    class Meta:
        model = LinkUser
        fields = ("first_name", "last_name", "email", "vesting_org",)

    vesting_org = forms.ModelChoiceField(queryset=VestingOrg.objects.all().order_by('name'), empty_label=None, label="Vesting organization", required=False,)

        
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

    def __init__(self, *args, **kwargs):
        registrar_id = False
        vesting_org_member_id = False

        if 'registrar_id' in kwargs:
            registrar_id = kwargs.pop('registrar_id')

        if 'vesting_org_member_id' in kwargs:
            vesting_org_member_id = kwargs.pop('vesting_org_member_id')

        super(UserAddVestingOrgForm, self).__init__(*args, **kwargs)

        vesting_org_member = LinkUser.objects.get(pk=vesting_org_member_id)

        # Vesting managers can only edit their own vesting members
        if registrar_id:
            # Get the union of the user's and the registrar member's vesting orgs
            vesting_orgs = vesting_org_member.vesting_org.all() | VestingOrg.objects.filter(registrar_id=registrar_id)

        elif vesting_org_member_id:
            vesting_orgs = vesting_org_member.vesting_org.all()

        else:
            # Must be registry member
            vesting_orgs = VestingOrg.objects.all()

        #self.fields['vesting_org'].queryset = vesting_orgs.order_by('name')

        self.fields['vesting_org'] = forms.ModelMultipleChoiceField(queryset=vesting_orgs.order_by('name'), label="Vesting organization", widget=CustomSelectSingleAsList)



    class Meta:
        model = LinkUser
        fields = ("vesting_org",)         



    #vesting_org = forms.ModelChoiceField(queryset=self.fields.vesting_orgs.order_by('name'), empty_label=None, label="Vesting organization", widget=CustomSelectSingleAsList)




    
    
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
