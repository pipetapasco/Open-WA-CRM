from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AIConfigViewSet

router = DefaultRouter()
router.register(r'config', AIConfigViewSet, basename='ai-config')

urlpatterns = [
    path('', include(router.urls)),
]
