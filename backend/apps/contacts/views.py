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
        Retorna contactos ordenados por creación reciente,
        anotados con el conteo de conversaciones.
        """
        return Contact.objects.select_related('account').annotate(
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
        Envía una plantilla a múltiples contactos.
        POST /contacts/bulk_send_template/
        Body: { 
            "ids": ["uuid1", "uuid2"],
            "template_data": { ... } 
        }
        """
        contact_ids = request.data.get('ids', [])
        template_data = request.data.get('template_data', {})
        
        if not contact_ids:
            return Response(
                {'error': 'No se proporcionaron IDs de contactos.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        from apps.chat.models import Conversation
        from apps.chat.serializers import SendTemplateMessageSerializer
        from apps.chat.views import MessageViewSet
        
        # Validar datos de plantilla usando el serializer existente
        serializer = SendTemplateMessageSerializer(data=template_data)
        serializer.is_valid(raise_exception=True)
        
        valid_data = serializer.validated_data
        
        # Filtrar contactos válidos (que pertenezcan a cuentas del usuario si aplica)
        contacts = Contact.objects.filter(id__in=contact_ids)
        
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for contact in contacts:
            try:
                # Obtener o crear conversación
                conversation, _ = Conversation.objects.get_or_create(
                    contact=contact,
                    account=contact.account
                )
                
                # Crear el mensaje localmente (reutilizando lógica similar a MessageViewSet)
                from apps.chat.models import Message
                from django.utils import timezone
                import uuid
                
                # Intentar renderizar el contenido completo de la plantilla
                rendered_body = f"[Template: {valid_data['template_name']}]"
                
                try:
                    # 1. Buscar la plantilla localmente
                    from apps.config_api.models import WhatsAppTemplate
                    template = WhatsAppTemplate.objects.filter(
                        account=contact.account,
                        name=valid_data['template_name'],
                        language=valid_data['template_language'],
                        status='APPROVED'
                    ).first()
                    
                    if template:
                        # 2. Extraer el componente BODY
                        body_component = next((c for c in template.components if c.get('type') == 'BODY'), None)
                        if body_component and body_component.get('text'):
                            text = body_component['text']
                            
                            # 3. Extraer parámetros enviados
                            # Los components enviados por el front vienen así: 
                            # [{'type': 'body', 'parameters': [...]}]
                            components = valid_data.get('components', [])
                            sent_body = next((c for c in components if c.get('type') == 'body'), None)
                            
                            if sent_body and sent_body.get('parameters'):
                                params = sent_body['parameters']
                                
                                # Mapa de valores posicionales y nombrados
                                positional_values = []
                                named_values = {}
                                
                                for p in params:
                                    if p.get('type') == 'text':
                                        val = p.get('text', '')
                                        # Si tiene parameter_name es nombrado
                                        if p.get('parameter_name'):
                                            named_values[p['parameter_name']] = val
                                        else:
                                            positional_values.append(val)
                                
                                # 4. Reemplazar variables nombradas {{nombre}}
                                for key, val in named_values.items():
                                    text = text.replace(f"{{{{{key}}}}}", val)
                                    
                                # 5. Reemplazar variables posicionales {{1}}, {{2}}
                                for i, val in enumerate(positional_values):
                                    text = text.replace(f"{{{{{i+1}}}}}", val)
                                    
                            rendered_body = text
                except Exception as e:
                    print(f"Error rendering bulk template body: {e}")

                # Crear mensaje
                # Generamos un ID temporal para evitar error de unicidad con string vacío
                # El task lo actualizará con el ID real de WhatsApp
                temp_id = f"temp-{uuid.uuid4()}"
                
                message = Message.objects.create(
                    conversation=conversation,
                    direction='outgoing',
                    message_type='template',
                    body=rendered_body,
                    # Guardamos metadata para referencia
                    metadata={
                        'template_name': valid_data['template_name'],
                        'template_language': valid_data['template_language'],
                        'components': valid_data.get('components', []),
                    },
                    delivery_status='sent',
                    whatsapp_id=temp_id
                )
                
                conversation.last_message_at = timezone.now()
                conversation.save(update_fields=['last_message_at'])
                
                # Enviar tarea asíncrona
                from apps.chat.tasks import send_whatsapp_template
                send_whatsapp_template.delay(
                    str(message.id),
                    valid_data['template_name'],
                    valid_data['template_language'],
                    valid_data.get('components', [])
                )
                
                results['success'] += 1
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                results['failed'] += 1
                results['errors'].append(f"Error con contacto {contact.id}: {str(e)}")
        
        return Response(results)
