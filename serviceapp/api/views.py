from django.shortcuts import render
from ..serializers import ServiceProviderSerializer, ServicesSerializer, AvailabilityScheduleSerializer, AppointmentSerializer
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from ..models import ServiceProvider, Service, AvailabilitySchedule, Appointment
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from ..permissions import IsServiceProvider
from ..utils import get_available_time_slots
from datetime import datetime, timedelta
from django.db import transaction
from django.urls import reverse
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import action


User = get_user_model()

class ServiceProviderViewSet(viewsets.ModelViewSet):
    queryset = ServiceProvider.objects.all()
    serializer_class = ServiceProviderSerializer
    permission_classes = [IsAuthenticated, IsServiceProvider]

    def get_queryset(self):
        # Providers can only see their own profile
        return ServiceProvider.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'], url_path='availability', permission_classes=[IsAuthenticated])
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
class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServicesSerializer   
    permission_classes = [IsAuthenticated, IsServiceProvider]

    def perform_create(self, serializer):
        provider = ServiceProvider.objects.get(user=self.request.user)
        serializer.save(provider=provider)

class AvailabilityScheduleViewSet(viewsets.ModelViewSet):
    queryset = AvailabilitySchedule.objects.all()
    serializer_class = AvailabilityScheduleSerializer
    permission_classes = [IsAuthenticated, IsServiceProvider]

    def get_queryset(self):
        # Providers only see their own schedules
        return AvailabilitySchedule.objects.filter(service_provider__user=self.request.user)

    def perform_create(self, serializer):
        provider = self.request.user.service_provider
        serializer.save(service_provider=provider)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
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
    
    def create(self, request, *args, **kwargs):
        data = request.data
        user = request.user

        try:
            service = Service.objects.get(pk=data.get('service').split('/')[-2])
        except (Service.DoesNotExist, AttributeError):
            return Response({'error': 'Invalid service URL.'}, status=status.HTTP_400_BAD_REQUEST)
        
        appointment_date = data.get('appointment_date')
        start_time_str = data.get('start_time')

        if not (appointment_date and start_time_str):
            return Response({'error': 'Invalid service URL.'}, status=status.HTTP_400_BAD_REQUEST)
        
        appointment_date = datetime.strptime(appointment_date, "%Y:%M:%D").date()
        start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
                             
        available_slots = get_available_time_slots(service.provider, service, days_ahead=30)
        is_available = False

        for date, slots in available_slots.items():
            if date == appointment_date:
                for slot in slots:
                    if slot['time'] == start_time and slot['available']:
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
            # print("SETTINGS:", settings)
            # print("DEFAULT_FROM_EMAIL:", settings.DEFAULT_FROM_EMAIL)
            send_mail(subject, message_provider, settings.DEFAULT_FROM_EMAIL, [appointment.service.provider.user.email])
            send_mail(subject, message_client, settings.DEFAULT_FROM_EMAIL, [appointment.client.email])
            
            appt_datetime = timezone.make_aware(
                datetime.combine(appointment.appointment_date, appointment.start_time)
            )
            serializer = self.get_serializer(appointment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
