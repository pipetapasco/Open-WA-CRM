from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import WhatsAppAccount, WhatsAppTemplate
from .serializers import WhatsAppAccountSerializer, WhatsAppTemplateSerializer


class WhatsAppAccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar cuentas de WhatsApp Business.
    
    Endpoints:
    - GET /accounts/ - Listar cuentas
    - POST /accounts/ - Crear cuenta
    - GET /accounts/{id}/ - Detalle
    - PUT/PATCH /accounts/{id}/ - Actualizar
    - DELETE /accounts/{id}/ - Eliminar
    - GET /accounts/{id}/sync_templates/ - Sincronizar plantillas
    """
    queryset = WhatsAppAccount.objects.all()
    serializer_class = WhatsAppAccountSerializer
    
    @action(detail=True, methods=['get'])
    def sync_templates(self, request, pk=None):
        """
        Placeholder para sincronizar plantillas desde Meta API.
        TODO: Implementar llamada a WhatsApp Business API para
        obtener las plantillas aprobadas.
        """
        account = self.get_object()
        
        return Response({
            'status': 'pending',
            'message': f'Sync templates for account "{account.name}" - Not implemented yet',
            'account_id': str(account.id),
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class WhatsAppTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar plantillas de WhatsApp.
    """
    queryset = WhatsAppTemplate.objects.select_related('account').all()
    serializer_class = WhatsAppTemplateSerializer
    filterset_fields = ['account', 'category', 'status', 'language']
