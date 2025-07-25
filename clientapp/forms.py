from .models import ClientProfile
from django import forms

class ClientProfileForm(forms.ModelForm):
    COMMON_TIMEZONES = [
        ('UTC', 'UTC'),
        ('Africa/Lagos', 'Lagos (UTC+1)'),
        ('Europe/London', 'London (UTC+0/+1)'),
        ('America/New_York', 'New York (UTC-5/-4)'),
        ('America/Los_Angeles', 'Los Angeles (UTC-8/-7)'),
        ('Asia/Tokyo', 'Tokyo (UTC+9)'),
        ('Asia/Shanghai', 'Shanghai (UTC+8)'),
        ('Australia/Sydney', 'Sydney (UTC+10/+11)'),
        ('Europe/Paris', 'Paris (UTC+1/+2)'),
        ('Asia/Dubai', 'Dubai (UTC+4)'),
        ('America/Chicago', 'Chicago (UTC-6/-5)'),
        ('Asia/Kolkata', 'Mumbai/Delhi (UTC+5:30)'),
        ('Europe/Berlin', 'Berlin (UTC+1/+2)'),
        ('America/Toronto', 'Toronto (UTC-5/-4)'),
        ('Pacific/Auckland', 'Auckland (UTC+12/+13)'),
    ]

    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'enter your firstname'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'enter your lastname'}))
    location = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Enter your address'}))
    contact = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Enter your phone number'}))
    timezone = forms.ChoiceField(choices=COMMON_TIMEZONES, widget=forms.Select(attrs={'class': 'form-control'}), help_text="Select your timezone for accurate appointment times")

    class Meta:
        model = ClientProfile
        fields = ['first_name', 'last_name', 'location', 'contact', 'profile_image', 'timezone']
        widgets = {
            'profile_image':forms.ClearableFileInput(attrs={'multiple':False}) # Keep as single file input
        }