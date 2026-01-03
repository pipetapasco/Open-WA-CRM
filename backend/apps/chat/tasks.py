from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue='whatsapp')
def process_webhook_payload(self, payload: dict, phone_number_id: str):
    """
    Procesa el payload del webhook de WhatsApp de forma asíncrona.
    
    Args:
        payload: JSON recibido del webhook de Meta
        phone_number_id: ID del número de teléfono (para identificar la cuenta)
    """
    try:
        logger.info(f"Processing webhook payload for {phone_number_id}: {payload.get('object', 'unknown')}")

        entry = payload.get('entry', [])
        
        for e in entry:
            changes = e.get('changes', [])
            
            for change in changes:
                value = change.get('value', {})
                
                messages = value.get('messages', [])
                for message in messages:
                    process_incoming_message.delay(message, phone_number_id)
                
                statuses = value.get('statuses', [])
                for status_update in statuses:
                    process_status_update.delay(status_update)
        
        logger.info("Webhook payload processed successfully")
        return {'status': 'success'}
        
    except Exception as exc:
        logger.error(f"Error processing webhook: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(queue='messages')
def process_incoming_message(message: dict, phone_number_id: str):
    """
    Procesa un mensaje entrante de WhatsApp.
    
    Args:
        message: Datos del mensaje
        phone_number_id: ID del número de teléfono de la cuenta
    """
    from apps.contacts.models import Contact
    from apps.chat.models import Conversation, Message
    from apps.config_api.models import WhatsAppAccount
    
    try:
        account = WhatsAppAccount.objects.filter(phone_number_id=phone_number_id).first()
        if not account:
            logger.warning(f"Account not found for phone_number_id: {phone_number_id}")
            return
        
        sender_phone = message.get('from')
        contact, created = Contact.objects.get_or_create(
            account=account,
            phone_number=sender_phone,
            defaults={'name': sender_phone}
        )
        
        if created:
            logger.info(f"New contact created: {sender_phone}")
        
        conversation, _ = Conversation.objects.get_or_create(
            account=account,
            contact=contact,
            defaults={'status': 'open'}
        )
        
        msg_type = message.get('type', 'text')
        msg_body = ''
        
        if msg_type == 'text':
            msg_body = message.get('text', {}).get('body', '')
        elif msg_type in ['image', 'video', 'audio', 'document']:
            msg_body = f"[{msg_type.upper()}]"
        
        Message.objects.create(
            conversation=conversation,
            whatsapp_id=message.get('id'),
            direction='inbound',
            message_type=msg_type,
            body=msg_body,
            metadata=message,
            status='received'
        )
        
        from django.utils import timezone
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])
        
        logger.info(f"Message saved: {message.get('id')}")
        
    except Exception as exc:
        logger.error(f"Error processing message: {exc}")
        raise


@shared_task(queue='messages')
def process_status_update(status_update: dict):
    """
    Procesa actualizaciones de estado de mensajes (delivered, read, failed).
    
    Args:
        status_update: Datos del status update
    """
    from apps.chat.models import Message
    
    try:
        whatsapp_id = status_update.get('id')
        new_status = status_update.get('status')
        
        message = Message.objects.filter(whatsapp_id=whatsapp_id).first()
        if message:
            message.status = new_status
            message.save(update_fields=['status', 'updated_at'])
            logger.info(f"Message {whatsapp_id} status updated to: {new_status}")
        else:
            logger.warning(f"Message not found for status update: {whatsapp_id}")
            
    except Exception as exc:
        logger.error(f"Error processing status update: {exc}")
        raise
