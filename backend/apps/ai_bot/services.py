"""
AI Bot Service Layer.

Este módulo implementa el patrón Service Layer para encapsular
la lógica de negocio del bot de IA, incluyendo la selección
del proveedor correcto y la gestión del historial de mensajes.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .models import AIConfig, AIProvider
from .providers import BaseAIProvider, ChatMessage, GeminiProvider
from .providers.base import AIProviderError

if TYPE_CHECKING:
    from apps.chat.models import Conversation, Message


logger = logging.getLogger(__name__)


class AIBotServiceError(Exception):
    """Excepción base para errores del servicio de AI Bot."""
    pass


class AIBotService:
    """
    Servicio principal para gestionar respuestas de IA en conversaciones.
    
    Este servicio orquesta el flujo completo:
    1. Verificar si la IA está habilitada para la cuenta
    2. Obtener el historial de mensajes
    3. Instanciar el proveedor correcto (Gemini, etc.)
    4. Generar y retornar la respuesta
    
    Attributes:
        conversation: La conversación activa
        ai_config: Configuración de IA de la cuenta (si existe)
    """
    
    # Registro de proveedores disponibles
    PROVIDERS: dict[str, type[BaseAIProvider]] = {
        AIProvider.GEMINI: GeminiProvider,
        # Futuros proveedores:
        # AIProvider.OPENAI: OpenAIProvider,
        # AIProvider.ANTHROPIC: AnthropicProvider,
    }
    
    def __init__(self, conversation: Conversation) -> None:
        """
        Inicializa el servicio para una conversación específica.
        
        Args:
            conversation: La conversación para la cual generar respuestas.
        """
        self.conversation = conversation
        self._ai_config: AIConfig | None = None
        self._provider: BaseAIProvider | None = None
        self._config_loaded = False
    
    @property
    def ai_config(self) -> AIConfig | None:
        """
        Obtiene la configuración de IA de la cuenta.
        
        Returns:
            AIConfig si existe, None en caso contrario.
        """
        if not self._config_loaded:
            self._load_config()
        return self._ai_config
    
    def _load_config(self) -> None:
        """Carga la configuración de IA desde la base de datos."""
        try:
            self._ai_config = AIConfig.objects.select_related('account').get(
                account=self.conversation.account
            )
        except AIConfig.DoesNotExist:
            self._ai_config = None
        finally:
            self._config_loaded = True
    
    def is_enabled(self) -> bool:
        """
        Verifica si la IA está habilitada para esta conversación.
        
        Returns:
            True si hay configuración activa y habilitada, False en caso contrario.
        """
        config = self.ai_config
        if config is None:
            return False
        return config.enabled and bool(config.api_key)
    
    def get_response(self) -> str | None:
        """
        Obtiene una respuesta de IA para la conversación actual.
        
        Este método realiza el flujo completo:
        1. Verifica que la IA está habilitada
        2. Obtiene el historial de mensajes
        3. Llama al proveedor para generar respuesta
        
        Returns:
            Respuesta generada por la IA, o None si hay error o no está habilitada.
        
        Raises:
            AIBotServiceError: Si la IA no está habilitada o hay error en el proceso.
        """
        if not self.is_enabled():
            logger.debug(f"AI not enabled for account {self.conversation.account_id}")
            return None
        
        try:
            # Obtener historial de mensajes
            history = self._get_history()
            
            if not history:
                logger.warning("No messages in history, skipping AI response")
                return None
            
            # Obtener proveedor e instanciar
            provider = self._get_provider()
            
            # Generar respuesta
            logger.info(
                f"Generating AI response for conversation {self.conversation.id} "
                f"using {self.ai_config.get_provider_display()}"
            )
            
            response = provider.generate_response(history)
            
            return response
            
        except AIProviderError as e:
            logger.error(f"AI provider error: {e}")
            raise AIBotServiceError(f"Provider error: {e}") from e
            
        except Exception as e:
            logger.exception(f"Unexpected error generating AI response: {e}")
            raise AIBotServiceError(f"Failed to generate response: {e}") from e
    
    def _get_history(self) -> list[ChatMessage]:
        """
        Obtiene el historial de mensajes para contexto del modelo.
        
        Mapea los mensajes de la BD al formato ChatMessage:
        - direction='incoming' -> role='user'
        - direction='outgoing' -> role='model'
        
        Returns:
            Lista de ChatMessage con el historial reciente.
        """
        from apps.chat.models import Message
        
        limit = self.ai_config.max_history_messages if self.ai_config else 10
        
        # Obtener los últimos N mensajes de texto ordenados cronológicamente
        messages = Message.objects.filter(
            conversation=self.conversation,
            message_type='text',  # Solo mensajes de texto para el contexto
        ).order_by('-created_at')[:limit]
        
        # Convertir a lista y revertir para orden cronológico
        messages_list = list(messages)
        messages_list.reverse()
        
        history: list[ChatMessage] = []
        
        for msg in messages_list:
            # Mapear direction a role
            if msg.direction == 'incoming':
                role = 'user'
            else:
                role = 'model'
            
            if msg.body:
                history.append(ChatMessage(
                    role=role,
                    content=msg.body
                ))
        
        return history
    
    def _get_provider(self) -> BaseAIProvider:
        """
        Obtiene la instancia del proveedor de IA configurado.
        
        Returns:
            Instancia del proveedor configurado.
        
        Raises:
            AIBotServiceError: Si el proveedor no está soportado.
        """
        if self._provider is not None:
            return self._provider
        
        config = self.ai_config
        if config is None:
            raise AIBotServiceError("No AI configuration found")
        
        provider_class = self.PROVIDERS.get(config.provider)
        
        if provider_class is None:
            raise AIBotServiceError(f"Unsupported provider: {config.provider}")
        
        self._provider = provider_class(
            api_key=config.api_key,
            system_prompt=config.system_prompt
        )
        
        return self._provider
