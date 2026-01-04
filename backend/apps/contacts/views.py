from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count

from .models import Contact
from .serializers import ContactSerializer


class ContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Contactos.
    
    Endpoints:
    - GET /contacts/ - Listar contactos
    - POST /contacts/ - Crear contacto
    - GET /contacts/{id}/ - Detalle
    - PUT/PATCH /contacts/{id}/ - Actualizar
    - DELETE /contacts/{id}/ - Eliminar
    
    Filtros:
    - ?account={uuid} - Filtrar por cuenta de WhatsApp
    - ?search={term} - Buscar por nombre o teléfono
    """
    serializer_class = ContactSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'phone_number']
    filterset_fields = ['account']

    def get_queryset(self):
        """
        Retorna contactos del usuario actual,
        ordenados por creación reciente,
        anotados con el conteo de conversaciones.
        """
        user_accounts = self.request.user.whatsapp_accounts.all()
        return Contact.objects.filter(
            account__in=user_accounts
        ).select_related('account').annotate(
            conversations_count=Count('conversations')
        ).order_by('-created_at')

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """
        Elimina múltiples contactos.
        POST /contacts/bulk_delete/
        Body: { "ids": ["uuid1", "uuid2"] }
        """
        contact_ids = request.data.get('ids', [])
        if not contact_ids:
            return Response(
                {'error': 'No se proporcionaron IDs de contactos.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count, _ = Contact.objects.filter(
            id__in=contact_ids,
            account__in=request.user.whatsapp_accounts.all() if not request.user.is_superuser else Contact.objects.all().values('account')
        ).delete()
        
        return Response({'deleted': deleted_count})

    @action(detail=False, methods=['post'])
    def bulk_send_template(self, request):
        """
        Envía una plantilla de WhatsApp a múltiples contactos.
        
        Esta vista actúa como "Thin View", delegando toda la lógica
        de negocio al WhatsAppNotificationService.
        
        POST /contacts/bulk_send_template/
        Body: {
            "ids": ["uuid1", "uuid2", ...],
            "template_data": {
                "template_name": "hello_world",
                "template_language": "es",
                "components": [...]  // opcional
            }
        }
        
        Returns:
            Response con el resumen de envíos:
            {
                "success": int,
                "failed": int,
                "errors": [str, ...]
            }
        """
        from apps.chat.serializers import SendTemplateMessageSerializer
        from apps.chat.services import (
            WhatsAppNotificationService,
            TemplateData,
        )
        
        # 1. Extraer datos de la solicitud
        contact_ids: list[str] = request.data.get('ids', [])
        template_data_raw: dict = request.data.get('template_data', {})
        
        # 2. Validar que se proporcionaron IDs
        if not contact_ids:
            return Response(
                {'error': 'No se proporcionaron IDs de contactos.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 3. Validar datos de plantilla con el serializer existente
        serializer = SendTemplateMessageSerializer(data=template_data_raw)
        serializer.is_valid(raise_exception=True)
        
        # 4. Construir DTO de plantilla desde datos validados
        template_data = TemplateData.from_validated_data(serializer.validated_data)
        
        # 5. Obtener contactos (sin filtrar por cuenta del usuario para bulk ops)
        contacts = Contact.objects.select_related('account').filter(
            id__in=contact_ids
        )
        
        # 6. Inicializar servicio y contadores de resultados
        service = WhatsAppNotificationService()
        results: dict[str, int | list[str]] = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        # 7. Iterar sobre contactos y delegar al servicio
        for contact in contacts:
            result = service.send_template_to_contact(
                contact=contact,
                account=contact.account,
                template_data=template_data
            )
            
            if result.success:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(
                    f"Error con contacto {contact.id}: {result.error}"
                )
        
        return Response(results)
