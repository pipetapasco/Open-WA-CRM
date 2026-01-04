"""
AI Bot Celery Tasks.

Tareas asíncronas para procesar respuestas de IA
e integrar con el flujo de mensajes de WhatsApp.
"""

import uuid

from celery import shared_task


@shared_task(queue='messages')
def process_ai_response(conversation_id: str) -> dict:
    from apps.ai_bot.services import AIBotService, AIBotServiceError
    from apps.chat.models import Conversation, Message

    try:
        conversation = Conversation.objects.select_related('account', 'contact').get(pk=conversation_id)

        service = AIBotService(conversation)

        if not service.is_enabled():
            return {'status': 'skipped', 'reason': 'AI not enabled'}

        response_text = service.get_response()

        if not response_text:
            return {'status': 'skipped', 'reason': 'No response generated'}

        message = Message.objects.create(
            conversation=conversation,
            whatsapp_id=f'ai_{uuid.uuid4().hex}',
            direction='outgoing',
            message_type='text',
            body=response_text,
            delivery_status='sent',
            metadata={'ai_generated': True, 'provider': service.ai_config.provider if service.ai_config else 'unknown'},
        )

        from django.utils import timezone

        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])

        from apps.chat.tasks import send_whatsapp_message

        send_whatsapp_message.delay(str(message.id))

        return {'status': 'success', 'message_id': str(message.id), 'response_length': len(response_text)}

    except Conversation.DoesNotExist:
        return {'status': 'error', 'reason': 'Conversation not found'}

    except AIBotServiceError as e:
        return {'status': 'error', 'reason': str(e)}

    except Exception as e:
        return {'status': 'error', 'reason': f'Unexpected error: {e}'}
