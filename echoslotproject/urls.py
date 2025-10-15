from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView,)


urlpatterns = [
    # web routes
    path('admin/', admin.site.urls),
    path('user-auth/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('echoslot/', include('echoslot.urls')),
    path('services/', include('serviceapp.urls')),
    path('client/', include('clientapp.urls')),

    # api routes (all grouped under /api/)
    path('api/', include('echoslotproject.api_urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
