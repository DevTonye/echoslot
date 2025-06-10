from django import forms
from .models import ServiceProvider, Service, Appointment
import datetime

class ServiceProviderForm(forms.ModelForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'forms-control', 'placeholder':'enter your firstname'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'forms-control', 'placeholder': 'enter your lastname'}))
    service_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'forms-control', 'placeholder': 'service name'}))
    description = forms.CharField(required=True, widget=forms.Textarea(attrs={'class':'forms-control', 'placeholder': 'tell us about your service', 'rows': 4}))
    address = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'forms-controle', 'placeholder':'Enter your address'}))
    phone = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'forms-controle', 'placeholder':'Enter your phone number'}))

    class Meta:
        model = ServiceProvider
        fields = ['first_name', 'last_name', 'service_name', 'description', 'address', 'phone']

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'duration', 'price']