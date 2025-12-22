from django.urls import path
from . import views

app_name = "serviceapp"

urlpatterns = [
    path("profile/", views.serviceprovider_profile, name="profile"),
    path("dashboard/", views.service_dashboard, name='dashboard'),
    path('settings/', views.provider_setting, name="settings"),
    path('settings-profile/', views.settings_profile, name="settings-profile"),
    path('security-settings/', views.security_settings, name="security-settings"),
    path('settings-account', views.account_security, name="account-settings"),
    path('add-service/', views.add_service, name='addservice'),
    path('editservice/<uuid:service_id>/', views.edit_service, name='editservice'),
    path('delete/<uuid:service_id>/', views.delete_service, name='deleteservice'),
    path('se/', views.services_all, name='service'),
    path('', views.appointments, name="appointment"),
    path('today-appointments/', views.today_appointments, name="today_appointments"),
    path('upcoming-appointments/', views.upcoming_appointments, name="upcoming_appointments"),
    path('past-appointments/', views.past_appointments, name='past_appointments'),
    path('service-providers/', views.find_services, name='find_serviceproviders'),
    path('my-availability/', views.myavailability, name='my_availability'),
    path('book/<int:provider_id>/', views.book_appointments, name='book_appointment'),
    path('appointments/success/<uuid:appointment_id>/', views.appointment_success, name='appointment_success'),
    path('availability-edit/<int:pk>/', views.edit_availability, name='editavailability'),
    path('delete-availability/<int:pk>/', views.delete_availability, name='deleteavailability'),
    path('status-form/<uuid:appointment_id>/', views.status_form, name='status_form'),
    path('appointment/<uuid:appointment_id>/status-modal/', views.status_modal, name='status_modal'),
    path('appointment/<uuid:appointment_id>/status-badge/', views.status_badge, name='status_badge'),
    path('update-status/<uuid:appointment_id>/', views.update_status, name='update_status'),
    path('appointment-details/<uuid:appointment_id>/', views.appointment_details, name='appointment_details'),

    path('checkin-modal/<uuid:appointment_id>/', views.checkin_modal, name='checkin_modal'),
    
]