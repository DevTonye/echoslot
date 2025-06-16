from django.urls import path
from . import views

app_name = 'clientapp'

urlpatterns = [
    path('profile/', views.create_clientprofile, name='clientprofile'),
    path('your-dashboard/', views.client_dashboard, name='client_dashboard'),
]