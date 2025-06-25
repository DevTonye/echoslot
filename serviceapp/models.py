from django.db import models
from django.db.models import UniqueConstraint
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

# service provider model
class ServiceProvider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='service_provider')
    first_name = models.CharField(max_length=50, blank=False, null=False)
    last_name = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=False, null=False)
    phone = models.CharField(max_length=20, blank=False, null=False)

    def __str__(self):
        return self.user.username
# services models
class Service(models.Model):
    service_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    provider = models.OneToOneField(ServiceProvider, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField()
    duration = models.IntegerField(help_text='Duration in minutes')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # need to add Experience
    def __str__(self):
        return self.name
    
# availability of a service provider 
class AvailabilitySchedule(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    service_provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
         # A service provider can have only one availability entry per day of the we
         constraints = [
              UniqueConstraint(fields=['service_provider', 'day_of_week'], name='unique_provider_day')
        ]
    def __str__(self):
        return f"{self.get_day_of_week_display()}: {self.start_time} - {self.end_time}"

# all appointments table  
class Appointment(models.Model):
    STATUS_CHOICE = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
    ]
    appointment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICE, default='scheduled') # track current state of an appointment
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.appointment_id} - {self.service.name} with {self.service.provider.service_name}"
    
    class Meta:
        ordering = ['appointment_date', 'start_time']


# what api can i use for notifications?? -> I think this should happen over a signal 
class Notification(models.Model):
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS')
    ]

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    sent_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField()
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.appointment.appointment_id}"