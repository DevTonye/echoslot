import zoneinfo
from django.utils import timezone

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user_tz = None
            # check for service provider timezone
            service_provider = getattr(request.user, "service_provider", None)
            if service_provider and getattr(service_provider, "timezone", None):
                user_tz = service_provider.timezone
                #print(f"DEBUG: User timezone being set to: {user_tz}")
            # check for client profile timezone if no provider timezone
            if not user_tz:
                client = getattr(request.user, "clientprofile", None)
                if client and getattr(client, "timezone", None):
                    user_tz = client.timezone
                    #print(f"DEBUG: User timezone being set to: {user_tz}")
            if user_tz:
                timezone.activate(zoneinfo.ZoneInfo(user_tz))
            else:
                timezone.deactivate()
        else:
            # fallback for anonymous users
            tzname = request.session.get("django_timezone")
            if tzname:
                timezone.activate(zoneinfo.ZoneInfo(tzname))
            else:
                timezone.deactivate()

        return self.get_response(request)
