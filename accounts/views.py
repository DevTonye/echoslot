from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .forms import RegisterForm, LoginForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.core.mail import send_mail, BadHeaderError
from django.core.validators import validate_email
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django_ratelimit.decorators import ratelimit
from django.urls import reverse
from django.conf import settings
import smtplib
import socket # for network errors 
import time
import random
import threading
from serviceapp.models import ServiceProvider
from django.db import transaction

User = get_user_model()

# Reusable function to safely send emails with standard error handling.
def send_custom_email(subject, message, recipient_email):
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email])
    except BadHeaderError:
        raise ValidationError("There was a problem with the email header. Please try again later.")
    except smtplib.SMTPRecipientsRefused:
        raise ValidationError("This email address is not valid or refused by the email server.")
    except smtplib.SMTPDataError:
        raise ValidationError("There was an error sending your email. Please try again.")
    except smtplib.SMTPException:
        raise ValidationError("A mail server error occurred. Please try again later.")
    except socket.error:
        raise ValidationError("Network error. Please check your internet connection and try again.")
    except ImproperlyConfigured:
        raise ValidationError("Email service is currently not configured. Please contact support.")
    except Exception:
        raise ValidationError("An unexpected error occurred. Please try again later.")

def send_verification_email(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    verification_link = request.build_absolute_uri(
        reverse("accounts:verifyemail", kwargs={"uidb64":uid, "token":token})
    )

    subject = "Verify your account"
    message = f"""Hello {user.username},
    
    Thank you for registering. Please verify your email by clicking the link below:
    
    {verification_link}

    If you did not register, please ignore this email.

    """
    send_custom_email(subject, message, user.email)

# verify users email
def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        # Log the user in after verification
        login(request, user)
        messages.success(request, "Your account have beem verified.")
        return redirect("accounts:selectrole")
    else:
        return render(request, 'account/verification_failed.html')

def verification_pending(request):
    return render(request, 'account/verification_pending.html')
    
# for email verification
def resend_verification_link(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                messages.info(request, "Your email is already verified")
                login(request, user)
            else:
                send_verification_email(user, request)
                messages.success(request, 'A new verification email has been sent. Please check your index.')
                return redirect('accounts:verificationpending')
        except ValidationError as e:
            messages.error(request, str(e))
    return render(request, 'account/resend_verification.html') 

# send password reset link email
def send_password_reset_link(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    reset_link = request.build_absolute_uri(
        reverse('accounts:newpassword_reset', kwargs={"uidb64":uid, "token":token})
    )

    subject = "Password Reset"
    message = f"""Hello {user.username}
    You requested a password reset for your account. Please click the link below to reset your password:

    {reset_link}

    If you didn't request this, you can safely ignore this email.

    This link will expire in 24 hours.
"""
    send_custom_email(subject, message, user.email)

def delayed_send_email(user, request):
    """Send email in a separate thread after a random delay"""
    def _send_with_delay():
        time.sleep(random.uniform(1.0, 2.0)) # random delay between 1 - 2 seconds
        try:
            if user is not None:
                send_password_reset_link(user, request)
        except ValidationError:
            pass # Silently handle errors in background thread
    thread = threading.Thread(target=_send_with_delay)
    thread.daemon = True
    thread.start()

# handle password reset request form
@require_http_methods(["GET", "POST"])
def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                delayed_send_email(user, request)
            except User.DoesNotExist:
                delayed_send_email(None, request)
            messages.success(request, "If an account with that email exists, a password reset link has been sent.")
            return redirect("accounts:passwordreset_done")
    else:
        form = PasswordResetForm()
    return render(request, "account/password_reset_form.html", {"form":form})

@require_http_methods(["GET"])
def password_reset_done(request):
    return render(request, 'account/password_reset_done.html')

# set a new password
@require_http_methods(["GET", "POST"])
def new_password_request(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    # check if the token is vaild
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password has been reset successfully. You can now log in with your new password.")
                return redirect("accounts:login")
        else:
            form = SetPasswordForm(user)
        return render(request, "account/newpassword.html", {"form": form})
    else:
        messages.error(request, "The password reset link is invalid or has expired.")
        return render(request, "account/passwordrest_invalid.html")

@require_http_methods(["GET"])
def passwordrest_complete(request):
    messages.success(request, "Your password has been reset successfully.")
    return redirect("accounts:login")

@ratelimit(key='ip', rate='5/h', method='POST', block=True)
@ratelimit(key='post:email', rate='3/h', method='POST', block=True)
def resend_passwordreset_link(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        try:
            validate_email(email) # checks the email format
        except User.DoesNotExist:
            messages.error(request, "Please enter a valid email address")
            return render(request, "account/password_reset_form.html")
        try:
            user = User.objects.get(email=email)
            delayed_send_email(user, request)
        except User.DoesNotExist:
            delayed_send_email(None, request)

        messages.success(request, "If an account with that email exists, a password reset link has been sent.")
        return redirect("accounts:passwordreset_done")
    return render(request, "account/password_reset_form.html")

# handle rate limit execeptions
def handle_ratelimited(request, exception):
    messages.error(request, "Too many requests. Please try again later.")
    return render(request, "account/password_reset_form.html", status=429)

# register users
def registeraccount(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # until a user is verified 
            user.set_password(form.cleaned_data["password1"])
            user.save()
            try:
                send_verification_email(user, request)
                messages.success(request, "Verification email sent.")
                return render(request, "account/verification_pending.html", {"email": user.email}) 
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            # show all form error as messages
            for field, errors in form.errors.items():
                for error in errors:
                    if field == "__all__":
                        messages.error(request, error)
                    else:
                        messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = RegisterForm()
    return render(request, "account/register.html", {"form":form})

def loginaccount(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            try:
                user = User.objects.get(email=email)
                if not user.check_password(password):
                    form.add_error("password", "Incorrect password.")
                    return render(request, "account/login.html", {"form": form})
            except User.DoesNotExist:
                # This should already be caught in clean_email, so this is a fallback
                form.add_error("email", "No account found with this email.")
                return render(request, "account/login.html", {"form": form})
            
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            
            if not user.is_active:
                messages.error(request, "Please verify your email address before logging in.")
                return redirect('accounts:verificationpending')
            
            if user.role == CustomUser.UserRole.SERVICE_PROVIDER:
                if not ServiceProvider.objects.filter(user=user).exists():
                    messages.warning(request, "You must create a profile before continuing.")
                    return redirect("serviceapp:profile")

            remember_me = form.cleaned_data.get("remember_me")
            if remember_me:
                request.session.set_expiry(0)  # session ends on browser close
            else:
                request.session.set_expiry(60 * 60 * 24 * 30)
            messages.success(request, f"Welcome back, {user.username}")
            return redirect('serviceapp:dashboard')
    else:
        form = LoginForm()
    return render(request, "account/login.html", {"form":form})

# logout users
def logoutuser(request):
    username = request.user.username  # Get the username before logging out
    logout(request)
    messages.success(request, f'{username} logged out')
    return redirect("accounts:login")

@login_required(login_url='accounts:login')
def selectuser_role(request):
    # Check if user already has a role selected
    if request.user.role:
        if request.user.role == CustomUser.UserRole.SERVICE_PROVIDER:
            messages.info(request, "You have already selected your role as Service Provider.")
            return redirect("serviceapp:dashboard")
        elif request.user.role == CustomUser.UserRole.CLIENT:
            messages.info(request, "You have already selected your role as Client.")
            return redirect('clientapp:clientprofile') 
    if request.method == "POST":
        role = request.POST.get("role")
        if role in [CustomUser.UserRole.CLIENT, CustomUser.UserRole.SERVICE_PROVIDER]:
            request.user.role = role
            request.user.save()
        
            if role == CustomUser.UserRole.SERVICE_PROVIDER:
                messages.success(request, "Your role has been set to Service Provider, please create a profile")
                return redirect("serviceapp:profile")
            else:
                messages.success(request, "Your role has been set to Client. Please create a profile.")
                return redirect("clientapp:clientprofile")
        else:
            messages.error(request, "Invalid role selected.")
    return render(request, 'account/selectrole.html')

# delete account
@login_required(login_url='accounts:login')
@transaction.atomic
def delete_account(request):
    user = request.user
    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, f"Account '{username}' has been deleted.")
        return redirect("accounts:register")
    else:
        messages.error(request, "Invalid request method.")
    return render(request, 'account/delete_account.html')
            
