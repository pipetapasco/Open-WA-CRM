from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WhatsAppAccountViewSet, WhatsAppTemplateViewSet, webhook

router = DefaultRouter()
router.register(r'accounts', WhatsAppAccountViewSet, basename='whatsapp-account')
router.register(r'templates', WhatsAppTemplateViewSet, basename='whatsapp-template')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/<str:phone_number_id>/', webhook, name='webhook'),
]
