from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import Conversation, Message
from .pagination import MessagePagination
from .serializers import (
    ConversationCreateSerializer,
    ConversationDetailSerializer,
    ConversationListSerializer,
    MessageSerializer,
    SendTextMessageSerializer,
)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Conversaciones.
    """

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'account']
    search_fields = ['contact__name', 'contact__phone_number']

    def get_queryset(self):
        user_accounts = self.request.user.whatsapp_accounts.all()
        return (
            Conversation.objects.filter(account__in=user_accounts)
            .select_related('contact', 'account')
            .annotate(
                unread_count=Count(
                    'messages',
                    filter=Q(messages__direction='incoming', messages__delivery_status__in=['sent', 'delivered']),
                )
            )
            .order_by('-last_message_at')
        )

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationListSerializer

    def destroy(self, request, *args, **kwargs):
        import os

        from django.conf import settings

        instance = self.get_object()

        messages_with_media = instance.messages.exclude(media_url__isnull=True).exclude(media_url='')

        deleted_files = 0
        for message in messages_with_media:
            if message.media_url:
                relative_path = message.media_url.lstrip('/')
                if relative_path.startswith('media/'):
                    relative_path = relative_path[6:]

                file_path = os.path.join(settings.MEDIA_ROOT, relative_path)

                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_files += 1
                    except OSError:
                        pass

        conversation_id = str(instance.id)
        instance.delete()

        return Response(
            {'status': 'deleted', 'conversation_id': conversation_id, 'deleted_files': deleted_files},
            status=status.HTTP_200_OK,
        )


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Mensajes.
    """

    serializer_class = MessageSerializer
    pagination_class = MessagePagination

    def get_queryset(self):
        user_accounts = self.request.user.whatsapp_accounts.all()
        queryset = Message.objects.filter(conversation__account__in=user_accounts).select_related(
            'conversation', 'conversation__contact'
        )

        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)

        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'])
    def by_conversation(self, request):
        conversation_id = request.query_params.get('conversation')
        if not conversation_id:
            return Response({'error': 'conversation parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(conversation_id=conversation_id)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_text(self, request, pk=None):
        serializer = SendTextMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text = serializer.validated_data['message']

        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        import uuid

        message = Message.objects.create(
            conversation=conversation,
            whatsapp_id=f'local_{uuid.uuid4().hex[:16]}',
            direction='outgoing',
            message_type='text',
            body=text,
            delivery_status='sent',
        )

        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])

        from .tasks import send_whatsapp_message

        send_whatsapp_message.delay(str(message.id))

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        updated = Message.objects.filter(
            conversation=conversation, direction='incoming', delivery_status__in=['sent', 'delivered']
        ).update(delivery_status='read')

        return Response({'marked_as_read': updated})

    @action(detail=True, methods=['post'])
    def send_template(self, request, pk=None):
        from .serializers import SendTemplateMessageSerializer

        serializer = SendTemplateMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        template_name = serializer.validated_data['template_name']
        template_language = serializer.validated_data['template_language']
        components = serializer.validated_data.get('components', [])

        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        import uuid

        from apps.config_api.models import WhatsAppTemplate

        rendered_body = f'[Template: {template_name}]'

        try:
            template = WhatsAppTemplate.objects.filter(
                account=conversation.account, name=template_name, language=template_language, status='APPROVED'
            ).first()

            if template:
                body_component = next((c for c in template.components if c.get('type') == 'BODY'), None)
                if body_component and body_component.get('text'):
                    text = body_component['text']

                    sent_body = next((c for c in components if c.get('type') == 'body'), None)

                    if sent_body and sent_body.get('parameters'):
                        params = sent_body['parameters']

                        positional_values = []
                        named_values = {}

                        for p in params:
                            if p.get('type') == 'text':
                                val = p.get('text', '')
                                if p.get('parameter_name'):
                                    named_values[p['parameter_name']] = val
                                else:
                                    positional_values.append(val)

                        for key, val in named_values.items():
                            text = text.replace(f'{{{{{key}}}}}', val)

                        for i, val in enumerate(positional_values):
                            text = text.replace(f'{{{{{i + 1}}}}}', val)

                    rendered_body = text

        except Exception:
            pass

        message = Message.objects.create(
            conversation=conversation,
            whatsapp_id=f'local_{uuid.uuid4().hex[:16]}',
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

        from .tasks import send_whatsapp_template

        send_whatsapp_template.delay(str(message.id), template_name, template_language, components)

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='upload_media', parser_classes=[MultiPartParser, FormParser])
    def upload_media(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        import os
        import uuid

        from django.conf import settings
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage

        ext = os.path.splitext(file_obj.name)[1]
        filename = f'{uuid.uuid4().hex}{ext}'
        save_path = f'whatsapp/uploads/{filename}'

        path = default_storage.save(save_path, ContentFile(file_obj.read()))
        media_url = os.path.join(settings.MEDIA_URL, path)

        return Response({'url': media_url, 'filename': filename, 'mime_type': file_obj.content_type})

    @action(detail=True, methods=['post'])
    def send_media(self, request, pk=None):
        media_type = request.data.get('media_type')
        media_url = request.data.get('media_url')
        caption = request.data.get('caption', '')

        if not media_type or not media_url:
            return Response({'error': 'media_type and media_url are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        import uuid

        message = Message.objects.create(
            conversation=conversation,
            whatsapp_id=f'local_{uuid.uuid4().hex[:16]}',
            direction='outgoing',
            message_type=media_type,
            body=caption,
            media_url=media_url,
            delivery_status='sent',
        )

        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])

        from .tasks import send_whatsapp_message

        send_whatsapp_message.delay(str(message.id))

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
