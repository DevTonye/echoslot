from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceProviderViewSet, ServiceViewSet, AvailabilityScheduleViewSet, AppointmentViewSet

router = DefaultRouter()
router.register(r'serviceproviders', ServiceProviderViewSet, basename='serviceprovider')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'availability', AvailabilityScheduleViewSet, basename='availabilityschedule')
router.register(r'appointments', AppointmentViewSet, basename='appointment')


urlpatterns = [
    path('', include(router.urls)),
]