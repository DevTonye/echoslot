from django.urls import path
from . import views

app_name = 'echoslot'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('api/docs/', views.api_documentation, name='api_docs'),
]