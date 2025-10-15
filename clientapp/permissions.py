from rest_framework.permissions import BasePermission
from .models import ClientProfile

class IsClient(BasePermission):
    #Allows access only to authenticated users with the 'client' role.

    def has_permission(self, request, view):
        # Ensure user is logged in and role is client
        return (
            request.user.is_authenticated
            and getattr(request.user, 'role', '').lower() == 'client'
        )

    def has_object_permission(self, request, view, obj):
        # If object is a ClientProfile, only the owner can access it
        if isinstance(obj, ClientProfile):
            return obj.user == request.user

        # If object has a 'user' attribute (e.g. appointments, reviews)
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # If object has a 'client' attribute (for models linked to clients)
        if hasattr(obj, 'client'):
            return obj.client == request.user

        return False
