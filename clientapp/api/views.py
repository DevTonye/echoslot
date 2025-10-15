from django.shortcuts import render
from ..serializers import ClientProfileSerializers
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from ..models import ClientProfile
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from ..permissions import IsClient

User = get_user_model()

class ClientProfileiewSet(viewsets.ModelViewSet):
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializers
    permission_classes = [IsAuthenticated, IsClient]

    def get_queryset(self):
        # Providers can only see their own profile
        return ClientProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)