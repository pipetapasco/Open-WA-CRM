from celery import shared_task
import logging
import httpx

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue='messages', max_retries=3)
def send_whatsapp_message(self, message_id: str):
    """
    Envía un mensaje a WhatsApp vía la API de Meta.
    
    Args:
        message_id: UUID del mensaje en nuestra BD
    """
    from apps.chat.models import Message
    
    try:
        message = Message.objects.select_related(
            'conversation__contact', 
            'conversation__account'
        ).get(pk=message_id)
        
        account = message.conversation.account
        contact = message.conversation.contact
        
        # Construir el payload para la API de Meta
        api_url = f"https://graph.facebook.com/v18.0/{account.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": contact.phone_number,
            "type": message.message_type,
        }
        
        if message.message_type == 'text':
            payload["text"] = {"body": message.body}
        elif message.message_type in ['image', 'video', 'audio', 'document', 'sticker']:
            media_id = None
            
            # Si tenemos media_url
            if message.media_url:
                # Subir archivo a Meta para obtener ID
                try:
                    # Fix: Convertir formatos no soportados (ej: webm -> ogg)
                    if message.message_type == 'audio':
                        from apps.common.utils import convert_media_for_whatsapp
                        converted_path = convert_media_for_whatsapp(message.media_url)
                        
                        # Si cambió el path, actualizar DB para futuras referencias y para que el upload use el nuevo
                        if converted_path != message.media_url:
                            logger.info(f"Updated media url after conversion: {message.media_url} -> {converted_path}")
                            message.media_url = converted_path
                            message.media_url = converted_path
                            message.save(update_fields=['media_url'])
                    
                    # New: Calculate duration for audio messages
                    if message.message_type == 'audio':
                         from apps.common.utils import get_media_duration
                         duration = get_media_duration(message.media_url)
                         if duration > 0:
                             logger.info(f"Audio duration: {duration}s")
                             if not message.metadata:
                                 message.metadata = {}
                             message.metadata['duration'] = duration
                             message.save(update_fields=['metadata'])
                    
                    media_id = upload_media_to_meta(message.media_url, account)
                except Exception as e:
                    logger.error(f"Failed to upload media to Meta: {e}")
                    raise e
            
            if not media_id:
                raise Exception("Cannot send media message without media_id")
                
            media_obj = {"id": media_id}
            
            # Añadir caption solo para tipos soportados
            if message.message_type in ['image', 'video', 'document'] and message.body:
                media_obj["caption"] = message.body
                
            # Añadir filename para documentos si es posible
            if message.message_type == 'document':
                import os
                media_obj["filename"] = os.path.basename(message.media_url)
                
            payload[message.message_type] = media_obj
        
        headers = {
            "Authorization": f"Bearer {account.access_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Sending message to WhatsApp: {contact.phone_number} (Type: {message.message_type})")
        
        # Enviar a la API de Meta
        with httpx.Client(timeout=60.0) as client:
            response = client.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            whatsapp_id = data.get('messages', [{}])[0].get('id')
            
            # Actualizar el mensaje con el ID real de WhatsApp
            if whatsapp_id:
                message.whatsapp_id = whatsapp_id
            message.delivery_status = 'sent'
            message.save(update_fields=['whatsapp_id', 'delivery_status', 'updated_at'])
            
            logger.info(f"Message sent successfully: {whatsapp_id}")
            return {'status': 'sent', 'whatsapp_id': whatsapp_id}
        else:
            logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
            message.delivery_status = 'failed'
            message.save(update_fields=['delivery_status', 'updated_at'])
            raise Exception(f"WhatsApp API error: {response.status_code}")
            
    except Message.DoesNotExist:
        logger.error(f"Message not found: {message_id}")
        return {'status': 'error', 'message': 'Message not found'}
        
    except Exception as exc:
        logger.error(f"Error sending message: {exc}")
        raise self.retry(exc=exc, countdown=30)


def upload_media_to_meta(media_path: str, account) -> str:
    """
    Sube un archivo local a la API de WhatsApp y retorna el media_id.
    """
    import os
    import mimetypes
    from django.conf import settings
    
    # 1. Resolver path local absoluto
    # media_path viene como relativo a MEDIA_URL o absoluto
    if media_path.startswith(settings.MEDIA_URL):
        relative_path = media_path[len(settings.MEDIA_URL):]
        file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    elif media_path.startswith('/'):
        # Asumimos que es relativo a media root si no matchea url media
        # esto es un poco tricky, mejor intentar reconstruir
         if settings.MEDIA_URL in media_path:
             offset = media_path.find(settings.MEDIA_URL) + len(settings.MEDIA_URL)
             file_path = os.path.join(settings.MEDIA_ROOT, media_path[offset:])
         else:
             file_path = media_path
    else:
        file_path = os.path.join(settings.MEDIA_ROOT, media_path)
        
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Media file not found: {file_path}")
        
    # 2. Obtener MIME type y tamaño
    mimetypes.init()
    mime_type, _ = mimetypes.guess_type(file_path)
    
    # Fallback específico para ogg/opus que a veces falla en contenedores mínimos
    if not mime_type:
        if file_path.endswith('.ogg'):
            mime_type = 'audio/ogg'
        elif file_path.endswith('.opus'):
            mime_type = 'audio/ogg' # WhatsApp usa este mimetype a menudo
        else:
            mime_type = 'application/octet-stream'
    
    file_size = os.path.getsize(file_path)
    
    # 3. Iniciar sesión de upload (resumable) o simple upload?
    # La API Graph soporta upload simple post a /{phone_id}/media
    
    url = f"https://graph.facebook.com/v18.0/{account.phone_number_id}/media"
    
    headers = {
        "Authorization": f"Bearer {account.access_token}"
    }
    
    files = {
        'file': (os.path.basename(file_path), open(file_path, 'rb'), mime_type)
    }
    
    data = {
        'messaging_product': 'whatsapp'
    }
    
    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, headers=headers, files=files, data=data)
        
    if response.status_code == 200:
        return response.json().get('id')
    else:
        raise Exception(f"Media upload failed: {response.status_code} - {response.text}")


@shared_task(bind=True, queue='messages', max_retries=3)
def send_whatsapp_template(self, message_id: str, template_name: str, template_language: str, components: list = None):
    """
    Envía un mensaje de plantilla a WhatsApp vía la API de Meta.
    
    Args:
        message_id: UUID del mensaje en nuestra BD
        template_name: Nombre de la plantilla
        template_language: Código de idioma (ej: es, en_US)
        components: Lista de componentes con variables
    """
    from apps.chat.models import Message
    
    try:
        message = Message.objects.select_related(
            'conversation__contact', 
            'conversation__account'
        ).get(pk=message_id)
        
        account = message.conversation.account
        contact = message.conversation.contact
        
        # Construir el payload para plantilla
        api_url = f"https://graph.facebook.com/v18.0/{account.phone_number_id}/messages"
        
        template_payload = {
            "name": template_name,
            "language": {"code": template_language},
        }
        
        # Añadir componentes si existen (variables)
        if components:
            template_payload["components"] = components
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": contact.phone_number,
            "type": "template",
            "template": template_payload
        }
        
        headers = {
            "Authorization": f"Bearer {account.access_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Sending template '{template_name}' to: {contact.phone_number}")
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            whatsapp_id = data.get('messages', [{}])[0].get('id')
            
            if whatsapp_id:
                message.whatsapp_id = whatsapp_id
            message.delivery_status = 'sent'
            message.save(update_fields=['whatsapp_id', 'delivery_status', 'updated_at'])
            
            logger.info(f"Template sent successfully: {whatsapp_id}")
            return {'status': 'sent', 'whatsapp_id': whatsapp_id}
        else:
            logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
            message.delivery_status = 'failed'
            message.save(update_fields=['delivery_status', 'updated_at'])
            raise Exception(f"WhatsApp API error: {response.status_code}")
            
    except Message.DoesNotExist:
        logger.error(f"Message not found: {message_id}")
        return {'status': 'error', 'message': 'Message not found'}
        
    except Exception as exc:
        logger.error(f"Error sending template: {exc}")
        raise self.retry(exc=exc, countdown=30)



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
        media_url = None
        
        if msg_type == 'text':
            msg_body = message.get('text', {}).get('body', '')
        elif msg_type in ['image', 'video', 'audio', 'document', 'sticker']:
            media_info = message.get(msg_type, {})
            msg_body = media_info.get('caption', '')
            media_id = media_info.get('id')
            
            if media_id:
                try:
                    media_url = download_whatsapp_media(media_id, account.access_token)
                except Exception as e:
                    logger.error(f"Failed to download media {media_id}: {e}")
                    media_url = None
        
        Message.objects.create(
            conversation=conversation,
            whatsapp_id=message.get('id'),
            direction='incoming',
            message_type=msg_type,
            body=msg_body,
            media_url=media_url,
            metadata=message,
            delivery_status='delivered'
        )
        
        from django.utils import timezone
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])
        
        logger.info(f"Message saved: {message.get('id')}")
        
        # === AI Bot Integration ===
        # Disparar procesamiento de IA si está habilitado
        try:
            from apps.ai_bot.services import AIBotService
            ai_service = AIBotService(conversation)
            if ai_service.is_enabled():
                from apps.ai_bot.tasks import process_ai_response
                process_ai_response.delay(str(conversation.id))
                logger.info(f"AI processing triggered for conversation {conversation.id}")
        except Exception as ai_error:
            logger.warning(f"AI processing skipped: {ai_error}")
        
    except Exception as exc:
        logger.error(f"Error processing message: {exc}")
        raise


def download_whatsapp_media(media_id: str, access_token: str) -> str:
    """
    Descarga un archivo multimedia de la API de WhatsApp.
    Retorna la URL relativa local.
    """
    import os
    from django.conf import settings
    import uuid
    import mimetypes
    
    # 1. Obtener URL de descarga
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        media_data = response.json()
        download_url = media_data.get('url')
        mime_type = media_data.get('mime_type')
        
        if not download_url:
            raise Exception("No download URL found in media metadata")
            
        # 2. Descargar el archivo binario
        # Nota: La URL de descarga también requiere auth headers
        file_response = client.get(download_url, headers=headers)
        file_response.raise_for_status()
        
        # 3. Guardar archivo localmente
        ext = mimetypes.guess_extension(mime_type) or '.bin'
        filename = f"{uuid.uuid4().hex}{ext}"
        
        save_dir = os.path.join(settings.MEDIA_ROOT, 'whatsapp')
        os.makedirs(save_dir, exist_ok=True)
        
        file_path = os.path.join(save_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_response.content)
            
        logger.info(f"Media downloaded: {file_path}")
        
        # Retornar URL relativa
        return f"{settings.MEDIA_URL}whatsapp/{filename}"


@shared_task(queue='messages')
def process_status_update(status_update: dict):
    """
    Procesa actualizaciones de estado de mensajes (sent, delivered, read, failed).
    Meta envía estos webhooks cuando el estado del mensaje cambia.
    
    Args:
        status_update: Datos del status update de Meta
    """
    from apps.chat.models import Message
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    try:
        whatsapp_id = status_update.get('id')
        new_status = status_update.get('status')
        
        logger.info(f"Processing status update: {whatsapp_id} -> {new_status}")
        
        message = Message.objects.select_related(
            'conversation'
        ).filter(whatsapp_id=whatsapp_id).first()
        
        if message:
            message.delivery_status = new_status
            message.save(update_fields=['delivery_status', 'updated_at'])
            logger.info(f"Message {whatsapp_id} status updated to: {new_status}")
            
            # Enviar actualización al frontend vía WebSocket
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        'inbox_updates',
                        {
                            'type': 'send_status_update',
                            'status_update': {
                                'message_id': str(message.id),
                                'conversation_id': str(message.conversation.id),
                                'whatsapp_id': whatsapp_id,
                                'delivery_status': new_status,
                            }
                        }
                    )
            except Exception as ws_error:
                logger.error(f"Error sending status via WebSocket: {ws_error}")
        else:
            logger.warning(f"Message not found for status update: {whatsapp_id}. Retrying...")
            # Reintentar por si es una condición de carrera con el guardado del ID
            # Exponential backoff o fixed delay
            raise self.retry(countdown=2, max_retries=5)
            
    except Exception as exc:
        logger.error(f"Error processing status update: {exc}")
        # No reintentar indefinidamente para errores generales, pero sí para la búsqueda
        if "Message not found" in str(exc) or isinstance(exc, self.retry_exception):
             raise exc
        raise self.retry(exc=exc, countdown=60, max_retries=3)
