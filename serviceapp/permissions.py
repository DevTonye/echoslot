from rest_framework.permissions import BasePermission
from .models import ServiceProvider

class IsServiceProvider(BasePermission):
    """
    Allows access only to authenticated users who are service providers.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            getattr(request.user, 'role', '').lower() == 'service_provider'
        )

    def has_object_permission(self, request, view, obj):
        # If the object itself is a ServiceProvider
        if isinstance(obj, ServiceProvider):
            return obj.user == request.user

        # If the object has a related provider (e.g. Service)
        if hasattr(obj, 'provider'):
            return obj.provider.user == request.user

        return False
