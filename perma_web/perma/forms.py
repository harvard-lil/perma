import logging

from django import forms
from django.contrib.auth.models import User, Group
from django.forms import ModelForm

from perma.models import Registrar
from perma.models import LinkUser

logger = logging.getLogger(__name__)


class registrar_form(ModelForm):
    class Meta:
        model = Registrar
        fields = ['name', 'email', 'website']

class regisrtar_member_form(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm
    """
    error_messages = {
        'duplicate_email': "A user with that email address already exists.",
    }

    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})

    registrar = forms.ModelChoiceField(queryset=Registrar.objects.all(), empty_label=None)

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "registrar"]

    def clean_email(self):
        # Since User.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM.

        email = self.cleaned_data["email"]
        try:
            LinkUser.objects.get(email=email)
        except LinkUser.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def clean_registrar(self):
        registrar = self.cleaned_data["registrar"]
        return registrar

    def save(self, commit=True):
        user = super(regisrtar_member_form, self).save(commit=False)

        if commit:
            user.save()

        return user


class regisrtar_member_form_edit(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is the edit form, so we strip it down even more
    """
    error_messages = {

    }

    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})

    registrar = forms.ModelChoiceField(queryset=Registrar.objects.all(), empty_label=None)
    
    group = forms.ModelChoiceField(queryset=Group.objects.all(), empty_label=None)

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "registrar"]

    def save(self, commit=True):
        user = super(regisrtar_member_form_edit, self).save(commit=False)
        group = self.cleaned_data['group']
        all_groups = Group.objects.all()
        for ag in all_groups:
          user.groups.remove(ag)
        user.groups.add(group)

        if commit:
            user.save()

        return user

class manage_user_form(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm
    """
    error_messages = {
        'duplicate_email': "A user with that email address already exists.",
    }

    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email"]

    def clean_email(self):
        # Since User.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM.

        email = self.cleaned_data["email"]
        try:
            LinkUser.objects.get(email=email)
        except LinkUser.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def save(self, commit=True):
        user = super(manage_user_form, self).save(commit=False)

        if commit:
            user.save()

        return user


class user_form_edit(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is the edit form, so we strip it down even more
    """
    error_messages = {

    }

    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})
                         
    group = forms.ModelChoiceField(queryset=Group.objects.all(), empty_label=None)

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email"]

    def save(self, commit=True):
        user = super(user_form_edit, self).save(commit=False)
        group = self.cleaned_data['group']
        all_groups = Group.objects.all()
        for ag in all_groups:
          user.groups.remove(ag)
        user.groups.add(group)

        if commit:
            user.save()

        return user

class journal_manager_form(forms.ModelForm):

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

    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})

    def clean_email(self):
        # Since User.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM.

        email = self.cleaned_data["email"]
        try:
            LinkUser.objects.get(email=email)
        except LinkUser.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def save(self, commit=True):
        user = super(journal_manager_form, self).save(commit=False)

        if commit:
            user.save()

        return user

class journal_manager_w_registrar_form(forms.ModelForm):

    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm
    """

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "registrar"]


    error_messages = {
        'duplicate_email': "A user with that email address already exists.",
    }

    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})

    registrar = forms.ModelChoiceField(queryset=Registrar.objects.all(), empty_label=None)

    def clean_email(self):
        # Since User.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM.

        email = self.cleaned_data["email"]
        try:
            LinkUser.objects.get(email=email)
        except LinkUser.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def save(self, commit=True):
        user = super(journal_manager_w_registrar_form, self).save(commit=False)

        if commit:
            user.save()

        return user


class journal_manager_form_edit(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is stripped down even further to match out editing needs
    """

    class Meta:
        model = LinkUser
        fields = ("first_name", "last_name", "email")


    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})                 

    def save(self, commit=True):
        user = super(journal_manager_form_edit, self).save(commit=False)

        if commit:
            user.save()

        return user
        
class journal_manager_w_group_form_edit(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is stripped down even further to match out editing needs
    """

    class Meta:
        model = LinkUser
        fields = ("first_name", "last_name", "email")


    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})
                         
    group = forms.ModelChoiceField(queryset=Group.objects.all(), empty_label=None)

    def save(self, commit=True):
        user = super(journal_manager_w_group_form_edit, self).save(commit=False)
        group = self.cleaned_data['group']
        all_groups = Group.objects.all()
        for ag in all_groups:
          user.groups.remove(ag)
        user.groups.add(group)

        if commit:
            user.save()

        return user


class journal_member_form(forms.ModelForm):

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

    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})

    def clean_email(self):
        # Since User.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM.

        email = self.cleaned_data["email"]
        try:
            LinkUser.objects.get(email=email)
        except LinkUser.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def save(self, commit=True):
        user = super(journal_member_form, self).save(commit=False)

        if commit:
            user.save()

        return user

class journal_member_w_registrar_form(forms.ModelForm):

    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm
    """

    class Meta:
        model = LinkUser
        fields = ["first_name", "last_name", "email", "registrar"]


    error_messages = {
        'duplicate_email': "A user with that email address already exists.",
    }

    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})

    registrar = forms.ModelChoiceField(queryset=Registrar.objects.all(), empty_label=None)

    def clean_email(self):
        # Since User.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM.

        email = self.cleaned_data["email"]
        try:
            LinkUser.objects.get(email=email)
        except LinkUser.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def save(self, commit=True):
        user = super(journal_member_w_registrar_form, self).save(commit=False)

        if commit:
            user.save()

        return user


class journal_member_form_edit(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is stripped down even further to match out editing needs
    """

    class Meta:
        model = LinkUser
        fields = ("first_name", "last_name", "email")


    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})

    def save(self, commit=True):
        user = super(journal_member_form_edit, self).save(commit=False)

        if commit:
            user.save()

        return user
        
class journal_member_w_group_form_edit(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is stripped down even further to match out editing needs
    """

    class Meta:
        model = LinkUser
        fields = ("first_name", "last_name", "email")


    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})
                         
    group = forms.ModelChoiceField(queryset=Group.objects.all(), empty_label=None)

    def save(self, commit=True):
        user = super(journal_member_w_group_form_edit, self).save(commit=False)
        group = self.cleaned_data['group']
        all_groups = Group.objects.all()
        for ag in all_groups:
          user.groups.remove(ag)
        user.groups.add(group)

        if commit:
            user.save()

        return user


class user_reg_form(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm
    """
    error_messages = {
        'duplicate_email': "A user with that email address already exists.",
    }

    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})

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

    def save(self, commit=True):
        user = super(user_reg_form, self).save(commit=False)
        #user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class user_form_self_edit(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm

    This is stripped down even further to match out editing needs
    """

    class Meta:
        model = LinkUser
        fields = ("first_name", "last_name", "email")


    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})

    def save(self, commit=True):
        user = super(user_form_self_edit, self).save(commit=False)

        if commit:
            user.save()

        return user


class set_password_form(forms.Form):
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
        super(set_password_form, self).__init__(*args, **kwargs)

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
