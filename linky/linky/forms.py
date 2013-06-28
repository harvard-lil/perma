from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm

from linky.models import Registrar


class registrar_form(ModelForm):
    class Meta:
        model = Registrar
        fields = ['name']

class regisrtar_member_form(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm
    """
    error_messages = {
        'duplicate_username': "A user with that username already exists.",
        'duplicate_email': "A user with that email address already exists.",
    }
    username = forms.RegexField(label="Username", max_length=30,
        regex=r'^[\w.@+-]+$',
        help_text = "30 characters or fewer. Letters, digits and "
                      "@/./+/-/_ only.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})
    
    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})
    
    
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    
    registrar = forms.ModelChoiceField(queryset=Registrar.objects.all(), empty_label=None)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "password", "registrar")


    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])
    
    def clean_email(self):
        # Since User.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM.
        
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def clean_registrar(self):
        return self.data.get('a-registrar')

    def save(self, commit=True):
        user = super(regisrtar_member_form, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
            
            profile = user.get_profile()
            registrar = Registrar.objects.get(id=self.cleaned_data["registrar"])
            profile.registrar = registrar
            profile.save()
        return user
        
        
class journal_member_form(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm
    """
    error_messages = {
        'duplicate_username': "A user with that username already exists.",
        'duplicate_email': "A user with that email address already exists.",
    }
    username = forms.RegexField(label="Username", max_length=30,
        regex=r'^[\w.@+-]+$',
        help_text = "30 characters or fewer. Letters, digits and "
                      "@/./+/-/_ only.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})

    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})


    password = forms.CharField(label="Password", widget=forms.PasswordInput)


    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "password")


    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])

    def clean_email(self):
        # Since User.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM.

        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def save(self, commit=True):
        user = super(journal_member_form, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user
        

class user_reg_form(forms.ModelForm):
    """
    stripped down user reg form
    This is mostly a django.contrib.auth.forms.UserCreationForm
    """
    error_messages = {
        'duplicate_username': "A user with that username already exists.",
        'duplicate_email': "A user with that email address already exists.",
    }
    username = forms.RegexField(label="Username", max_length=30,
        regex=r'^[\w.@+-]+$',
        help_text = "30 characters or fewer. Letters, digits and "
                      "@/./+/-/_ only.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})
    
    email = forms.RegexField(label="Email", required=True, max_length=254,
        regex=r'^[\w.@+-]+$',
        help_text = "Letters, digits and @/./+/-/_ only. 254 characters or fewer.",
        error_messages = {
            'invalid': "This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."})
    
    
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])
    
    def clean_email(self):
        # Since User.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM.
        
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def save(self, commit=True):
        user = super(user_reg_form, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user