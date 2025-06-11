from django.shortcuts import render, redirect, get_object_or_404
from .models import ServiceProvider, Service, Appointment
from .forms import ServiceProviderForm, ServiceForm
from django.contrib import messages
from django.utils import timezone
import datetime
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from accounts.models import CustomUser
from django.db.models import Q

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
            messages.error(request, 'You need to register')
            return redirect('accounts:register')
        return view_func(request, *agrs, **kwargs)
    return wrapper

# service provider profile
@login_required(login_url='accounts:login')
def serviceprovider_profile(request):
    if request.user.role != CustomUser.UserRole.SERVICE_PROVIDER:
        messages.error(request, "You have to sign in as a service provider")
        return redirect('echoslot:index')
    if request.method == "POST":
        #print("POST data:", request.POST)
        form = ServiceProviderForm(request.POST)
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
            service = form.save(commit=False)
            service.provider = provider
            service.save()
            messages.success(request, "Service added successfully.")
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

@service_provider_required
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
@service_provider_required
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

@service_provider_required
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