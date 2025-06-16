from .models import ClientProfile
from django import forms

class ClientProfileForm(forms.ModelForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'enter your firstname'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'enter your lastname'}))
    location = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-controle', 'placeholder':'Enter your address'}))
    contact = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-controle', 'placeholder':'Enter your phone number'}))

    class Meta:
        model = ClientProfile
        fields = ['first_name', 'last_name', 'location', 'contact', 'profile_image']
        widgets = {
            'profile_image':forms.ClearableFileInput(attrs={'multiple':False}) # Keep as single file input
        }