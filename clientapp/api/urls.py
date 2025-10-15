from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientProfileiewSet

router = DefaultRouter()
router.register(r'clientsprofile', ClientProfileiewSet, basename='client')

urlpatterns = [
    path('', include(router.urls)),
]