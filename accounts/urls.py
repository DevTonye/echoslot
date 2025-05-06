from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verifyemail'),
    path('verification-pending/', views.verification_pending, name='verification_pending'),
    path('resend-verification/', views.resend_verification_link, name='resend_verification'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete, name='password_reset_complete'),
    path('register/', views.RegisterAccount, name='register'),
    path('login/', views.LoginAccount, name='login'),
    path('logout/', views.LogoutAccount, name='logout'), 
]