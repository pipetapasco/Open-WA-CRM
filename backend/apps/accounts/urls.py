from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import RegisterView, MeView

urlpatterns = [
    # Registro
    path('register/', RegisterView.as_view(), name='auth-register'),
    
    # JWT Login (obtener tokens)
    path('login/', TokenObtainPairView.as_view(), name='auth-login'),
    
    # Refresh token
    path('refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    
    # Usuario actual
    path('me/', MeView.as_view(), name='auth-me'),
]
