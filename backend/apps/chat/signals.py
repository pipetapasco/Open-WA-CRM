from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Message
from .serializers import MessageSerializer


@receiver(post_save, sender=Message)
def notify_new_message(sender, instance, created, **kwargs):
    if created:
        try:
            channel_layer = get_channel_layer()

            if channel_layer is None:
                return

            message_data = MessageSerializer(instance).data

            message_data['conversation_id'] = str(instance.conversation.id)
            message_data['contact_name'] = instance.conversation.contact.name
            message_data['contact_phone'] = instance.conversation.contact.phone_number

            async_to_sync(channel_layer.group_send)(
                'inbox_updates', {'type': 'send_new_message', 'message': message_data}
            )

        except Exception:
            pass


@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    if created:
        from django.utils import timezone

        conversation = instance.conversation
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at', 'updated_at'])
