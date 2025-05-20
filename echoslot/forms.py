from django import forms
from .models import ServiceProvider, Appointment, Service
from django.utils import timezone
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
        
class AppointmentForm(forms.ModelForm):
    service = forms.ModelChoiceField(queryset=Service.objects.none())
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=datetime.date.today        
    )
    start_time = forms.TimeField(
        widget=forms.Select(choices=[]),
        help_text="Select an availabe time slot"
    )

    class Meta:
        model = Appointment
        fields = ['service', 'appointment_date', 'start_time']

    def __init__(self, *args, **kwargs):
        """
        preven users from choosing services that doesn't belong to 
        the selected service provider 
        """
        provider_id = kwargs.pop('provider_id', None)
        super().__init__(*args, **kwargs)

        if provider_id:
            # only show services offered by that provider
            self.fields['service'].queryset = Service.objects.filter(provider_id=provider_id)

    def clean(self):
        # prevent double booking 
        cleaned_data = super().clean()
        service = cleaned_data.get('service')
        appointment_date = cleaned_data.get('appointment_date')
        start_time = cleaned_data.get('start_time')

        if service and appointment_date and start_time:
            # Calculate end time based on service duration
            hour, minute = start_time.hour, start_time.mintue
            minutes_to_add = service.duration
            end_time_minutes = (minute + minutes_to_add) % 60 # handles minute overflow (beyond 60)
            end_time_hours = (hour + (minute + minutes_to_add) // 60) % 24
            end_time = datetime.time(end_time_hours, end_time_minutes)
            """
            This calculates when the appointment will end based on:
            The start time selected by the client
            The duration of the selected service provider
            """

            # check if this time slot is available
            overlapping_appointments = Appointment.objects.filter(
                service__provider=service.provider,
                appointment_date=appointment_date,
                status__in=['scheduled', 'confirmed'],
            ).exclude(pk=self.instance.pk if self.instance.pk else None)

            for existing_appointment in overlapping_appointments:
                if ( start_time < existing_appointment.end_time and end_time > existing_appointment.start_time):
                    raise forms.ValidationError('This time slot is already booked')
                
            # Add end_time to cleaned_data for saving
            cleaned_data['end_time'] = end_time
        return cleaned_data