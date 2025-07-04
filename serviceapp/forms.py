from django import forms
from .models import ServiceProvider, Service, AvailabilitySchedule, Appointment
import datetime
from datetime import datetime, timedelta, date
from django.core.exceptions import ValidationError

class ServiceProviderForm(forms.ModelForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'enter your firstname'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'enter your lastname'}))
    description = forms.CharField(required=True, widget=forms.Textarea(attrs={'class':'form-control', 'placeholder': 'tell us about your service', 'rows': 4}))
    address = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Enter your address'}))
    phone = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Enter your phone number'}))

    class Meta:
        model = ServiceProvider
        fields = ['first_name', 'last_name', 'description', 'address', 'phone']

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
    first_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter your last name'
        })
    )
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'your@email.com'
        })
    )
    phone = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+234 812 345 6789'
        })
    )
    service = forms.ModelChoiceField(
        queryset=Service.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    appointment_date = forms.DateField(
    widget=forms.DateInput(attrs={'type': 'date'}),
    initial=datetime.today().strftime('%Y-%m-%d %H:%M:%S') 
)

    start_time = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select an available time slot"
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4, 
            'class': 'form-control',
            'placeholder': 'Please describe your symptoms or reason for the appointment...'
        }),
        required=False
    )

    class Meta:
        model = Appointment
        fields = ['first_name', 'last_name', 'email', 'phone', 'service', 
                 'appointment_date', 'start_time', 'notes']

    def __init__(self, *args, **kwargs):
        self.provider_id = kwargs.pop('provider_id', None)
        self.available_slots = kwargs.pop('available_slots', {})
        super().__init__(*args, **kwargs)

        if self.provider_id:
            self.fields['service'].queryset = Service.objects.filter(provider_id=self.provider_id)
        
        # Populate time choices from available slots
        self.update_time_choices()

    def update_time_choices(self):
        """Update time field choices based on available slots"""
        choices = [('', 'Select a time slot')]
        
        for date, slots in self.available_slots.items():
            date_label = date.strftime('%A, %B %d, %Y')
            for slot in slots:
                if slot['available']:
                    choice_value = f"{date.isoformat()}|{slot['time'].strftime('%H:%M')}"
                    choice_label = f"{date_label} - {slot['display']}"
                    choices.append((choice_value, choice_label))
        
        self.fields['start_time'].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get('service')
        appointment_date = cleaned_data.get('appointment_date')
        start_time_choice = cleaned_data.get('start_time')
    
       
        if start_time_choice and '|' in start_time_choice:
            # Parse the combined date|time value
            date_str, time_str = start_time_choice.split('|')
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            parsed_time = datetime.strptime(time_str, '%H:%M').time()
            
            # Update the cleaned data
            cleaned_data['appointment_date'] = parsed_date
            cleaned_data['start_time'] = parsed_time
            
            # Validate the slot is still available
            if not self.is_slot_available(parsed_date, parsed_time, service):
                raise ValidationError("This time slot is no longer available.")
            
            # Calculate end time
            if service:
                start_datetime = datetime.combine(parsed_date, parsed_time)
                end_datetime = start_datetime + timedelta(minutes=service.duration)
                cleaned_data['end_time'] = end_datetime.time()

        return cleaned_data
    
    def is_slot_available(self, date, time, service):
        """Check if a specific time slot is still available"""
        if not service:
            return False
            
        # Check for overlapping appointments
        end_time = (datetime.combine(date, time) + timedelta(minutes=service.duration)).time()
        
        overlapping = Appointment.objects.filter(
            service__provider=service.provider,
            appointment_date=date,
            status__in=['scheduled', 'confirmed']
        ).exclude(pk=self.instance.pk if self.instance else None)
        
        for existing in overlapping:
            if time < existing.end_time and end_time > existing.start_time:
                return False
        return True
    
class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status']
