from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthRegisterAPIView,
    AuthLoginAPIView,
    AuthLogoutAPIView,
    AuthProfileAPIView,
    AddressViewSet,
)

router = DefaultRouter()
router.register(r'addresses', AddressViewSet, basename='address')

urlpatterns = [
    path('auth/register/', AuthRegisterAPIView.as_view(), name='api_auth_register'),
    path('auth/login/', AuthLoginAPIView.as_view(), name='api_auth_login'),
    path('auth/logout/', AuthLogoutAPIView.as_view(), name='api_auth_logout'),
    path('auth/profile/', AuthProfileAPIView.as_view(), name='api_auth_profile'),
    path('', include(router.urls)),
]
