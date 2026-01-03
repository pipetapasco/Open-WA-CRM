from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

from .models import Message
from .serializers import MessageSerializer

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Message)
def notify_new_message(sender, instance, created, **kwargs):
    """
    Signal que se dispara cuando se crea un mensaje.
    Envía notificación a todos los clientes WebSocket conectados.
    """
    if created:
        logger.info(
            f"SOCKET TRIGGER: Nuevo mensaje en chat {instance.conversation.id} "
            f"(direction={instance.direction}, type={instance.message_type})"
        )
        
        try:
            channel_layer = get_channel_layer()
            
            if channel_layer is None:
                logger.warning("Channel layer not configured")
                return
            
            # Serializar el mensaje para enviar por WebSocket
            message_data = MessageSerializer(instance).data
            
            # Agregar info de la conversación y contacto
            message_data['conversation_id'] = str(instance.conversation.id)
            message_data['contact_name'] = instance.conversation.contact.name
            message_data['contact_phone'] = instance.conversation.contact.phone_number
            
            # Enviar al grupo inbox_updates
            async_to_sync(channel_layer.group_send)(
                'inbox_updates',
                {
                    'type': 'send_new_message',
                    'message': message_data
                }
            )
            
            logger.debug(f"Message sent to WebSocket group: inbox_updates")
            
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {e}")


@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    """
    Actualiza el timestamp de la conversación cuando se crea un mensaje.
    """
    if created:
        from django.utils import timezone
        conversation = instance.conversation
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at', 'updated_at'])
