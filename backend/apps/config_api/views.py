from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import HttpResponse
import logging

from .models import WhatsAppAccount, WhatsAppTemplate
from .serializers import WhatsAppAccountSerializer, WhatsAppTemplateSerializer
from apps.chat.tasks import process_webhook_payload

logger = logging.getLogger(__name__)


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


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def webhook(request, phone_number_id):
    """
    Endpoint para recibir webhooks de WhatsApp Business API.
    
    URL: /api/config/webhook/<phone_number_id>/
    
    GET: Verificación del webhook (Meta envía hub.mode, hub.verify_token, hub.challenge)
    POST: Recepción de mensajes y eventos
    """
    account = WhatsAppAccount.objects.filter(phone_number_id=phone_number_id).first()
    
    if not account:
        logger.warning(f"Webhook request for unknown phone_number_id: {phone_number_id}")
        return HttpResponse('Not Found', status=404)
    
    if request.method == 'GET':
        mode = request.query_params.get('hub.mode')
        token = request.query_params.get('hub.verify_token')
        challenge = request.query_params.get('hub.challenge')
        
        if mode == 'subscribe' and token:
            if account.webhook_verify_token == token:
                logger.info(f"Webhook verified for account: {account.name}")
                return HttpResponse(challenge, content_type='text/plain', status=200)
            else:
                logger.warning(f"Webhook verification failed: token mismatch for {account.name}")
                return HttpResponse('Forbidden', status=403)
        
        return HttpResponse('Bad Request', status=400)
    
    elif request.method == 'POST':
        payload = request.data
        
        logger.info(f"Webhook received for {account.name}: {payload.get('object', 'unknown')}")
        
        process_webhook_payload.delay(payload, phone_number_id)
        
        return Response({'status': 'ok'}, status=200)
