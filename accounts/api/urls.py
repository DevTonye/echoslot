from django.urls import path
from .views import RegisterView, LoginView, PasswordResetView, PasswordResetConfirmAPI, SendVerificationEmailView, VerifyEmailView, SelectUserRoleView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path("login/", LoginView.as_view(), name="login"),
    path("resend-verification/", SendVerificationEmailView.as_view(), name="resend_verification"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmAPI.as_view(), name='password-reset-confirm'),
    path('select-role/', SelectUserRoleView.as_view(), name='selectrole'),
]
