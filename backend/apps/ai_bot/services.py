"""
AI Bot Service Layer.

Este módulo implementa el patrón Service Layer para encapsular
la lógica de negocio del bot de IA, incluyendo la selección
del proveedor correcto y la gestión del historial de mensajes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import AIConfig, AIProvider
from .providers import BaseAIProvider, ChatMessage, GeminiProvider
from .providers.base import AIProviderError

if TYPE_CHECKING:
    from apps.chat.models import Conversation


class AIBotServiceError(Exception):
    pass


class AIBotService:
    PROVIDERS: dict[str, type[BaseAIProvider]] = {
        AIProvider.GEMINI: GeminiProvider,
    }

    def __init__(self, conversation: Conversation) -> None:
        self.conversation = conversation
        self._ai_config: AIConfig | None = None
        self._provider: BaseAIProvider | None = None
        self._config_loaded = False

    @property
    def ai_config(self) -> AIConfig | None:
        if not self._config_loaded:
            self._load_config()
        return self._ai_config

    def _load_config(self) -> None:
        try:
            self._ai_config = AIConfig.objects.select_related('account').get(account=self.conversation.account)
        except AIConfig.DoesNotExist:
            self._ai_config = None
        finally:
            self._config_loaded = True

    def is_enabled(self) -> bool:
        config = self.ai_config
        if config is None:
            return False
        return config.enabled and bool(config.api_key)

    def get_response(self) -> str | None:
        if not self.is_enabled():
            return None

        try:
            history = self._get_history()

            if not history:
                return None

            provider = self._get_provider()

            response = provider.generate_response(history)

            return response

        except AIProviderError as e:
            raise AIBotServiceError(f'Provider error: {e}') from e

        except Exception as e:
            raise AIBotServiceError(f'Failed to generate response: {e}') from e

    def _get_history(self) -> list[ChatMessage]:
        from apps.chat.models import Message

        limit = self.ai_config.max_history_messages if self.ai_config else 10

        messages = Message.objects.filter(
            conversation=self.conversation,
            message_type='text',
        ).order_by('-created_at')[:limit]

        messages_list = list(messages)
        messages_list.reverse()

        history: list[ChatMessage] = []

        for msg in messages_list:
            if msg.direction == 'incoming':
                role = 'user'
            else:
                role = 'model'

            if msg.body:
                history.append(ChatMessage(role=role, content=msg.body))

        return history

    def _get_provider(self) -> BaseAIProvider:
        if self._provider is not None:
            return self._provider

        config = self.ai_config
        if config is None:
            raise AIBotServiceError('No AI configuration found')

        provider_class = self.PROVIDERS.get(config.provider)

        if provider_class is None:
            raise AIBotServiceError(f'Unsupported provider: {config.provider}')

        self._provider = provider_class(api_key=config.api_key, system_prompt=config.system_prompt)

        return self._provider
