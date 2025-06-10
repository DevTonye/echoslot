from django.urls import path
from . import views

app_name = 'echoslot'

urlpatterns = [
    path('', views.index, name='index')
]