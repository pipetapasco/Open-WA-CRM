"""
WhatsApp Notification Services.

Este módulo implementa el patrón Service Layer para encapsular
la lógica de negocio relacionada con el envío de notificaciones
de WhatsApp, separándola de las vistas.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from django.utils import timezone

from apps.chat.models import Conversation, Message
from apps.config_api.models import WhatsAppAccount, WhatsAppTemplate
from apps.contacts.models import Contact


class WhatsAppServiceError(Exception):
    pass


class TemplateNotFoundError(WhatsAppServiceError):
    pass


class TemplateRenderError(WhatsAppServiceError):
    pass


class MessageCreationError(WhatsAppServiceError):
    pass


@dataclass(frozen=True)
class TemplateData:
    name: str
    language: str
    components: list[dict[str, Any]] | None = None

    @classmethod
    def from_validated_data(cls, data: dict[str, Any]) -> TemplateData:
        return cls(
            name=data['template_name'], language=data['template_language'], components=data.get('components', [])
        )


@dataclass
class SendTemplateResult:
    success: bool
    message: Message | None = None
    error: str | None = None


class WhatsAppNotificationService:
    def send_template_to_contact(
        self, contact: Contact, account: WhatsAppAccount, template_data: TemplateData
    ) -> SendTemplateResult:
        try:
            conversation = self._get_or_create_conversation(contact, account)

            rendered_body = self._render_template_body(
                account=account,
                template_name=template_data.name,
                template_language=template_data.language,
                components=template_data.components or [],
            )

            message = self._create_message(
                conversation=conversation, template_data=template_data, rendered_body=rendered_body
            )

            self._update_conversation_timestamp(conversation)

            self._enqueue_send_task(message, template_data)

            return SendTemplateResult(success=True, message=message)

        except WhatsAppServiceError as e:
            return SendTemplateResult(success=False, error=str(e))

        except Exception as e:
            return SendTemplateResult(success=False, error=f'Error inesperado: {str(e)}')

    def _get_or_create_conversation(self, contact: Contact, account: WhatsAppAccount) -> Conversation:
        conversation, created = Conversation.objects.get_or_create(contact=contact, account=account)
        return conversation

    def _render_template_body(
        self, account: WhatsAppAccount, template_name: str, template_language: str, components: list[dict[str, Any]]
    ) -> str:
        fallback_body = f'[Template: {template_name}]'

        try:
            template = WhatsAppTemplate.objects.filter(
                account=account, name=template_name, language=template_language, status='APPROVED'
            ).first()

            if not template:
                return fallback_body

            body_component = self._extract_body_component(template.components)
            if not body_component:
                return fallback_body

            body_text = body_component.get('text', '')
            if not body_text:
                return fallback_body

            rendered_text = self._apply_parameters(body_text, components)

            return rendered_text

        except Exception:
            return fallback_body

    def _extract_body_component(self, components: list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any] | None:
        if not components or isinstance(components, dict):
            return None

        return next((c for c in components if c.get('type') == 'BODY'), None)

    def _apply_parameters(self, text: str, components: list[dict[str, Any]]) -> str:
        sent_body = next((c for c in components if c.get('type') == 'body'), None)

        if not sent_body or not sent_body.get('parameters'):
            return text

        params = sent_body['parameters']

        positional_values: list[str] = []
        named_values: dict[str, str] = {}

        for param in params:
            if param.get('type') != 'text':
                continue

            value = param.get('text', '')
            parameter_name = param.get('parameter_name')

            if parameter_name:
                named_values[parameter_name] = value
            else:
                positional_values.append(value)

        for key, value in named_values.items():
            text = text.replace(f'{{{{{key}}}}}', value)

        for index, value in enumerate(positional_values):
            text = text.replace(f'{{{{{index + 1}}}}}', value)

        return text

    def _create_message(self, conversation: Conversation, template_data: TemplateData, rendered_body: str) -> Message:
        try:
            temp_whatsapp_id = f'temp-{uuid.uuid4()}'

            message = Message.objects.create(
                conversation=conversation,
                direction='outgoing',
                message_type='template',
                body=rendered_body,
                metadata={
                    'template_name': template_data.name,
                    'template_language': template_data.language,
                    'components': template_data.components or [],
                },
                delivery_status='sent',
                whatsapp_id=temp_whatsapp_id,
            )

            return message

        except Exception as e:
            raise MessageCreationError(f'Failed to create message: {str(e)}') from e

    def _update_conversation_timestamp(self, conversation: Conversation) -> None:
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])

    def _enqueue_send_task(self, message: Message, template_data: TemplateData) -> None:
        from apps.chat.tasks import send_whatsapp_template

        send_whatsapp_template.delay(
            str(message.id), template_data.name, template_data.language, template_data.components or []
        )


def send_template_to_contact(
    contact: Contact, account: WhatsAppAccount, template_data: TemplateData
) -> SendTemplateResult:
    service = WhatsAppNotificationService()
    return service.send_template_to_contact(contact, account, template_data)
