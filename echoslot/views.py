from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ServiceProvider, Service, Notification, Appointment
from .forms import ServiceProviderForm, AppointmentForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from accounts.models import CustomUser
from django.utils import timezone
import datetime

User = get_user_model()

# landing page view
def index(request):
    return render(request, 'echoslot/index.html')

# service provider profile view
@login_required
def complete_provider_profile(request):
    if request.user.role != CustomUser.UserRole.SERVICE_PROVIDER:
        messages.success(request, 'You are not authorized to access this page')
        return redirect('echoslot:index')
    
    if hasattr(request.user, 'serviceprovider'):
        messages.info(request, "You've already completed your provider profile.")
        return redirect('echoslot:index') # dashborad later

    if request.method == 'POST':
        form = ServiceProviderForm(request.POST)
        if form.is_valid():
            provider = form.save(commit=False)
            provider.user = request.user
            provider.save()
            messages.success(request, 'Your provider account has been created!')
            return redirect('echoslot:index') # dashborad later
    else:
        form = ServiceProviderForm()
    return render(request,  'echoslot/provider_signup.html', {'form': form})

@login_required
def book_appointmen(request, provider_id):
    """ book an appointment with service provider"""
    provider = get_object_or_404(ServiceProvider, pk=provider_id)

    if request.method == 'POST':
        form = AppointmentForm(request.POST, provider_id=provider_id)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = request.user
            appointment.end_time = form.cleaned_data['end_time']
            appointment.save()

            # Create notifications
            appt_date = appointment.appointment_date
            appt_time = appointment.start_time
            appt_datetime = timezone.make_aware(
                datetime.datetime.combine(appt_date, appt_time)
            )

            # Notification 1 day before
            reminder_time = appt_datetime - datetime.timedelta(days=1)
            Notification.objects.create(
                appointment=appointment, 
                notification_type='email', 
                scheduled_for=reminder_time, 
                message=f"Reminder: You have an appointment for {appointment.service.name} tomorrow at {appointment.start_time}."
            )

            # Notification 2 hours before
            reminder_time = appt_datetime - datetime.timedelta(hours=2)
            Notification.objects.create(
                appointment=appointment,
                notification_type='sms', 
                scheduled_for=reminder_time,
                message=f"Reminder: Your appointment for {appointment.service.name} is in 2 hours at {appointment.start_time}."
            )

            messages.success(request, 'Appointment booked successfully!')
            return redirect('echoslot:appointsuccess', appointment_id=appointment.appointment_id)
    else:
        form = AppointmentForm()
    context = {
        'provider':provider,
        'form':form,
        'services': Service.objects.filter(provider=provider)
    }
    return render(request, 'echoslot/bookappointment.html', context)


@login_required
def appointment_success(request, appointment_id):
    appointment = get_object_or_404(Appointment)
def dashborad(request):

    return render(request, 'echoslot/dashborad')