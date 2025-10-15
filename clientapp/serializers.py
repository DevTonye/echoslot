from rest_framework import serializers
from .models import ClientProfile
from django.contrib.auth import get_user_model

User = get_user_model()

class ClientProfileSerializers(serializers.ModelField):
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = ClientProfile
        fields = ['id', 'user', 'first_name', 'last_name', 'profile_image', 'location', 'contact', 'timezone']