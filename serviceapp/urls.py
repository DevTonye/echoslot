from django.urls import path
from . import views

app_name = "serviceapp"

urlpatterns = [
    path("profile/", views.serviceprovider_profile, name="profile"),
    path("dashboard/", views.service_dashboard, name='dashboard'),
    path('add-service/', views.add_service, name='addservice'),
    path('editservice/<uuid:service_id>/', views.edit_service, name='editservice'),
    path('delete/<uuid:service_id>/', views.delete_service, name='deleteservice'),
    path('se/', views.services_all, name='service'),
    path('', views.appointments, name="appointment"),
    path('today-appointments/', views.today_appointments, name="today_appointments"),
    path('upcoming-appointments/', views.upcoming_appointments, name="upcoming_appointments"),
    path('past-appointments/', views.past_appointments, name='past_appointments'),
    path('service-providers/', views.find_services, name='find_service'),
    path('book/<int:provider_id>/', views.book_appointments, name='book_appointment'),
    path('appointments/success/<uuid:appointment_id>/', views.appointment_success, name='appointment_success'),
]