from django.shortcuts import render, redirect, get_object_or_404
from .models import ServiceProvider, Service, Appointment, Notification, AvailabilitySchedule
from .forms import ServiceProviderForm, ServiceForm, AppointmentForm, AvailabilityScheduleForm
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
import datetime
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from accounts.models import CustomUser
from django.db.models import Q
import random
from celery import shared_task
from django.db import IntegrityError
from django.db import transaction


# service provider views
User = get_user_model()

def service_provider_required(view_func):
    @wraps(view_func)
    def wrapper(request, *agrs, **kwargs):
        user = request.user
        if user.role != CustomUser.UserRole.SERVICE_PROVIDER:
            messages.error(request, "You have no access to this page")
            return redirect("accounts:selectrole")
        try:
            user.service_provider
        except ServiceProvider.DoesNotExist:
            messages.error(request, 'Please create a profile')
            return redirect('serviceapp:profile')
        return view_func(request, *agrs, **kwargs)
    return wrapper

# service provider profile
@login_required(login_url='accounts:login')
def serviceprovider_profile(request):
    if request.method == "POST":
        #print("POST data:", request.POST)
        form = ServiceProviderForm(request.POST)
        #print(form.errors)
        if form.is_valid():
            provider = form.save(commit=False)
            provider.user = request.user
            provider.save()
            messages.success(request, "Your service account has been created!")
            return redirect("serviceapp:set_availability")
    else:
        form = ServiceProviderForm()
    return render(request, "service/profile.html", {"form": form})

# service provider dashboard
@login_required(login_url='accounts:login')
@service_provider_required
def service_dashboard(request):
    provider = request.user.service_provider
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

    service = Service.objects.filter(provider=provider)[:3]

    context = {
        'provider':provider,
        'today_appointments':today_appointments,
        'upcoming_appointments':upcoming_appointments,
        'services':service
    }

    return render(request, 'service/dashboard.html', context)

# add services views 
@service_provider_required
def add_service(request): 
    provider = request.user.service_provider
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            try:
                service = form.save(commit=False)
                service.provider = provider
                service.save()
                messages.success(request, "Service added successfully.")
                return redirect("serviceapp:service")
            except IntegrityError: 
                messages.error(request, 'You already have a service. You can only have one service per account.')
                return redirect("serviceapp:service")
    else:
        form = ServiceForm()
    return render(request, "service/addservice.html", {"form": form})

# edit services
@login_required(login_url='accounts:login')
def edit_service(request, service_id):
    service_provider = get_object_or_404(ServiceProvider, user=request.user)
    service = get_object_or_404(Service, service_id=service_id, provider=service_provider)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service updated')
            return redirect('serviceapp:service')
        else:
            messages.error(request, "Fill the form correctly")
    else:
        form = ServiceForm(instance=service)
    return render(request, 'service/editservice.html', {'form': form})

# delete a sevice
@login_required(login_url='accounts:login')
def delete_service(request, service_id):
    service_provider = get_object_or_404(ServiceProvider, user=request.user)
    service = get_object_or_404(Service, service_id=service_id, provider=service_provider)
    if request.method == "POST":
        service.delete()
        messages.success(request, "Service deleted.")
        return redirect('serviceapp:service')
    return render(request, 'service/confirmdelete.html', {'service': service})

# make a request to get all, today, upcoming and past appointments
@service_provider_required
def appointments(request):
    provider = request.user.service_provider
    return render(request, "service/appointments.html", {"provider":provider})

def today_appointments(request):
    provider = request.user.service_provider
    today = timezone.now().date()
    
    today_appointments = Appointment.objects.filter(
        service__provider=provider,
        appointment_date=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('start_time')

    service = Service.objects.filter(provider=provider)

    context = {
        'provider':provider,
        'today_appointments':today_appointments,
        'services':service
    }
    return render(request, "partials/today.html", context)

# display upcoming appointments for a service provider
def upcoming_appointments(request):
    provider = request.user.service_provider
    today = timezone.now().date()
    
    upcoming_appointments = Appointment.objects.filter(
        service__provider=provider,
        appointment_date__gt=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('appointment_date', 'start_time')

    service = Service.objects.filter(provider=provider)

    context = {
        'provider':provider,
        'upcoming_appointments':upcoming_appointments,
        'services':service
    }
    return render(request, "partials/upcoming.html", context)

def past_appointments(request):
    provider = request.user.service_provider    
    today = timezone.now().date()
    
    past_appointments = Appointment.objects.filter(
        service__provider=provider,
        appointment_date__lt=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('start_time')

    # get appointments from today that are completed/cancelled
    past_appointments = Appointment.objects.filter(
    Q(service__provider=provider) & 
        (Q(appointment_date__lt=today) | 
        Q(appointment_date=today, status__in=['completed', 'cancelled', 'no_show']))
    ).order_by('-appointment_date', '-start_time')[:50]

    service = Service.objects.filter(provider=provider)

    context = {
        'provider':provider,
        'past_appointments':past_appointments,
        'services':service
    }
    return render(request, "partials/past.html", context)

# view all services
def services_all(request):
    services = Service.objects.all()
    context = {"services": services}
    return render(request, 'service/allservice.html', context)

# allow service providers to set and view their availability
@login_required(login_url="accounts:login")
@service_provider_required
def myavailability(request):
    availability_success = False
    if request.method == "POST":
        form = AvailabilityScheduleForm(request.POST, service_provider=request.user.service_provider)
        if form.is_valid():
            form.save()
            availability_success = True
            return redirect("serviceapp:my_availability")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AvailabilityScheduleForm(service_provider=request.user.service_provider)
    # display all availability by a service proivder
    all_availability = AvailabilitySchedule.objects.filter(
        service_provider = request.user.service_provider
    ).order_by('day_of_week', 'start_time')
    return render(request, 'service/myavailability.html', { 'form': form, 'availabilities': all_availability, 'availability_success': availability_success,})

# edit availability function 
@login_required(login_url="accounts:login")
@service_provider_required
def edit_availability(request, pk):
    availability = get_object_or_404(AvailabilitySchedule, pk=pk, service_provider=request.user.service_provider)
    if request.method == "POST":
        form = AvailabilityScheduleForm(request.POST, instance=availability, service_provider=request.user.service_provider)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Availability updated successfully.")
                return redirect("serviceapp:my_availability")
            except IntegrityError:
                form.add_error(None, "This availability would create a duplicate day entry. Please choose another day.")
    else:
        form = AvailabilityScheduleForm(instance=availability, service_provider=request.user.service_provider)
    return render(request, "service/editavailability.html", {'form':form, 'availability':availability})
    
@login_required(login_url="accounts:login")
@service_provider_required
def delete_availability(request, pk):
    availability = get_object_or_404(AvailabilitySchedule, pk=pk, service_provider=request.user.service_provider)

    if request.method == 'POST':
        availability.delete()
        messages.success(request, "Availability deleted successfully.")
        return redirect('serviceapp:my_availability')
    return render(request, 'service/delete_availability_confirm.html', {'availability': availability})

# service provider finder 
@login_required(login_url="accounts:login")
def find_services(request):
    service_provider = list(ServiceProvider.objects.all())
    random_providers = random.sample(service_provider, min(len(service_provider), 6)) if service_provider else []
    return render(request, "service/findservices.html", {'providers': random_providers})

# book appointments
@login_required(login_url="accounts:login")
def book_appointments(request, provider_id):
    provider = get_object_or_404(ServiceProvider, pk=provider_id)
    services = Service.objects.filter(provider=provider)
    availability_schedule = AvailabilitySchedule.objects.filter(service_provider=provider).order_by('day_of_week', 'start_time')
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, provider_id=provider_id)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = request.user
            appointment.end_time = form.cleaned_data['end_time']
            appointment.status = 'scheduled'

            with transaction.atomic():
                appointment.save()

                appt_datetime = timezone.make_aware(
                    datetime.datetime.combine(appointment.appointment_date, appointment.start_time)
                )

                # Email reminder (1 day before)
                reminder_day = appt_datetime - datetime.timedelta(days=1)
                if reminder_day > timezone.now():
                    Notification.objects.create(
                        appointment=appointment,
                        notification_type='email',
                        scheduled_for=reminder_day,
                        message=f"Reminder: You have an appointment for {appointment.service.name} tomorrow at {appointment.start_time}."
                    )

                # SMS reminder (1 hour before)
                reminder_hour = appt_datetime - datetime.timedelta(hours=1)
                if reminder_hour > timezone.now():
                    Notification.objects.create(
                        appointment=appointment,
                        notification_type='sms',
                        scheduled_for=reminder_hour,
                        message=f"Reminder: Your appointment for {appointment.service.name} is in 1 hour at {appointment.start_time}."
                    )

            messages.success(request, 'Appointment booked successfully!')
            return redirect('serviceapp:appointment_success', appointment_id=appointment.appointment_id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AppointmentForm(provider_id=provider_id)

    return render(request, 'service/bookappointment.html', {
        'provider': provider,
        'form': form,
        'services': services,
        'availability_schedule': availability_schedule
    })

@login_required(login_url="accounts:login")
def appointment_success(request, appointment_id):
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id, client=request.user)
    return render(request, 'service/appointmentsuccess.html', {'appointment': appointment})


