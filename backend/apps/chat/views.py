from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone

from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer,
    ConversationDetailSerializer,
    MessageSerializer,
    SendTextMessageSerializer,
    ConversationCreateSerializer,
)
from .pagination import MessagePagination


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Conversaciones.
    
    Endpoints:
    - GET /conversations/ - Listar conversaciones
    - GET /conversations/{id}/ - Detalle de conversación
    - PATCH /conversations/{id}/ - Actualizar (ej: cambiar status)
    - DELETE /conversations/{id}/ - Eliminar conversación con todos sus archivos
    
    Filtros:
    - ?status=open|resolved - Filtrar por estado
    - ?account={uuid} - Filtrar por cuenta de WhatsApp
    """
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'account']
    search_fields = ['contact__name', 'contact__phone_number']

    def get_queryset(self):
        """
        Retorna conversaciones con conteo de mensajes no leídos.
        Mensajes entrantes que no han sido leídos.
        """
        return Conversation.objects.select_related(
            'contact', 'account'
        ).annotate(
            unread_count=Count(
                'messages',
                filter=Q(
                    messages__direction='incoming',
                    messages__delivery_status__in=['sent', 'delivered']
                )
            )
        ).order_by('-last_message_at')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationListSerializer

    def destroy(self, request, *args, **kwargs):
        """
        Elimina una conversación y todos sus archivos multimedia asociados.
        """
        import os
        from django.conf import settings
        
        instance = self.get_object()
        
        # Obtener todos los mensajes con archivos multimedia
        messages_with_media = instance.messages.exclude(
            media_url__isnull=True
        ).exclude(media_url='')
        
        # Eliminar archivos del sistema de archivos
        deleted_files = 0
        for message in messages_with_media:
            if message.media_url:
                # Convertir URL relativa a path absoluto
                # media_url es algo como "/media/whatsapp/archivo.jpg"
                relative_path = message.media_url.lstrip('/')
                if relative_path.startswith('media/'):
                    relative_path = relative_path[6:]  # Quitar "media/"
                
                file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_files += 1
                    except OSError as e:
                        print(f"Error deleting file {file_path}: {e}")
        
        # Eliminar la conversación (esto elimina mensajes en cascada)
        conversation_id = str(instance.id)
        instance.delete()
        
        return Response({
            'status': 'deleted',
            'conversation_id': conversation_id,
            'deleted_files': deleted_files
        }, status=status.HTTP_200_OK)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Mensajes.
    
    Endpoints:
    - GET /messages/?conversation={uuid} - Listar mensajes de una conversación
    - POST /messages/{conv_id}/send_text/ - Enviar mensaje de texto
    
    Paginación: 50 mensajes por página (para Infinite Scroll)
    """
    serializer_class = MessageSerializer
    pagination_class = MessagePagination

    def get_queryset(self):
        """
        Retorna mensajes ordenados por fecha (más recientes primero para scroll).
        Opcionalmente filtrados por conversación.
        """
        queryset = Message.objects.select_related('conversation', 'conversation__contact')
        
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        
        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'])
    def by_conversation(self, request):
        """
        Obtiene mensajes de una conversación específica.
        Usage: GET /messages/by_conversation/?conversation={uuid}
        """
        conversation_id = request.query_params.get('conversation')
        if not conversation_id:
            return Response(
                {'error': 'conversation parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(conversation_id=conversation_id)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_text(self, request, pk=None):
        """
        Envía un mensaje de texto desde una conversación existente.
        
        POST /messages/{conversation_id}/send_text/
        Body: { "message": "Hola, ¿cómo estás?" }
        """
        serializer = SendTextMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        text = serializer.validated_data['message']
        
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        import uuid
        message = Message.objects.create(
            conversation=conversation,
            whatsapp_id=f"local_{uuid.uuid4().hex[:16]}",
            direction='outgoing',
            message_type='text',
            body=text,
            delivery_status='sent',
        )
        
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])
        
        # Encolar el envío real a WhatsApp (asíncrono)
        from .tasks import send_whatsapp_message
        send_whatsapp_message.delay(str(message.id))
        
        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Marca todos los mensajes de una conversación como leídos.
        
        POST /messages/{conversation_id}/mark_as_read/
        """
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        updated = Message.objects.filter(
            conversation=conversation,
            direction='incoming',
            delivery_status__in=['sent', 'delivered']
        ).update(delivery_status='read')
        
        return Response({'marked_as_read': updated})

    @action(detail=True, methods=['post'])
    def send_template(self, request, pk=None):
        """
        Envía un mensaje de plantilla a una conversación existente.
        
        POST /messages/{conversation_id}/send_template/
        Body: {
            "template_name": "hello_world",
            "template_language": "es",
            "components": [{"type": "body", "parameters": [{"type": "text", "text": "valor"}]}]
        }
        """
        from .serializers import SendTemplateMessageSerializer
        
        serializer = SendTemplateMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        template_name = serializer.validated_data['template_name']
        template_language = serializer.validated_data['template_language']
        components = serializer.validated_data.get('components', [])
        
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        import uuid
        from apps.config_api.models import WhatsAppTemplate
        
        # Intentar renderizar el contenido completo de la plantilla
        rendered_body = f"[Template: {template_name}]"
        
        try:
            # 1. Buscar la plantilla localmente
            template = WhatsAppTemplate.objects.filter(
                account=conversation.account,
                name=template_name,
                language=template_language,
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
                        # Nota: Meta usa índices base-1 en el texto {{1}}
                        for i, val in enumerate(positional_values):
                            text = text.replace(f"{{{{{i+1}}}}}", val)
                            
                    rendered_body = text
                    
        except Exception as e:
            print(f"Error rendering template body: {e}")
            # Fallback al default
            pass

        # Crear mensaje de tipo template
        message = Message.objects.create(
            conversation=conversation,
            whatsapp_id=f"local_{uuid.uuid4().hex[:16]}",
            direction='outgoing',
            message_type='template',
            body=rendered_body,
            metadata={
                'template_name': template_name,
                'template_language': template_language,
                'components': components,
            },
            delivery_status='sent',
        )
        
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])
        
        # Encolar el envío real a WhatsApp
        from .tasks import send_whatsapp_template
        send_whatsapp_template.delay(
            str(message.id),
            template_name,
            template_language,
            components
        )
        
        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED
        )
