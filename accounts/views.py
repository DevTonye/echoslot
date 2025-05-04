from django.shortcuts import render, redirect
from .forms import RegisterForm, LoginForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.core.mail import send_mail, BadHeaderError
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator # token generator 
from django.urls import reverse
from django.conf import settings
import smtplib
import socket # for network errors 
User = get_user_model()

def send_verification_email(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    verification_link = request.build_absolute_uri(
        reverse("accounts:verifyemail", kwargs={"uidb64":uid, "token":token})
    )

    subject = "Verify your account"
    message = f"Hello {user.username},\n\nPlease verify your account by clicking the link below:\n\n{verification_link}"

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
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


# verify user's email
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
        return redirect('echoslot:index') # to be change later
    else:
        return render(request, 'account/verification_failed.html')
    
# resend verification link
def resend_verification_link(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                messages.info(request, 'Your email is already verified.')
                login(request, user)
            else:
                send_verification_email(user, request) # Generate new token and send verification email
                messages.success(request, 'A new verification email has been sent. Please check your index.')
                return redirect('accounts:verification_pending') 
        except ValidationError as e:
            messages.error(request, str(e))

    return render(request, 'account/resend_verification.html') # to be created

def verification_pending(request):
    return render(request, 'account/verification_pending.html') # to be created

# register users
def RegisterAccount(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # set until verified
            user.set_password(form.cleaned_data["password1"])
            user.save()
            try:
                send_verification_email(user, request)
                messages.success(request, "Verification email sent.")
                return render(request, 'account/verification_pending.html', {'email': user.email})
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
        
def LoginAccount(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            try:
                user = User.objects.get(email=email)
                if not user.check_password(password):
                    raise User.DoesNotExist
            except User.DoesNotExist:
                messages.error(request, "Incorrect email address or password.")
                return render(request, "account/login.html", {"form": form})

            if not user.is_active:
                messages.error(request, "Please verify your email address before logging in.")
                return redirect('accounts:verification_pending')

            user.backend = 'django.contrib.auth.backends.ModelBackend'  # required when bypassing authenticate()
            login(request, user)

            remember_me = form.cleaned_data.get("remember_me")
            if remember_me:
                request.session.set_expiry(0)  # session ends on browser close
            else:
                request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days

            messages.success(request, f"Welcome back, {user.username}")
            return redirect('echoslot:index') # will be changed 
        else:
            # form is invalid
            for field, errors in form.errors.items():
                for error in errors:
                    if field == "__all__":
                        messages.error(request, error)
                    else:
                        messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = LoginForm()

    return render(request, "account/login.html", {"form": form})


# logout users
def LogoutAccount(request):
    username = request.user.username  # Get the username before logging out
    logout(request)
    messages.success(request, f'{username} logged out')
    return redirect("echoslot:index")