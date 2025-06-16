from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='clientprofile')
    first_name = models.CharField(max_length=60, blank=False, null=False)
    last_name = models.CharField(max_length=60, blank=False, null=False)
    profile_image = models.ImageField(upload_to='client/profile/', blank=False, null=False)
    location = models.CharField(max_length=250, blank=False, null=False)
    contact = models.CharField(max_length=20)
     
    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    