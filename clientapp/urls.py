from django.urls import path
from . import views

app_name = 'clientapp'

urlpatterns = [
    path('profile/', views.create_clientprofile, name='clientprofile'),
    path('your-dashboard/', views.client_appointment_dashboard, name='client_dashboard'),
    path('', views.client_appointments, name='client_appointment'), 
    path('today-appointments/', views.today_appointments, name='today_appointments'), 
    path('upcoming-appointments/', views.upcoming_appointments, name='upcoming_appointments'),
    path('past-appointments/', views.past_appointments, name='past_appointments'),
    path('cancel/', views.cancelled_appointments, name='cancel_appointment'),
    path('appointment-cancelled/<uuid:appointment_id>/', views.cancel_appointment_action, name='cancel_appointment_action'),
    path('settings/', views.profile_settings, name='profile_settings'),
    path('edit-profile/', views.client_edit_profile, name="edit_profile"),
    path('security/', views.security_settings, name="security"),
]
