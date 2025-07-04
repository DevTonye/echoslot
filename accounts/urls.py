from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verifyemail'),
    path('verification-pending/', views.verification_pending, name="verificationpending"), 
    path('resend-verification/', views.resend_verification_link, name='resend_verification'),
    path('password-reset/', views.password_reset_request, name="passwordrest"),
    path('password-reset/done/', views.password_reset_done, name='passwordreset_done'),
    path('newpassword/<uidb64>/<token>/', views.new_password_request, name="newpassword_reset"), 
    path('password-reset-complete/', views.passwordrest_complete, name='resetcomplete'),
    path('reset-password/', views.resend_passwordreset_link, name="resend_password_link"),
    path('register/', views.registeraccount, name='register'),
    path('login/', views.loginaccount, name='login'),
    path('logout/', views.logoutuser, name='logout'), 
    path('select-role/', views.selectuser_role, name='selectrole'),
    path('delete-account/', views.delete_account, name='delete_account'),
]