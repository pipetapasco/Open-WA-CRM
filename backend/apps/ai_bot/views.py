import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AIConfig, AIProvider
from .serializers import AIConfigSerializer

logger = logging.getLogger(__name__)


class AIConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar configuraciones de IA.
    
    Permite ver, crear y editar la configuración de IA asociada a una cuenta.
    Filtrado automático por cuentas del usuario.
    
    Endpoints:
    - GET /ai-config/ : Listar configuraciones
    - POST /ai-config/ : Crear configuración
    - GET /ai-config/{id}/ : Ver detalle
    - PUT/PATCH /ai-config/{id}/ : Actualizar
    - GET /ai-config/?account={id} : Filtrar por cuenta
    """
    serializer_class = AIConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['account', 'enabled', 'provider']
    
    def get_queryset(self):
        """
        Retorna solo las configuraciones de cuentas que pertenecen al usuario.
        """
        return AIConfig.objects.filter(account__owner=self.request.user).select_related('account')
    
    def perform_create(self, serializer):
        """Log al crear configuración."""
        instance = serializer.save()
        logger.info(f"AI Config created for account {instance.account.name} by {self.request.user}")
        
    def perform_update(self, serializer):
        """Log al actualizar configuración."""
        instance = serializer.save()
        logger.info(f"AI Config updated for account {instance.account.name}")

    @action(detail=False, methods=['get'])
    def providers(self, request):
        """
        Retorna la lista de proveedores de IA disponibles.
        """
        providers = [
            {'id': code, 'name': label}
            for code, label in AIProvider.choices
        ]
        return Response(providers)
