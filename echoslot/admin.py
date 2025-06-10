from django.contrib import admin
from serviceapp.models import ServiceProvider, Service, AvailabilitySchedule, Appointment, Notification


admin.site.register(ServiceProvider)
admin.site.register(Service)