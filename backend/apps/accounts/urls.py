from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    register_view,
    login_view,
    logout_view,
    AuthRegisterAPIView,
    AuthLoginAPIView,
    AuthLogoutAPIView,
    AuthProfileAPIView,
    AddressViewSet,
)

router = DefaultRouter()
router.register(r'addresses', AddressViewSet, basename='address')

urlpatterns = [
    # Legacy HTML session views
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # SRS Section 8.1 API endpoints
    path('api/register/', AuthRegisterAPIView.as_view(), name='api-auth-register'),
    path('api/login/', AuthLoginAPIView.as_view(), name='api-auth-login'),
    path('api/logout/', AuthLogoutAPIView.as_view(), name='api-auth-logout'),
    path('api/profile/', AuthProfileAPIView.as_view(), name='api-auth-profile'),

    # Address Management
    path('api/', include(router.urls)),
]

