"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import HelloWorldView, CustomTokenObtainPairView, GoogleLoginView
from members.views import MemberViewSet
from courts.views import CourtViewSet
from system.views import HealthCheckView

router = DefaultRouter()
router.register(r'members', MemberViewSet)
router.register(r'courts', CourtViewSet)

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Test endpoint
    path('api/hello/', HelloWorldView.as_view(), name='hello-world'),
    
    # System health check endpoint
    path('api/system/health/', HealthCheckView.as_view(), name='healthcheck'),
    
    # API endpoints registered by the router (members, courts)
    path('api/', include(router.urls)),

    # Authentication endpoints (JWT and Google OAuth)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/google/', GoogleLoginView.as_view(), name='token_obtain_google'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Génération du schéma YAML/JSON

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Interfaces UI

    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
