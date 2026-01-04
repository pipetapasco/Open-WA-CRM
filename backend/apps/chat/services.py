"""
WhatsApp Notification Services.

Este módulo implementa el patrón Service Layer para encapsular
la lógica de negocio relacionada con el envío de notificaciones
de WhatsApp, separándola de las vistas.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from django.utils import timezone

from apps.chat.models import Conversation, Message
from apps.config_api.models import WhatsAppAccount, WhatsAppTemplate
from apps.contacts.models import Contact

logger = logging.getLogger(__name__)


# ==============================================================================
# Excepciones personalizadas
# ==============================================================================

class WhatsAppServiceError(Exception):
    """Excepción base para errores del servicio de WhatsApp."""
    pass


class TemplateNotFoundError(WhatsAppServiceError):
    """Se lanza cuando no se encuentra la plantilla especificada."""
    pass


class TemplateRenderError(WhatsAppServiceError):
    """Se lanza cuando falla el renderizado de la plantilla."""
    pass


class MessageCreationError(WhatsAppServiceError):
    """Se lanza cuando falla la creación del mensaje en la base de datos."""
    pass


# ==============================================================================
# Data Transfer Objects
# ==============================================================================

@dataclass(frozen=True)
class TemplateData:
    """
    DTO que encapsula los datos necesarios para enviar una plantilla.
    
    Attributes:
        name: Nombre de la plantilla (ej: 'hello_world')
        language: Código de idioma (ej: 'es', 'en_US')
        components: Lista de componentes con parámetros (opcional)
    """
    name: str
    language: str
    components: list[dict[str, Any]] | None = None

    @classmethod
    def from_validated_data(cls, data: dict[str, Any]) -> TemplateData:
        """
        Crea una instancia desde los datos validados del serializer.
        
        Args:
            data: Diccionario con los campos validados.
            
        Returns:
            Instancia de TemplateData.
        """
        return cls(
            name=data['template_name'],
            language=data['template_language'],
            components=data.get('components', [])
        )


@dataclass
class SendTemplateResult:
    """
    DTO que representa el resultado del envío de una plantilla.
    
    Attributes:
        success: Si el envío fue exitoso.
        message: El objeto Message creado (si success=True).
        error: Mensaje de error (si success=False).
    """
    success: bool
    message: Message | None = None
    error: str | None = None


# ==============================================================================
# Servicio Principal
# ==============================================================================

class WhatsAppNotificationService:
    """
    Servicio para enviar notificaciones de WhatsApp a contactos.
    
    Encapsula toda la lógica de negocio relacionada con:
    - Búsqueda de plantillas en la base de datos
    - Renderizado del cuerpo del mensaje con variables
    - Creación del registro Message
    - Encolado de tareas Celery para envío asíncrono
    
    Ejemplo de uso:
        >>> service = WhatsAppNotificationService()
        >>> template_data = TemplateData(name='hello_world', language='es')
        >>> result = service.send_template_to_contact(contact, account, template_data)
        >>> if result.success:
        ...     print(f"Mensaje creado: {result.message.id}")
    """

    def send_template_to_contact(
        self,
        contact: Contact,
        account: WhatsAppAccount,
        template_data: TemplateData
    ) -> SendTemplateResult:
        """
        Envía una plantilla de WhatsApp a un contacto específico.
        
        Este método orquesta el flujo completo:
        1. Obtiene o crea la conversación
        2. Busca y renderiza la plantilla
        3. Crea el registro de mensaje
        4. Encola la tarea de Celery
        
        Args:
            contact: El contacto destinatario.
            account: La cuenta de WhatsApp Business a usar.
            template_data: Datos de la plantilla a enviar.
            
        Returns:
            SendTemplateResult con el mensaje creado o el error.
        """
        try:
            # 1. Obtener o crear conversación
            conversation = self._get_or_create_conversation(contact, account)
            
            # 2. Renderizar el cuerpo del mensaje
            rendered_body = self._render_template_body(
                account=account,
                template_name=template_data.name,
                template_language=template_data.language,
                components=template_data.components or []
            )
            
            # 3. Crear el mensaje en la base de datos
            message = self._create_message(
                conversation=conversation,
                template_data=template_data,
                rendered_body=rendered_body
            )
            
            # 4. Actualizar timestamp de la conversación
            self._update_conversation_timestamp(conversation)
            
            # 5. Encolar tarea de Celery para envío asíncrono
            self._enqueue_send_task(message, template_data)
            
            logger.info(
                f"Template '{template_data.name}' enqueued for contact {contact.id}"
            )
            
            return SendTemplateResult(success=True, message=message)
            
        except WhatsAppServiceError as e:
            logger.error(f"Service error sending template to {contact.id}: {e}")
            return SendTemplateResult(success=False, error=str(e))
            
        except Exception as e:
            logger.exception(f"Unexpected error sending template to {contact.id}")
            return SendTemplateResult(
                success=False,
                error=f"Error inesperado: {str(e)}"
            )

    def _get_or_create_conversation(
        self,
        contact: Contact,
        account: WhatsAppAccount
    ) -> Conversation:
        """
        Obtiene o crea una conversación entre el contacto y la cuenta.
        
        Args:
            contact: El contacto participante.
            account: La cuenta de WhatsApp.
            
        Returns:
            La conversación existente o recién creada.
        """
        conversation, created = Conversation.objects.get_or_create(
            contact=contact,
            account=account
        )
        if created:
            logger.debug(f"Created new conversation for contact {contact.id}")
        return conversation

    def _render_template_body(
        self,
        account: WhatsAppAccount,
        template_name: str,
        template_language: str,
        components: list[dict[str, Any]]
    ) -> str:
        """
        Renderiza el cuerpo de la plantilla reemplazando las variables.
        
        Soporta dos tipos de variables:
        - Posicionales: {{1}}, {{2}}, etc.
        - Nombradas: {{nombre}}, {{fecha}}, etc.
        
        Args:
            account: La cuenta de WhatsApp para buscar la plantilla.
            template_name: Nombre de la plantilla.
            template_language: Código de idioma de la plantilla.
            components: Lista de componentes con parámetros.
            
        Returns:
            El texto renderizado o un placeholder si no se encuentra.
        """
        # Valor por defecto si no se puede renderizar
        fallback_body = f"[Template: {template_name}]"
        
        try:
            # 1. Buscar la plantilla en la base de datos
            template = WhatsAppTemplate.objects.filter(
                account=account,
                name=template_name,
                language=template_language,
                status='APPROVED'
            ).first()
            
            if not template:
                logger.warning(
                    f"Template '{template_name}' ({template_language}) "
                    f"not found or not approved for account {account.id}"
                )
                return fallback_body
            
            # 2. Extraer el componente BODY de la plantilla
            body_component = self._extract_body_component(template.components)
            if not body_component:
                logger.warning(f"No BODY component in template '{template_name}'")
                return fallback_body
            
            body_text = body_component.get('text', '')
            if not body_text:
                return fallback_body
            
            # 3. Extraer y aplicar parámetros
            rendered_text = self._apply_parameters(body_text, components)
            
            return rendered_text
            
        except Exception as e:
            logger.error(f"Error rendering template body: {e}")
            return fallback_body

    def _extract_body_component(
        self,
        components: list[dict[str, Any]] | dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Extrae el componente BODY de la lista de componentes de una plantilla.
        
        Args:
            components: Lista de componentes de la plantilla.
            
        Returns:
            El componente BODY o None si no existe.
        """
        # Manejar caso donde components es dict vacío o None
        if not components or isinstance(components, dict):
            return None
            
        return next(
            (c for c in components if c.get('type') == 'BODY'),
            None
        )

    def _apply_parameters(
        self,
        text: str,
        components: list[dict[str, Any]]
    ) -> str:
        """
        Aplica los parámetros al texto de la plantilla.
        
        Procesa tanto parámetros posicionales ({{1}}, {{2}}) como
        parámetros nombrados ({{nombre}}, {{key}}).
        
        Args:
            text: El texto original con placeholders.
            components: Lista de componentes enviados con parámetros.
            
        Returns:
            El texto con las variables reemplazadas.
        """
        # Buscar el componente body en los parámetros enviados
        sent_body = next(
            (c for c in components if c.get('type') == 'body'),
            None
        )
        
        if not sent_body or not sent_body.get('parameters'):
            return text
        
        params = sent_body['parameters']
        
        # Separar parámetros posicionales y nombrados
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
        
        # Aplicar reemplazos nombrados: {{key}} -> value
        for key, value in named_values.items():
            text = text.replace(f"{{{{{key}}}}}", value)
        
        # Aplicar reemplazos posicionales: {{1}}, {{2}}, etc.
        for index, value in enumerate(positional_values):
            text = text.replace(f"{{{{{index + 1}}}}}", value)
        
        return text

    def _create_message(
        self,
        conversation: Conversation,
        template_data: TemplateData,
        rendered_body: str
    ) -> Message:
        """
        Crea el registro de mensaje en la base de datos.
        
        Genera un ID temporal que será actualizado por la tarea
        de Celery cuando Meta devuelva el ID real de WhatsApp.
        
        Args:
            conversation: La conversación asociada.
            template_data: Datos de la plantilla.
            rendered_body: El cuerpo renderizado del mensaje.
            
        Returns:
            El objeto Message creado.
            
        Raises:
            MessageCreationError: Si falla la creación del mensaje.
        """
        try:
            # ID temporal que se actualizará con el ID real de WhatsApp
            temp_whatsapp_id = f"temp-{uuid.uuid4()}"
            
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
                whatsapp_id=temp_whatsapp_id
            )
            
            return message
            
        except Exception as e:
            raise MessageCreationError(
                f"Failed to create message: {str(e)}"
            ) from e

    def _update_conversation_timestamp(self, conversation: Conversation) -> None:
        """
        Actualiza el timestamp del último mensaje de la conversación.
        
        Args:
            conversation: La conversación a actualizar.
        """
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])

    def _enqueue_send_task(
        self,
        message: Message,
        template_data: TemplateData
    ) -> None:
        """
        Encola la tarea de Celery para enviar el mensaje a WhatsApp.
        
        Args:
            message: El mensaje a enviar.
            template_data: Datos de la plantilla.
        """
        from apps.chat.tasks import send_whatsapp_template
        
        send_whatsapp_template.delay(
            str(message.id),
            template_data.name,
            template_data.language,
            template_data.components or []
        )


# ==============================================================================
# Función de conveniencia
# ==============================================================================

def send_template_to_contact(
    contact: Contact,
    account: WhatsAppAccount,
    template_data: TemplateData
) -> SendTemplateResult:
    """
    Función de conveniencia para enviar una plantilla sin instanciar el servicio.
    
    Args:
        contact: El contacto destinatario.
        account: La cuenta de WhatsApp Business.
        template_data: Datos de la plantilla.
        
    Returns:
        SendTemplateResult con el resultado de la operación.
        
    Example:
        >>> from apps.chat.services import send_template_to_contact, TemplateData
        >>> result = send_template_to_contact(
        ...     contact=my_contact,
        ...     account=my_account,
        ...     template_data=TemplateData(name='hello', language='es')
        ... )
    """
    service = WhatsAppNotificationService()
    return service.send_template_to_contact(contact, account, template_data)
