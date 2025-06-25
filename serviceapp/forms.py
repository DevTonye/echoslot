from django import forms
from .models import ServiceProvider, Service, AvailabilitySchedule, Appointment
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

# a form for service providers can use to set their availability
class AvailabilityScheduleForm(forms.ModelForm):
    class Meta:
        model = AvailabilitySchedule
        fields = ['day_of_week', 'start_time', 'end_time']
        widgets = {
            'day_of_week': forms.Select(),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        self.service_provider = kwargs.pop('service_provider', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time >= end_time: 
                raise forms.ValidationError("End time must be after start time.")

        if self.service_provider:
            day = cleaned_data.get('day_of_week')
            # Check if provider already has availability for this day (if creating)
            if not self.instance.pk and AvailabilitySchedule.objects.filter(service_provider=self.service_provider, day_of_week=day).exists():
                raise forms.ValidationError("You have already set availability for this day.")
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.service_provider:
            instance.service_provider = self.service_provider
        if commit:
            instance.save()
        return instance
    
class AppointmentForm(forms.ModelForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'forms-control', 'placeholder':'enter your firstname'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'forms-control', 'placeholder':'enter your lastname'}))
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'your@gmail.com'}))
    phone = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': '+234 812 345 6789'}))
    service = forms.ModelChoiceField(queryset=Service.objects.none())
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=datetime.date.today
    )
    start_time = forms.TimeField(
        widget=forms.Select(choices=[]),
        help_text="Select an available time slot"
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Please describe your symptoms or reason for the appointment...'}),
        required=False
    )
    class Meta:
        model = Appointment
        fields = ['first_name', 'last_name', 'email', 'phone', 'service', 'appointment_date', 'start_time', 'notes']

    def __init__(self, *args, **kwargs):
        self.provider_id = kwargs.pop('provider_id', None)
        super().__init__(*args, **kwargs)

        if self.provider_id:
            self.fields['service'].queryset = Service.objects.filter(provider_id=self.provider_id)

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get('service')
        appointment_date = cleaned_data.get('appointment_date')
        start_time = cleaned_data.get('start_time')

        if service and appointment_date and start_time:
            # Calculate end time using timedelta
            start_datetime = datetime.datetime.combine(appointment_date, start_time)
            end_datetime = start_datetime + datetime.timedelta(minutes=service.duration)
            end_time = end_datetime.time()

            # Check for overlapping appointments
            overlapping_appointments = Appointment.objects.filter(
                service__provider=service.provider,
                appointment_date=appointment_date,
                status__in=['scheduled', 'confirmed']
            )

            if self.instance.pk:
                overlapping_appointments = overlapping_appointments.exclude(pk=self.instance.pk)

            for existing in overlapping_appointments:
                if start_time < existing.end_time and end_time > existing.start_time:
                    raise forms.ValidationError("This time slot is already booked.")

            cleaned_data['end_time'] = end_time

        return cleaned_data
