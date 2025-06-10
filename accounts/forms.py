from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth.forms import SetPasswordForm  as DjangoSetPasswordForm
from django.contrib.auth import get_user_model
from .models import CustomUser

User = get_user_model()

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'forms-control', 'placeholder': 'youremail@gmail.com'}))
    username = forms.CharField(required=True, max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'username'}))
    password1 = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'enter password'}))
    password2 = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'confirm password'}))

    class Meta:
        model = User
        fields = ['email', 'username', 'password1', 'password2']

        # check if an email already exists
        def clean_email(self):
            email = self.cleaned_data.get("email")
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError("A user with this email already exists.")
            return email
        
        # check if a username exists
        def clean_username(self):
            username = self.cleaned_data.get("username")
            if User.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError("Username already exists.")

        # Check that the two password entries matc
        def clean_password(self):
            password1 = self.cleaned_data.get("password1")
            password2 = self.cleaned_data.get("password2")

            if password1 and password2 and password1 != password2: 
                raise forms.ValidationError("Password don't match")
            if password1 and len(password1) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long")
            raise password2
        
        def save(self, commit=True):
            user = super().save(commit=False)
            user.set_password(self.cleaned_data["password1"])
            if commit:
                user.save()
            return user
        
class LoginForm(forms.Form):
    email = forms.EmailField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'email'}))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    remember_me = forms.BooleanField(required=False, initial=False, widget=forms.CheckboxInput())

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email does not exist.")
        return email

# a form for requesting a new password
class PasswordResetForm(forms.Form):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class':'form-control', 'placeholder':'email-address', 'autocomplete':'email'}))

    def clean_email(self):
        email = self.cleaned_data["email"]
        if email:
            email = email.lower()
        return email
    
# set a new password
class SetPasswordForm(DjangoSetPasswordForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder': 'enter new password', 'autocomplete':'new-password'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder': 'confirm password', 'autocomplete':'new-password'}),
        strip=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', "The two password fields didn't match.")
        return cleaned_data
