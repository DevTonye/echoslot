from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

# service provider profile model
class ServiceProvider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, blank=False, null=False)
    last_name = models.CharField(max_length=50, blank=False, null=False)
    service_name = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=False, null=False)
    phone = models.CharField(max_length=20, blank=False, null=False)

    def __str__(self):
        return self.service_name

# services a serviceprovider offers
class Service(models.Model):
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField()
    duration = models.IntegerField(help_text='Duration in minutes')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
    