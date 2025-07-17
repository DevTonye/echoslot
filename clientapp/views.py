from django.shortcuts import render, redirect
from .forms import ClientProfileForm
from .models import ClientProfile
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import CustomUser
from django.utils import timezone
from serviceapp.models import Appointment
from django.core.paginator import Paginator
from django.db.models import Q

User = get_user_model()

@login_required(login_url="accounts:login")
def create_clientprofile(request):
    if request.user.role != CustomUser.UserRole.CLIENT:
        messages.error(request, "Access deined")
        return redirect("serviceapp:dashboard")
    # check if the user already has a profile
    if ClientProfile.objects.filter(user=request.user).exists():
        messages.error(request, "You already have a profile and cannot create another one")
        return redirect('serviceapp:find_serviceproviders')
    if request.method == "POST":
        form = ClientProfileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                client_profile = form.save(commit=False)
                client_profile.user = request.user
                client_profile.save()
                messages.success(request, f"Profile created {request.user.username}")
                return redirect('serviceapp:client_dashboard')
            except Exception as e:
                messages.error(request, f"An error occured: {e}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ClientProfileForm()
    return render(request, 'client/clientprofile.html', {"form": form})

@login_required(login_url="accounts:login")
def client_appointment_dashboard(request):
    requesting_client = request.user
    today = timezone.now().date()

    # display appointments for today
    today_appointments_quary = Appointment.objects.filter(
        client=requesting_client, 
        appointment_date=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('start_time')

    upcoming_appointments_query = Appointment.objects.filter(
        client=requesting_client, 
        appointment_date__gt=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('appointment_date', 'start_time')

    past_appointments_query = Appointment.objects.filter(
        Q(client=requesting_client) & (Q(appointment_date__lt=today) | Q(appointment_date=today, status__in=['completed', 'cancelled', 'no_show']))
    ).order_by('-appointment_date', '-start_time')

    context = {
        "requesting_client":requesting_client,
        "today_appointments": today_appointments_quary,
        "upcoming_appointments": upcoming_appointments_query,
        "past_appointments":past_appointments_query
    }
    return render(request, 'client/clientdashboard.html', context)

# view clients appointments 
@login_required(login_url="accounts:login")
def client_appointments(request):
     requesting_client = request.user
     return render(request, "client/appointments.html", {"requesting_client":requesting_client})

@login_required(login_url="accounts:login")
def today_appointments(request):
    requesting_client = request.user

    today = timezone.now().date()

    # display appointments for today
    today_appointments_query = Appointment.objects.filter(
        client=requesting_client, 
        appointment_date=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('start_time')

    paginator = Paginator(today_appointments_query, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "requesting_client": requesting_client,
        "today_appointments": today_appointments_query,
        "page_obj":page_obj
    }
    return render(request, "partials/client/_today_appointments.html", context)

@login_required(login_url="accounts:login")
def upcoming_appointments(request):
    requesting_client = request.user

    today = timezone.now().date()

    # display upcoming appointments 
    upcoming_appointments_query = Appointment.objects.filter(
        client=requesting_client, 
        appointment_date__gt=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('appointment_date', 'start_time')

    paginator = Paginator(upcoming_appointments_query, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "requesting_client": requesting_client,
        "upcoming_appointments": upcoming_appointments_query,
        "page_obj":page_obj
    }
    return render(request, "partials/client/_upcoming_appointments.html", context)

@login_required(login_url="accounts:login")
def past_appointments(request):
    requesting_client = request.user

    today = timezone.now().date()

    past_appointments_query = Appointment.objects.filter(
        Q(client=requesting_client) & (Q(appointment_date__lt=today) | Q(appointment_date=today, status__in=['completed', 'cancelled', 'no_show']))
    ).order_by('-appointment_date', '-start_time')
    
    paginator = Paginator(past_appointments_query, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "requesting_client": requesting_client,
        "past_appointments": past_appointments_query,
        "page_obj":page_obj
    }
    return render(request, "partials/client/_past_appointments.html", context)