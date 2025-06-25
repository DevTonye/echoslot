from django.shortcuts import render, redirect
from .forms import ClientProfileForm
from .models import ClientProfile
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import CustomUser
User = get_user_model()

@login_required(login_url="accounts:login")
def create_clientprofile(request):
    if request.user.role != CustomUser.UserRole.CLIENT:
        messages.error(request, "Access deined")
        return redirect("serviceapp:dashboard")
    # check if the user already has a profile
    if ClientProfile.objects.filter(user=request.user).exists():
        messages.error(request, "You already have a profile and cannot create another one")
        return redirect('serviceapp:find_service')
    if request.method == "POST":
        form = ClientProfileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                client_profile = form.save(commit=False)
                client_profile.user = request.user
                client_profile.save()
                messages.success(request, f"Profile created {request.user.username}")
                return redirect('serviceapp:find_service')
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
def client_dashboard(request):
    return render(request, 'client/clientdashboard.html')