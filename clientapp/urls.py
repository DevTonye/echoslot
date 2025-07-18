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
]