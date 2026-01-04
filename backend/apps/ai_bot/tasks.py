"""
AI Bot Celery Tasks.

Tareas asíncronas para procesar respuestas de IA
e integrar con el flujo de mensajes de WhatsApp.
"""
import logging
import uuid
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(queue='messages')
def process_ai_response(conversation_id: str) -> dict:
    """
    Procesa una respuesta de IA para una conversación.
    
    Esta tarea:
    1. Usa AIBotService para generar una respuesta
    2. Crea un mensaje en la BD con direction='outgoing'
    3. Dispara la tarea send_whatsapp_message para enviar
    
    Args:
        conversation_id: UUID de la conversación como string.
    
    Returns:
        Dict con el resultado del procesamiento.
    """
    from apps.chat.models import Conversation, Message
    from apps.ai_bot.services import AIBotService, AIBotServiceError
    
    try:
        # Obtener la conversación
        conversation = Conversation.objects.select_related(
            'account', 'contact'
        ).get(pk=conversation_id)
        
        # Crear servicio y verificar si está habilitado
        service = AIBotService(conversation)
        
        if not service.is_enabled():
            logger.debug(f"AI not enabled for conversation {conversation_id}")
            return {
                'status': 'skipped',
                'reason': 'AI not enabled'
            }
        
        # Generar respuesta de IA
        response_text = service.get_response()
        
        if not response_text:
            logger.warning(f"No AI response generated for conversation {conversation_id}")
            return {
                'status': 'skipped',
                'reason': 'No response generated'
            }
        
        # Crear mensaje en la BD
        message = Message.objects.create(
            conversation=conversation,
            whatsapp_id=f"ai_{uuid.uuid4().hex}",  # ID temporal, se actualiza al enviar
            direction='outgoing',
            message_type='text',
            body=response_text,
            delivery_status='sent',
            metadata={
                'ai_generated': True,
                'provider': service.ai_config.provider if service.ai_config else 'unknown'
            }
        )
        
        logger.info(f"AI message created: {message.id} for conversation {conversation_id}")
        
        # Actualizar timestamp de la conversación
        from django.utils import timezone
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])
        
        # Disparar tarea de envío a WhatsApp
        from apps.chat.tasks import send_whatsapp_message
        send_whatsapp_message.delay(str(message.id))
        
        logger.info(f"AI response queued for sending: {message.id}")
        
        return {
            'status': 'success',
            'message_id': str(message.id),
            'response_length': len(response_text)
        }
        
    except Conversation.DoesNotExist:
        logger.error(f"Conversation not found: {conversation_id}")
        return {
            'status': 'error',
            'reason': 'Conversation not found'
        }
        
    except AIBotServiceError as e:
        logger.error(f"AI service error for conversation {conversation_id}: {e}")
        return {
            'status': 'error',
            'reason': str(e)
        }
        
    except Exception as e:
        logger.exception(f"Unexpected error processing AI response: {e}")
        return {
            'status': 'error',
            'reason': f'Unexpected error: {e}'
        }
