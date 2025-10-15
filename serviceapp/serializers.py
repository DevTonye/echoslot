from rest_framework import serializers
from .models import ServiceProvider, Service, AvailabilitySchedule, Appointment
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

class ServiceProviderSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    service = serializers.HyperlinkedRelatedField(read_only=True, view_name='service-detail')
    class Meta:
        model = ServiceProvider
        fields = ['id', 'user', 'first_name', 'last_name', 'profile_image', 'bio', 'address', 'phone', 'timezone', 'service']

class ServicesSerializer(serializers.HyperlinkedModelSerializer):
    provider = serializers.HyperlinkedRelatedField(view_name='serviceprovider-detail', read_only=True)
    class Meta:
        model = Service
        fields = ['url',  'service_id', 'provider', 'name', 'description', 'duration', 'price']


class AvailabilityScheduleSerializer(serializers.HyperlinkedModelSerializer):
    service_provider = serializers.HyperlinkedRelatedField(view_name='serviceprovider-detail', read_only=True)
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    class Meta:
        model = AvailabilitySchedule
        fields = ['url', 'service_provider', 'day_of_week', 'day_of_week_display', 'start_time', 'end_time']

    def validate(self, data):
        # Ensure valid time range and unique availability per day for a provider.
        request = self.context.get("request")
        service_provider = getattr(request.user, "service_provider", None)
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        day = data.get("day_of_week")

        if start_time and end_time:
            if start_time >= end_time:
                serializers.ValidationError("End time must be after start time.")

        # Check duplicate schedule for same provider/day
        if service_provider and day is not None:
            existing = AvailabilitySchedule.objects.filter(service_provider=service_provider, day_of_week=day)

        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)  # allow update of same record

        if existing.exists():
            raise serializers.ValidationError("You have already set availability for this day.")
        
        return data
    
    def create(self, validated_data):
        request = self.context.get("request")
        service_provider = getattr(request.user, "serviceprovider", None)
        return AvailabilitySchedule.objects.create(service_provider=service_provider, **validated_data)
    
class AppointmentSerializer(serializers.HyperlinkedModelSerializer):
    service = serializers.HyperlinkedRelatedField(
        view_name='service-detail',
        queryset=Service.objects.all()
    )
    # set for now
    client_email = serializers.EmailField(source='client.email', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'url', 'appointment_id', 'service', 'client_email',
            'first_name', 'last_name', 'email', 'phone', 
            'appointment_date', 'start_time', 'end_time','status', 'notes', 
            'created_at','updated_at'
            ]
        read_only_fields = ['end_time', 'status']
      
      # Check that the appointment doesn't overlap with existing appointments
        def validate(self, attrs):
            service = attrs.get('service')
            appointment_date = attrs.get('appointment_date')
            start_time = attrs.get('start_time')
            end_time = attrs.get('end_time')
        
            # Basic field presence checks
            if not service or not appointment_date or not start_time:
                raise serializers.ValidationError("Service, date, and time are required.")
            
            # Calculate end_time based on service duration
            start_datetime = datetime.combine(appointment_date, start_time)
            end_datetime = start_datetime + timedelta(minutes=service.duration)
            attrs['end_time'] = end_datetime.time()

            # Validate overlapping appointments
            overlapping = Appointment.objects.filter(
                service__provider = service.provider, 
                appointment_date=appointment_date,
                status__in = ['scheduled', 'confirmed']
            )
        
            # exclude self if updating
            if self.instance:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            for existing in overlapping:
                if start_time < existing.end_time and attrs['end_time']  > existing.start_time:
                    raise serializers.ValidationError("This time slot is no longer available.")
            return attrs