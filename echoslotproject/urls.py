from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user-auth/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('echoslot/', include('echoslot.urls')),
    path('services/', include('serviceapp.urls')),
    path('client/', include('clientapp.urls')),
] 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
