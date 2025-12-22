from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class ServiceProviderThrottle(UserRateThrottle):
    scope = "service_provider"

class ServiceThrottle(UserRateThrottle):
    scope = "service"

class AppointmentThrottle(UserRateThrottle):
    scope = 'appointments'

class AppointmentCreateThrottle(UserRateThrottle):
    scope = 'appointment_create'