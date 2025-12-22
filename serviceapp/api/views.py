from django.shortcuts import render
from ..serializers import ServiceProviderSerializer, ServicesSerializer, AvailabilityScheduleSerializer, AppointmentSerializer
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from ..models import ServiceProvider, Service, AvailabilitySchedule, Appointment
from ..throttle import ServiceProviderThrottle, ServiceThrottle, AppointmentCreateThrottle, AppointmentThrottle
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from ..permissions import IsServiceProvider
from ..utils import get_available_time_slots
from datetime import datetime, timedelta, date
from django.db import transaction
from django.urls import reverse
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import action
from rest_framework import filters
from .pagination import CustomPagination
from drf_spectacular.utils import extend_schema

User = get_user_model()

@extend_schema(tags=['ServiceProvider'])
class ServiceProviderViewSet(viewsets.ModelViewSet):
    queryset = ServiceProvider.objects.all()
    serializer_class = ServiceProviderSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'bio', 'address']
    ordering_fields = ['first_name', 'last_name']

    def get_permissions(self):
        """
        Allow anyone to list/retrieve providers (for searching)
        Only authenticated service providers can create/update/delete
        """
        if self.action in ['list', 'retrieve', 'get_availability']:
            return [AllowAny()]
        return [IsAuthenticated(), IsServiceProvider()]

    def get_throttles(self):
        if self.action in ['list', 'retrieve', 'get_availability']:
            return [AnonRateThrottle()]
        return [ServiceProviderThrottle()]
    
    def get_queryset(self):
        queryset = ServiceProvider.objects.all()
        
        # If provider is managing their own profile
        if self.action not in ['list', 'retrieve', 'get_availability']:
            return queryset.filter(user=self.request.user)
        
        # For public listing/search - filter by query params
        service_name = self.request.query_params.get('name', None)
        location = self.request.query_params.get('location', None)
        
        if service_name:
            queryset = queryset.filter(services__name__icontains=service_name)
        
        if location:
            queryset = queryset.filter(address__icontains=location)
        
        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'], url_path='availability', permission_classes=[AllowAny])
    def get_availability(self, request, pk=None):
        """
        Returns the available time slots for a specific provider and optional service.
        Example: /api/providers/<provider_id>/availability/?service=<service_id>
        """
        provider = self.get_object()
        service_id = request.query_params.get('service')

        if not service_id:
            return Response({'error': 'Please provide a service ID as a query parameter.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service = Service.objects.get(pk=service_id, provider=provider)
        except Service.DoesNotExist:
            return Response({'error': 'Service not found for this provider.'}, status=status.HTTP_404_NOT_FOUND)

        # Get available slots 
        available_slots = get_available_time_slots(provider, service, days_ahead=30)

        return Response({
            'provider': provider.id,
            'service': service.id,
            'available_slots': available_slots
        })
    
@extend_schema(tags=['Service'])
class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServicesSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'provider__first_name', 'provider__last_name']
    ordering_fields = ['name', 'price', 'duration']

    def get_permissions(self):
        """
        Allow anyone to list/retrieve services (for searching)
        Only authenticated service providers can create/update/delete
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsServiceProvider()]

    def get_throttles(self):
        if self.action in ['list', 'retrieve']:
            return [AnonRateThrottle()]
        return [ServiceThrottle()]
    
    def get_queryset(self):
        queryset = Service.objects.all()
        
        # If provider is managing their own services
        if self.action not in ['list', 'retrieve']:
            return queryset.filter(provider__user=self.request.user)
        
        # For public listing - filter by query params
        provider_id = self.request.query_params.get('provider', None)
        price = self.request.query_params.get('price', None)
        duration = self.request.query_params.get('duration', None)
        
        if provider_id:
            queryset = queryset.filter(provider__id=provider_id)
        
        if price:
            queryset = queryset.filter(price__lte=price)
        
        if price:
            queryset = queryset.filter(duration__lte=price)
        
        return queryset

    def perform_create(self, serializer):
        provider = ServiceProvider.objects.get(user=self.request.user)
        serializer.save(provider=provider)

@extend_schema(tags=['Availability'])
class AvailabilityScheduleViewSet(viewsets.ModelViewSet):
    queryset = AvailabilitySchedule.objects.all()
    serializer_class = AvailabilityScheduleSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, IsServiceProvider]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        # Providers only see their own schedules
        return AvailabilitySchedule.objects.filter(service_provider__user=self.request.user)

    def perform_create(self, serializer):
        provider = self.request.user.service_provider
        serializer.save(service_provider=provider)

@extend_schema(tags=['Appointments'])
class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

   
    def get_queryset(self):
        user = self.request.user
        # Provider can see their own appointments
        if hasattr(user, 'service_provider'):
            provider_appointments = Appointment.objects.filter(service__provider__user=user)
            client_appointments =  Appointment.objects.filter(client=user)
            return (provider_appointments | client_appointments).distinct()
        # Regular user can only see their own appointments
        return Appointment.objects.filter(client=user)

    def get_throttles(self):
        if self.action == 'create':
            return [AppointmentCreateThrottle()]
        return [AppointmentThrottle()]
    
    # custom endpoints
    @action(detail=False, methods=['get'], url_path='today')
    def today_appointments(self, request):
        today = date.today()
        qs = self.get_queryset().filter(appointment_date=today, status__in=["scheduled", "completed"])
        if not qs.exists():
            return Response({"message": "No appointments found for today."},status=status.HTTP_200_OK)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming_appointments(self, request):
        today = date.today()
        qs = self.get_queryset().filter(appointment_date__gt=today, status__in=["scheduled", "completed"])
        if not qs.exists():
            return Response({"message": "No upcoming appointments found."},status=status.HTTP_200_OK)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='past')
    def past_appointments(self, request):
        today = date.today()
        qs = self.get_queryset().filter(appointment_date__lt=today, status__in=["scheduled", "completed"])
        if not qs.exists():
            return Response({"message": "No past appointments found."},status=status.HTTP_200_OK)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        data = request.data
        user = request.user

        try:
            # Handle both URL and direct ID
            service_id = data.get('service')
            if isinstance(service_id, str) and '/' in service_id:
                service_id = service_id.split('/')[-2]
            service = Service.objects.get(pk=service_id)
        except (Service.DoesNotExist, AttributeError, ValueError):
            return Response({'error': 'Invalid service ID or URL.'}, status=status.HTTP_400_BAD_REQUEST)
        
        appointment_date = data.get('appointment_date')
        start_time_str = data.get('start_time')

        if not (appointment_date and start_time_str):
            return Response({'error': 'Appointment date and start time are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        appointment_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
                             
        available_slots = get_available_time_slots(service.provider, service, days_ahead=30)
        is_available = False

        """
        print("DEBUG AVAILABLE SLOTS:", available_slots)
        print("REQUESTED DATE:", appointment_date)
        print("REQUESTED TIME:", start_time)
"""
        for date_str, slots in available_slots.items():
            # convert string to date for comparison
            slot_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if slot_date == appointment_date:
                for slot in slots:
                    if slot['time'] == start_time.strftime('%H:%M:%S') and slot['available']:
                        is_available = True
                        break


        if not is_available:
            return Response({'error': 'This time slot is no longer available.'}, status=status.HTTP_400_BAD_REQUEST)

        # compute end time
        end_time = (datetime.combine(appointment_date, start_time) + timedelta(minutes=service.duration)).time()             

        # create appointment in db
        with transaction.atomic():
            appointment = Appointment.objects.create(
                service=service,
                client=user,
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                email=data.get('email'),
                phone=data.get('phone'), 
                appointment_date=appointment_date,
                start_time=start_time, 
                end_time=end_time, 
                notes=data.get('notes', ''),
                status='scheduled'
            )
            login_url = request.build_absolute_uri(reverse("accounts:login"))
            subject = "New Appointment Booked"
            message_provider = f"""
                        Hello {appointment.service.provider.user.first_name}, 

                        A new appointment has been booked by {appointment.client.first_name }, 

                        📅 Date: {appointment.appointment_date}
                        🕐 Time: {appointment.start_time.strftime('%I:%M %p')}
                        🧾 Service: {appointment.service.name}
                        💬 Note: {appointment.notes or 'None'}

                        Login to your dashboard to view more details.
                        {login_url}
                    """
            message_client = f"""
                        Hi {appointment.client.first_name},

                        Your appointment with {appointment.service.provider.user.get_full_name()} has been successfully booked.

                        📅 Date: {appointment.appointment_date}
                        🕐 Time: {appointment.start_time.strftime('%I:%M %p')}
                        🧾 Service: {appointment.service.name}

                        You can log in here if needed:
                        {login_url}

                        We'll remind you 24 hours before it starts.
                    """
            # for testing
            # print("SETTINGS:", settings)
            # print("DEFAULT_FROM_EMAIL:", settings.DEFAULT_FROM_EMAIL)
            try:
                send_mail(subject, message_provider, settings.DEFAULT_FROM_EMAIL, [appointment.service.provider.user.email])
                send_mail(subject, message_client, settings.DEFAULT_FROM_EMAIL, [appointment.client.email])
            except Exception as e:
                print(f"Email sending failed: {e}")
            appt_datetime = timezone.make_aware(
                datetime.combine(appointment.appointment_date, appointment.start_time)
            )
            serializer = self.get_serializer(appointment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        appointment = self.get_object()
        user = request.user
        new_status = request.data.get("status")

        # Allowed statuses
        valid_statuses = ["scheduled", "cancelled", "completed", "no_show"]
        if new_status not in valid_statuses:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        # Authorization rules
        if user == appointment.client:
            # Clients can only cancel their own appointments
            if new_status != "cancelled":
                return Response({"error": "You can only cancel appointments."}, status=status.HTTP_403_FORBIDDEN)
        elif user == appointment.service.provider.user:
            # Providers can mark as completed or cancel
            if new_status not in ["cancelled", "completed"]:
                return Response({"error": "You can only update to cancelled or completed."}, status=status.HTTP_403_FORBIDDEN)
        else:
            # Neither provider nor client
            return Response({"error": "Not authorized to update this appointment."}, status=status.HTTP_403_FORBIDDEN)

        # If status is already the same, ignore
        if appointment.status == new_status:
            return Response({"message": f"Appointment already {new_status}."}, status=status.HTTP_200_OK)

        # Update status
        appointment.status = new_status
        appointment.save(update_fields=['status', 'updated_at'])

        serializer = self.get_serializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)
