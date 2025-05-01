from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verifyemail'),
    path('verification-pending/', views.verification_pending, name='verification_pending'),
    path('resend-verification/', views.resend_verification_link, name='resend_verification'),
    path('register/', views.RegisterAccount, name='register'),
    path('login/', views.LoginAccount, name='login'),
    path('logout/', views.LogoutAccount, name='logout'), 
]