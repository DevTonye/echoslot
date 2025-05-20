from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ServiceProvider, Service, Notification, Appointment
from .forms import ServiceProviderForm, ServiceForm, AppointmentForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from accounts.models import CustomUser
from django.utils import timezone
import datetime
from django.db.models import Q

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
    
    '''
    if hasattr(request.user, 'service_provider'):
        messages.info(request, "You've already completed your provider profile.")
        return redirect('echoslot:index') # dashborad later
    '''

    if request.method == 'POST':
        form = ServiceProviderForm(request.POST)
        if form.is_valid():
            provider = form.save(commit=False)
            provider.user = request.user
            provider.save()
            messages.success(request, 'Your service account has been created!')
            return redirect('echoslot:dashboard') # dashborad later
    else:
        form = ServiceProviderForm()
    return render(request, 'echoslot/completeprofile.html', {'form': form})

@login_required
def book_appointment(request, provider_id):
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
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id, client=request.user)
    return render(request, 'echoslot/appointmentsuccess.html', {'appointment': appointment})

@login_required
def view_appointments(request):
    # get all upcoming appointments for a client
    upcoming_appointments = Appointment.objects.filter(
        client=request.user,
        appointment_date__gte = timezone.now().date(),
        status__in=['scheduled', 'confirmed']
    ).order_by('appointment_date', 'start_time')

    # view past appointments
    past_appointments = Appointment.objects.filter(
        client=request.user
    ).filter(
        Q(appointment_date__lt=timezone.now().date()) | Q(status__in=['completed', 'cancelled', 'no_show'])
    ).order_by('-appointment_date', '-start_time')

    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments
    }
    return render(request, 'echoslot/viewappointment.html', context)

def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id, client=request.user)

    if appointment.status not in ['scheduled', 'confirmed']:
        messages.error(request, "This appointment cannot be cancelled.")
        return redirect('echoslot:viewappointments')
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully')
        return redirect('echoslot:viewappointments')
    
    return render(request, 'echoslot/cancelappointment.html', {'appointment': appointment})

def sp_dashboard(request):
    user = request.user
     # Check if the user has the correct role
    if user.role != CustomUser.UserRole.SERVICE_PROVIDER:
        messages.error(request, 'You need to register as a service provider first.')
        return redirect('accounts:select_role') # will update later  
    # Check if the service provider profile exists
    try: 
        provider = user.service_provider  
    except ServiceProvider.DoesNotExist:
        messages.error(request, 'You need to register as a service provider first.')
        return redirect('accounts:register')
    
    today = timezone.now().date()
    today_appointments = Appointment.objects.filter(
        service__provider=provider,
        appointment_date=today, 
        status__in=['scheduled', 'confirmed']
    ).order_by('start_time')

    upcoming_appointments = Appointment.objects.filter(
        service__provider=provider,
        appointment_date__gt=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('appointment_date', 'start_time')

    services = Service.objects.filter(provider=provider)

    context = {
        'provider':provider,
        'today_appointments':today_appointments,
        'upcoming_appointments':upcoming_appointments,
        'services':services
    }
    return render(request, 'echoslot/dashboard.html', context)

@login_required
def add_service(request):
    user = request.user

    if user.role != CustomUser.UserRole.SERVICE_PROVIDER:
        messages.error(request, 'Access denied: Your account is not registered as a service provider.')
        return redirect('accounts:select_role')
    try:
        provider = user.service_provider
    except ServiceProvider.DoesNotExist:
        messages.error(request, 'You need to register as a service provider first.')
        return redirect('provider_signup')
    
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.provider = provider
            service.save()
            messages.success(request, 'Service added successfully.')
            return redirect('echoslot:dashboard')
    else:
        form = ServiceForm()
    return render(request, 'echoslot/addservice.html', {'form': form})

def updateAppointment_status(request, appointment_id):
    user = request.user

    if user.role != CustomUser.UserRole.SERVICE_PROVIDER:
        messages.error(request, 'You must be a service provider to update an appointment')
    try:
        provider = request.service_provider
    except ServiceProvider.DoesNotExist:
        messages.error(request, "Access denied")
        return redirect('account:register') # to be changed 
    
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id, service__provider=provider)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [status[0] for status in Appointment.STATUS_CHOICE]:
            appointment.status = new_status
            appointment.save()
            messages.success(request, f'Appointment status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status')
        
        return redirect('echoslot:dashboard')
    return render(request, 'echoslot/updatestatus.html', {'appointment': appointment})

# edit a service 
@login_required
def edit_service(request, service_id):
    service_provider = get_object_or_404(ServiceProvider, user=request.user)
    service = get_object_or_404(Service, id=service_id, provider=service_provider) # get the service or return a 404
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Updated')
            return redirect('echoslot:dashboard')
        else:
            messages.error(request, 'Fill the form correctly')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'echoslot/editservice.html', {'form':form})

@login_required
def delete_service(request, service_id):
    service_provider = get_object_or_404(ServiceProvider, user=request.user)
    service = get_object_or_404(Service, id=service_id, provider=service_provider)

    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Service deleted successfully.')
        return redirect('echoslot:dashboard')
    return render(request, 'echoslot/confirmdelete.html', {'service': service})