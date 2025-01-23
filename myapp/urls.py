"""
URL configuration for myapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.views.generic import RedirectView
from rest_framework.views import APIView
from rest_framework.response import Response

schema_view = get_schema_view(
   openapi.Info(
      title="Inventory API",
      default_version='v1',
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# Optional: Add a basic health check endpoint
class HealthCheckView(APIView):
    def get(self, request):
        return Response({"status": "healthy"})
    
class APIRootView(APIView):
    permission_classes = [permissions.AllowAny]  # Allow anyone to see the API root
    
    def get(self, request):
        return Response({
            "message": "Welcome to the Inventory API",
            "endpoints": {
                "api": "/api/",
                "admin": "/admin/",
                "documentation": {
                    "swagger": "/swagger/",
                    "redoc": "/redoc/"
                },
                "health": "/health/"
            }
        })
    
urlpatterns = [
    path('', APIRootView.as_view(), name='api-root'),
    path('admin/', admin.site.urls),
    path('api/', include('inventory.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0)),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0)),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
