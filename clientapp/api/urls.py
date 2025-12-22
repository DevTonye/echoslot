from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientProfileViewSet

router = DefaultRouter()
router.register(r'clientsprofile', ClientProfileViewSet, basename='client')

urlpatterns = [
    path('', include(router.urls)),
]