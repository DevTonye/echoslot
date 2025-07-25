from django.shortcuts import render, redirect, get_object_or_404
from .forms import ClientProfileForm
from .models import ClientProfile
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import CustomUser
from django.utils import timezone
from serviceapp.models import Appointment, ServiceProvider, Service
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse

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
                return redirect('clientapp:client_dashboard')
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

    total_appointments = today_appointments_quary.count() + upcoming_appointments_query.count()

    context = {
        "requesting_client":requesting_client,
        "today_appointments": today_appointments_quary,
        "upcoming_appointments": upcoming_appointments_query,
        "past_appointments":past_appointments_query,
        "total_appointments": total_appointments,
    }
    return render(request, 'client/clientdashboard.html', context)

# view clients appointments 
@login_required(login_url="accounts:login")
def client_appointments(request):
     return render(request, "client/appointments.html")

@login_required(login_url="accounts:login")
def today_appointments(request):
    if not request.htmx:
        return render(request, "403.html", status=403)
    
    requesting_client = request.user

    today = timezone.now().date()

    # display appointments for today
    today_appointments_query = Appointment.objects.filter(
        client=requesting_client, 
        appointment_date=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('start_time')

    paginator = Paginator(today_appointments_query, 4)
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
    if not request.htmx:
        return render(request, "403.html", status=403)
    
    requesting_client = request.user

    today = timezone.now().date()

    # display upcoming appointments 
    upcoming_appointments_query = Appointment.objects.filter(
        client=requesting_client, 
        appointment_date__gt=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('appointment_date', 'start_time')

    paginator = Paginator(upcoming_appointments_query, 4)
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
    if not request.htmx:
        return render(request, "403.html", status=403)
    
    requesting_client = request.user

    today = timezone.now().date()

    past_appointments_query = Appointment.objects.filter(
        Q(client=requesting_client) & (Q(appointment_date__lt=today) | Q(appointment_date=today, status__in=['completed', 'cancelled', 'no_show']))
    ).order_by('-appointment_date', '-start_time')
    
    paginator = Paginator(past_appointments_query, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "requesting_client": requesting_client,
        "past_appointments": past_appointments_query,
        "page_obj":page_obj
    }
    return render(request, "partials/client/_past_appointments.html", context)

# view cancelled appointments
@login_required(login_url="accounts:login")
def cancelled_appointments(request):
    if not request.htmx:
        return render(request, "403.html", status=403)
    
    requesting_client = request.user  
    
    # Get appointments from today that are completed/cancelled and past appointments
    cancelled_appointments_query = Appointment.objects.filter(
         Q(client=requesting_client) & Q(status='cancelled')).order_by('-appointment_date', '-start_time')
    
    paginator = Paginator(cancelled_appointments_query, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "cancelled_appointment":cancelled_appointments_query,
        "page_obj":page_obj
    }
    return render(request, "partials/client/_cancel_appointment.html", context)

# cancel appointments
@login_required(login_url="accounts:login")
def cancel_appointment_action(request, appointment_id):
    if not request.htmx:
        return render(request, "403.html", status=403)
    
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id, client=request.user)
    if appointment.status not in['completed', 'cancelled', 'no_show']:
        appointment.status = "cancelled"
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
        return render(request, "partials/client/cancel_success.html")
    else:
        messages.warning(request, "You cannot cancel this appointment.")

# view info about the appointment 
@login_required(login_url="accounts:login")
def appointment_info(request, appointment_id):
    requesting_client = request.user
    appointment = Appointment.objects.get(appointment_id=appointment_id)
    context = {
        'appointment': appointment,
        'now': timezone.now(), 
        'requesting_client': requesting_client
    }
    return render(request, 'client/appointment_info.html', context)


@login_required(login_url="accounts:login")
def profile_settings(request):
    return render(request, "client/profile_settings.html")

# edit profile
@login_required(login_url="accounts:login")
def client_edit_profile(request):
    # Block direct non-HTMX access
    if not request.htmx:
        return render(request, "403.html", status=403)
    
    client_profile = get_object_or_404(ClientProfile, user=request.user)
    if request.method == "POST":
        form = ClientProfileForm(request.POST, request.FILES, instance=client_profile)
        if form.is_valid():
            save_profile = form.save()
            save_profile.refresh_from_db()
            messages.success(request, "Profile updated successfully.", extra_tags='profile')
            form = ClientProfileForm(instance=client_profile)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ClientProfileForm(instance=client_profile)
    return render(request, "partials/client/_editprofile.html", {"form":form})

@login_required(login_url="accounts:login")
def security_settings(request):
    if not request.htmx:
        return render(request, "403.html", status=403)
    return render(request, 'partials/client/_security_settings.html')

# search
'''
def search_providers(request):
    query = request.GET.get('q', '')
    providers = ServiceProvider.objects.all()

    if query:
        query = query.strip()
        providers = ServiceProvider.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )

        services = Service.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    return render(request, 'service/findservices.html', {
        'query':query, 
        'providers':providers,
        'services': services,
    })

'''