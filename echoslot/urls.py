from django.urls import path
from . import views

app_name = 'echoslot'

urlpatterns = [
    path('', views.index, name='index'), 
    path('creatprofile/', views.complete_provider_profile, name='completeprofile'),
    path('<int:provider_id>/', views.book_appointment, name='book_appointment'), #book appointment
    path('appointments/success/<uuid:appointment_id>/', views.appointment_success, name='appointment_success'), # appointmemt status url
    path('my-appointments/', views.view_appointments, name='view_appointments'), #let clients view appointments
    path('cancel/<uuid:appointment_id>/', views.cancel_appointment, name='cancel_appointment'), # cancel appt
    path('provider/dashboard/', views.sp_dashboard, name='dashboard'),
    path('provider/add-service/', views.add_service, name='add_service'),
    path('update-status/<uuid:appointment_id>/', views.updateAppointment_status, name='updatestatus'), # update appt status
    path('editservice/<int:service_id>/', views.edit_service, name='editservice'),
    path('delete/<int:service_id>/', views.delete_service, name='deleteservice'),
]