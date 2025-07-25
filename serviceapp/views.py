from django.shortcuts import render, redirect, get_object_or_404
from .models import ServiceProvider, Service, Appointment, Notification, AvailabilitySchedule
from .forms import ServiceProviderForm, ServiceForm, AppointmentForm, AvailabilityScheduleForm, AppointmentStatusForm
from django.contrib import messages
from django.utils import timezone
import datetime
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from accounts.models import CustomUser
from django.db.models import Q
import random
from django.http import HttpResponse
from django.db import IntegrityError
from django.db import transaction
from datetime import datetime, timedelta, time
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.core.paginator import Paginator

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
        form = ServiceProviderForm(request.POST, request.FILES)
        #print(form.errors)
        if form.is_valid():
            provider = form.save(commit=False)
            provider.user = request.user
            provider.save()
            messages.success(request, "Your service account has been created!")
            return redirect("serviceapp:dashboard")
    else:
        form = ServiceProviderForm()
    return render(request, "service/profile.html", {"form": form})

# service provider dashboard
@login_required(login_url='accounts:login')
@service_provider_required
def service_dashboard(request):
    provider = request.user.service_provider
    today = timezone.now().date()

    # display user appointments 
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

@login_required(login_url="accounts:login")
def settings(request):
    provider = request.user.service_provider
    return render(request, "service/settings.html", {"provider":provider})

@login_required(login_url="accounts:login")
@service_provider_required
def settings_profile(request):
    if not request.htmx:
        return render(request, "403.html", status=403) 
    
    sp_profile = get_object_or_404(ServiceProvider, user=request.user)
    if request.method == "POST":
        form = ServiceProviderForm(request.POST, request.FILES, instance=sp_profile)
        if form.is_valid():
            saved_profile = form.save()

            saved_profile.refresh_from_db()
            messages.success(request, 'Profile updated successfully.', extra_tags='profile')
            form = ServiceProviderForm(instance=sp_profile)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ServiceProviderForm(instance=sp_profile)
    return render(request, 'partials/settingsprofile.html', {'form': form})
    
@login_required(login_url="accounts:login")
@service_provider_required
def security_settings(request):
    if not request.htmx:
        return render(request, "403.html", status=403) 
    return render(request, 'partials/security_settings.html')

@login_required(login_url="accounts:login")
def account_security(request):
    if not request.htmx:
        return render(request, "403.html", status=403) 
    return render(request, 'partials/account_settings.html')

# add services views 
@login_required(login_url="accounts:login")
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

# view all services and recent appointments
def services_all(request):
    provider = request.user.service_provider
    services = Service.objects.all()
    recent_appointemnt = Appointment.objects.filter(service__provider=provider).order_by('-appointment_date')[:5]
    context = {"services": services, "provider":provider, 'recent_appointment':recent_appointemnt}
    return render(request, 'service/allservice.html', context)


# make a request to get all, today, upcoming and past appointments 
@service_provider_required
def appointments(request):
    provider = request.user.service_provider
    return render(request, "service/appointments.html", {"provider":provider})

def today_appointments(request):
    if not request.htmx:
        return render(request, "403.html", status=403)
        
    provider = request.user.service_provider
    today = timezone.now().date()
    
    today_appointments_quary = Appointment.objects.filter(
        service__provider=provider,
        appointment_date=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('start_time')

    paginator = Paginator(today_appointments_quary, 5) # for testing
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    service = Service.objects.filter(provider=provider)

    context = {
        'provider':provider,
        'today_appointments':today_appointments_quary,
        'services':service,
        'page_obj': page_obj
    }
    return render(request, "partials/today.html", context)

# display upcoming appointments for a service provider
def upcoming_appointments(request):
    if not request.htmx:
        return render(request, "403.html", status=403)
    
    provider = request.user.service_provider
    today = timezone.now().date()
    
    upcoming_appointments_query = Appointment.objects.filter(
        service__provider=provider,
        appointment_date__gt=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('appointment_date', 'start_time')

    paginator = Paginator(upcoming_appointments_query, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    service = Service.objects.filter(provider=provider)

    context = {
        'provider':provider,
        'upcoming_appointments':upcoming_appointments_query,
        'services':service, 
        'page_obj': page_obj
    }
    return render(request, "partials/upcoming.html", context)

def past_appointments(request):
    if not request.htmx:
        return render(request, "403.html", status=403)
    
    provider = request.user.service_provider    
    today = timezone.now().date()
    
    # Get appointments from today that are completed/cancelled and past appointments
    past_appointments_query = Appointment.objects.filter(
        Q(service__provider=provider) & 
        (Q(appointment_date__lt=today) | Q(status='cancelled') |
         Q(appointment_date=today, status__in=['completed', 'cancelled', 'no_show']))
    ).order_by('-appointment_date', '-start_time')
    
    
    # Set up pagination
    paginator = Paginator(past_appointments_query, 5)   
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    service = Service.objects.filter(provider=provider)
    
    context = {
        'provider': provider,
        'past_appointments': past_appointments_query,  # For the count
        'services': service,
        'page_obj': page_obj
    }
    
    return render(request, "partials/past.html", context)


# cancel

# allow service providers to set and view their availability
@login_required(login_url="accounts:login")
@service_provider_required
def myavailability(request):
    provider = request.user.service_provider
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
    return render(request, 'service/myavailability.html', { 'form': form, 'availabilities': all_availability, 'availability_success': availability_success, 'provider':provider})

# edit availability function 
@login_required(login_url="accounts:login")
@service_provider_required
def edit_availability(request, pk):
    provider = request.user.service_provider
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
    return render(request, "service/editavailability.html", {'form':form, 'availability':availability, 'provider':provider})
    
@login_required(login_url="accounts:login")
@service_provider_required
def delete_availability(request, pk):
    availability = get_object_or_404(AvailabilitySchedule, pk=pk, service_provider=request.user.service_provider)

    if request.method == 'POST':
        availability.delete()
        messages.success(request, "Availability deleted successfully.")
        return redirect('serviceapp:my_availability')
    return render(request, 'service/delete_availability_confirm.html', {'availability': availability})

# view all service provider 
@login_required(login_url="accounts:login")
def find_services(request):
    query = request.GET.get('q', '').strip()
    providers = []

    if query:
        terms = query.replace('.', ' ').split()

        filters = Q()
        for term in terms:
            filters |= (
                Q(first_name__icontains=term) |
                Q(last_name__icontains=term) |
                Q(service__name__icontains=term) |
                Q(service__description__icontains=term)
            )

        providers = ServiceProvider.objects.filter(filters).distinct()
    else:
        # Default: show random 6 providers
        all_providers = list(ServiceProvider.objects.all())
        providers = random.sample(all_providers, min(len(all_providers), 6)) if all_providers else []

    return render(request, "service/findservices.html", {
        'query': query,
        'providers': providers
    })

@login_required(login_url="accounts:login")
def book_appointments(request, provider_id):
    provider = get_object_or_404(ServiceProvider, pk=provider_id)
    services = Service.objects.filter(provider=provider)
    availability_schedule = AvailabilitySchedule.objects.filter(
        service_provider=provider
    ).order_by('day_of_week', 'start_time')
    
    # Initialize available_slots and service
    service_id = request.GET.get('service')
    service = None

    if service_id:
        try:
            service = Service.objects.get(pk=service_id, provider=provider)
        except Service.DoesNotExist:
            service = None

    # Fallback to the first service
    if not service:
        service = services.first()

    available_slots = {}
    if service:
        available_slots = get_available_time_slots(provider, service, days_ahead=30)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, provider_id=provider_id, available_slots=available_slots)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = request.user
            appointment.end_time = form.cleaned_data['end_time']
            appointment.status = 'scheduled'

            with transaction.atomic():
                appointment.save()

                appt_datetime = timezone.make_aware(
                    datetime.combine(appointment.appointment_date, appointment.start_time)
                )

                # Email reminder (1 day before)
                reminder_day = appt_datetime - timedelta(days=1)
                if reminder_day > timezone.now():
                    Notification.objects.create(
                        appointment=appointment,
                        notification_type='email',
                        scheduled_for=reminder_day,
                        message=f"Reminder: You have an appointment for {appointment.service.name} tomorrow at {appointment.start_time}."
                    )

                # SMS reminder (1 hour before)
                reminder_hour = appt_datetime - timedelta(hours=1)
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
            print("Form errors:", form.errors)
            messages.error(request, "Please correct the errors below.")
    else:
        form = AppointmentForm(provider_id=provider_id, available_slots=available_slots)

    return render(request, 'service/bookappointment.html', {
        'provider': provider,
        'form': form,
        'services': services,
        'availability_schedule': availability_schedule,
        'available_slots': available_slots,
        'selected_date': request.POST.get('appointment_date') or timezone.now().date()
    })

# generate available time slot for clients base on a service provider availability schedule
def get_available_time_slots(provider, service, days_ahead=30):
    available_slots = {}
    now = timezone.localtime()  # current aware datetime in active timezone
    today = now.date()
    slot_duration = service.duration  # minutes

    # Provider’s availability
    availability_schedule = AvailabilitySchedule.objects.filter(
        service_provider=provider
    ).order_by('day_of_week', 'start_time')

    # Existing booked slots
    existing_appointments = Appointment.objects.filter(
        service__provider=provider,
        appointment_date__gte=today,
        appointment_date__lte=today + timedelta(days=days_ahead),
        status__in=['scheduled', 'confirmed']
    ).values_list('appointment_date', 'start_time', 'end_time')

    booked_slots = {}
    for apt_date, start_time, end_time in existing_appointments:
        booked_slots.setdefault(apt_date, []).append((start_time, end_time))

    # Generate slots for each day
    for i in range(days_ahead):
        current_date = today + timedelta(days=i)
        day_availability = availability_schedule.filter(day_of_week=current_date.weekday())
        if not day_availability:
            continue

        date_slots = []

        for schedule in day_availability:
            current_time = datetime.combine(current_date, schedule.start_time)
            end_time = datetime.combine(current_date, schedule.end_time)

            while current_time + timedelta(minutes=slot_duration) <= end_time:
                slot_start = current_time.time()
                slot_end = (current_time + timedelta(minutes=slot_duration)).time()

                # Full aware datetime for this slot
                slot_datetime = timezone.make_aware(datetime.combine(current_date, slot_start))
                
                # Skip if slot is in the past
                if slot_datetime <= now:
                    current_time += timedelta(minutes=slot_duration)
                    continue

                # Check if slot overlaps with existing appointment
                is_available = True
                if current_date in booked_slots:
                    for booked_start, booked_end in booked_slots[current_date]:
                        if slot_start < booked_end and slot_end > booked_start:
                            is_available = False
                            break

                if is_available:
                    date_slots.append({
                        'time': slot_start,
                        'display': slot_start.strftime('%I:%M %p'),
                        'available': True
                    })

                current_time += timedelta(minutes=slot_duration)

        if date_slots:
            available_slots[current_date] = date_slots

    return available_slots
@login_required(login_url="accounts:login")
def load_slots(request, provider_id):
    if not request.htmx:
        return render(request, "403.html", status=403)
    
    provider = get_object_or_404(ServiceProvider, id=provider_id)
    service_id = request.GET.get("service")
    
    if service_id:
        try:
            service = Service.objects.get(id=service_id, provider=provider)
            available_slots = get_available_time_slots(provider, service)
        except Service.DoesNotExist:
            available_slots = {}
    else:
        available_slots = {}

    return render(request, "service/partials/slot_options.html", {
        "available_slots": available_slots
    })

@login_required(login_url="accounts:login")
def appointment_success(request, appointment_id):
    provider = get_object_or_404(ServiceProvider)
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id, client=request.user)
    return render(request, 'service/appointmentsuccess.html', {'appointment': appointment, 'provider':provider})

# get all appointment status
def status_form(request, appointment_id):
    if not request.htmx:
        return render(request, "403.html", status=403)
    
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    form = AppointmentStatusForm(instance=appointment)
    return render(request, 'partials/status_form.html', {'form': form, 'appointment': appointment})

# update the status
def update_status(request, appointment_id):
    if not request.htmx:
        return render(request, "403.html", status=403)
    appointment = Appointment.objects.get(appointment_id=appointment_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        appointment.status = new_status
        appointment.save()
        html = render_to_string('partials/status_td.html', {'appointment': appointment})
        return HttpResponse(html)

# view client appointment details
def appointment_details(request, appointment_id):
    provider = request.user.service_provider
    appointment = Appointment.objects.get(appointment_id=appointment_id)
    context = {
        'appointment': appointment,
        'now': timezone.now(),  # Useful for showing current datetime in template
        'provider': provider
    }
    return render(request, 'service/appointment_details.html', context)