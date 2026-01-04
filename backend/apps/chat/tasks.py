import httpx
from celery import shared_task


@shared_task(bind=True, queue='messages', max_retries=3)
def send_whatsapp_message(self, message_id: str):
    from apps.chat.models import Message

    try:
        message = Message.objects.select_related('conversation__contact', 'conversation__account').get(pk=message_id)

        account = message.conversation.account
        contact = message.conversation.contact

        api_url = f'https://graph.facebook.com/v18.0/{account.phone_number_id}/messages'

        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': contact.phone_number,
            'type': message.message_type,
        }

        if message.message_type == 'text':
            payload['text'] = {'body': message.body}
        elif message.message_type in ['image', 'video', 'audio', 'document', 'sticker']:
            media_id = None

            if message.media_url:
                try:
                    if message.message_type == 'audio':
                        from apps.common.utils import convert_media_for_whatsapp

                        converted_path = convert_media_for_whatsapp(message.media_url)

                        if converted_path != message.media_url:
                            message.media_url = converted_path
                            message.media_url = converted_path
                            message.save(update_fields=['media_url'])

                    if message.message_type == 'audio':
                        from apps.common.utils import get_media_duration

                        duration = get_media_duration(message.media_url)
                        if duration > 0:
                            if not message.metadata:
                                message.metadata = {}
                            message.metadata['duration'] = duration
                            message.save(update_fields=['metadata'])

                    media_id = upload_media_to_meta(message.media_url, account)
                except Exception as e:
                    raise e

            if not media_id:
                raise Exception('Cannot send media message without media_id')

            media_obj = {'id': media_id}

            if message.message_type in ['image', 'video', 'document'] and message.body:
                media_obj['caption'] = message.body

            if message.message_type == 'document':
                import os

                media_obj['filename'] = os.path.basename(message.media_url)

            payload[message.message_type] = media_obj

        headers = {'Authorization': f'Bearer {account.access_token}', 'Content-Type': 'application/json'}

        with httpx.Client(timeout=60.0) as client:
            response = client.post(api_url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            whatsapp_id = data.get('messages', [{}])[0].get('id')

            if whatsapp_id:
                message.whatsapp_id = whatsapp_id
            message.delivery_status = 'sent'
            message.save(update_fields=['whatsapp_id', 'delivery_status', 'updated_at'])

            return {'status': 'sent', 'whatsapp_id': whatsapp_id}
        else:
            message.delivery_status = 'failed'
            message.save(update_fields=['delivery_status', 'updated_at'])
            raise Exception(f'WhatsApp API error: {response.status_code}')

    except Message.DoesNotExist:
        return {'status': 'error', 'message': 'Message not found'}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


def upload_media_to_meta(media_path: str, account) -> str:
    import mimetypes
    import os

    from django.conf import settings

    if media_path.startswith(settings.MEDIA_URL):
        relative_path = media_path[len(settings.MEDIA_URL) :]
        file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    elif media_path.startswith('/'):
        if settings.MEDIA_URL in media_path:
            offset = media_path.find(settings.MEDIA_URL) + len(settings.MEDIA_URL)
            file_path = os.path.join(settings.MEDIA_ROOT, media_path[offset:])
        else:
            file_path = media_path
    else:
        file_path = os.path.join(settings.MEDIA_ROOT, media_path)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f'Media file not found: {file_path}')

    mimetypes.init()
    mime_type, _ = mimetypes.guess_type(file_path)

    if not mime_type:
        if file_path.endswith('.ogg') or file_path.endswith('.opus'):
            mime_type = 'audio/ogg'
        else:
            mime_type = 'application/octet-stream'

    url = f'https://graph.facebook.com/v18.0/{account.phone_number_id}/media'

    headers = {'Authorization': f'Bearer {account.access_token}'}

    data = {'messaging_product': 'whatsapp'}

    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, mime_type)}

        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            return response.json().get('id')
        else:
            raise Exception(f'Media upload failed: {response.status_code} - {response.text}')


@shared_task(bind=True, queue='messages', max_retries=3)
def send_whatsapp_template(self, message_id: str, template_name: str, template_language: str, components: list = None):
    from apps.chat.models import Message

    try:
        message = Message.objects.select_related('conversation__contact', 'conversation__account').get(pk=message_id)

        account = message.conversation.account
        contact = message.conversation.contact

        api_url = f'https://graph.facebook.com/v18.0/{account.phone_number_id}/messages'

        template_payload = {
            'name': template_name,
            'language': {'code': template_language},
        }

        if components:
            template_payload['components'] = components

        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': contact.phone_number,
            'type': 'template',
            'template': template_payload,
        }

        headers = {'Authorization': f'Bearer {account.access_token}', 'Content-Type': 'application/json'}

        with httpx.Client(timeout=30.0) as client:
            response = client.post(api_url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            whatsapp_id = data.get('messages', [{}])[0].get('id')

            if whatsapp_id:
                message.whatsapp_id = whatsapp_id
            message.delivery_status = 'sent'
            message.save(update_fields=['whatsapp_id', 'delivery_status', 'updated_at'])

            return {'status': 'sent', 'whatsapp_id': whatsapp_id}
        else:
            message.delivery_status = 'failed'
            message.save(update_fields=['delivery_status', 'updated_at'])
            raise Exception(f'WhatsApp API error: {response.status_code}')

    except Message.DoesNotExist:
        return {'status': 'error', 'message': 'Message not found'}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, queue='whatsapp')
def process_webhook_payload(self, payload: dict, phone_number_id: str):
    try:
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

        return {'status': 'success'}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(queue='messages')
def process_incoming_message(message: dict, phone_number_id: str):
    from apps.chat.models import Conversation, Message
    from apps.config_api.models import WhatsAppAccount
    from apps.contacts.models import Contact

    try:
        account = WhatsAppAccount.objects.filter(phone_number_id=phone_number_id).first()
        if not account:
            return

        sender_phone = message.get('from')
        contact, created = Contact.objects.get_or_create(
            account=account, phone_number=sender_phone, defaults={'name': sender_phone}
        )

        conversation, _ = Conversation.objects.get_or_create(
            account=account, contact=contact, defaults={'status': 'open'}
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
                except Exception:
                    media_url = None

        Message.objects.create(
            conversation=conversation,
            whatsapp_id=message.get('id'),
            direction='incoming',
            message_type=msg_type,
            body=msg_body,
            media_url=media_url,
            metadata=message,
            delivery_status='delivered',
        )

        from django.utils import timezone

        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])

        try:
            from apps.ai_bot.services import AIBotService

            ai_service = AIBotService(conversation)
            if ai_service.is_enabled():
                from apps.ai_bot.tasks import process_ai_response

                process_ai_response.delay(str(conversation.id))
        except Exception:
            pass

    except Exception:
        raise


def download_whatsapp_media(media_id: str, access_token: str) -> str:
    import mimetypes
    import os
    import uuid

    from django.conf import settings

    url = f'https://graph.facebook.com/v18.0/{media_id}'
    headers = {'Authorization': f'Bearer {access_token}'}

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        media_data = response.json()
        download_url = media_data.get('url')
        mime_type = media_data.get('mime_type')

        if not download_url:
            raise Exception('No download URL found in media metadata')

        file_response = client.get(download_url, headers=headers)
        file_response.raise_for_status()

        ext = mimetypes.guess_extension(mime_type) or '.bin'
        filename = f'{uuid.uuid4().hex}{ext}'

        save_dir = os.path.join(settings.MEDIA_ROOT, 'whatsapp')
        os.makedirs(save_dir, exist_ok=True)

        file_path = os.path.join(save_dir, filename)

        with open(file_path, 'wb') as f:
            f.write(file_response.content)

        return f'{settings.MEDIA_URL}whatsapp/{filename}'


@shared_task(bind=True, queue='messages')
def process_status_update(self, status_update: dict):
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    from apps.chat.models import Message

    try:
        whatsapp_id = status_update.get('id')
        new_status = status_update.get('status')

        message = Message.objects.select_related('conversation').filter(whatsapp_id=whatsapp_id).first()

        if message:
            message.delivery_status = new_status
            message.save(update_fields=['delivery_status', 'updated_at'])

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
                            },
                        },
                    )
            except Exception:
                pass
        else:
            raise self.retry(countdown=2, max_retries=5)

    except Exception as exc:
        if 'Message not found' in str(exc) or isinstance(exc, self.retry_exception):
            raise exc
        raise self.retry(exc=exc, countdown=60, max_retries=3)
