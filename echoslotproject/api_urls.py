from django.urls import path, include

urlpatterns = [
    path('user-auth/', include('accounts.api.urls')),
    path('', include('serviceapp.api.urls')),
    path('client-api', include('clientapp.api.urls')),
]