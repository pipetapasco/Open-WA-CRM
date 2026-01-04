"""
Base AI Provider - Patrón Strategy para proveedores de IA.

Este módulo define la interfaz abstracta que todos los proveedores
de IA deben implementar, permitiendo intercambiar proveedores
sin modificar la lógica de negocio.
"""
from abc import ABC, abstractmethod
from typing import TypedDict


class ChatMessage(TypedDict):
    """
    Estructura de un mensaje en el historial de chat.
    
    Attributes:
        role: Rol del mensaje ('user' para cliente, 'model' para asistente)
        content: Contenido textual del mensaje
    """
    role: str
    content: str


class BaseAIProvider(ABC):
    """
    Clase base abstracta para proveedores de Inteligencia Artificial.
    
    Implementa el patrón Strategy para desacoplar la lógica de negocio
    de los proveedores específicos de IA (Gemini, OpenAI, etc.).
    
    Attributes:
        api_key: Clave de API del proveedor
        system_prompt: Prompt del sistema que define el comportamiento del asistente
    """
    
    def __init__(self, api_key: str, system_prompt: str = "") -> None:
        """
        Inicializa el proveedor de IA.
        
        Args:
            api_key: Clave de API para autenticación con el proveedor
            system_prompt: Instrucciones iniciales para el modelo
        """
        self.api_key = api_key
        self.system_prompt = system_prompt
    
    @abstractmethod
    def generate_response(self, history: list[ChatMessage]) -> str:
        """
        Genera una respuesta basada en el historial de mensajes.
        
        Este método debe ser implementado por cada proveedor específico.
        Debe manejar la comunicación con la API externa y retornar
        la respuesta generada.
        
        Args:
            history: Lista de mensajes previos en la conversación.
                     Cada mensaje tiene 'role' ('user'/'model') y 'content'.
        
        Returns:
            La respuesta generada por el modelo de IA.
        
        Raises:
            AIProviderError: Si ocurre un error en la comunicación con la API.
        """
        pass


class AIProviderError(Exception):
    """Excepción base para errores de proveedores de IA."""
    
    def __init__(self, message: str, provider: str = "unknown", original_error: Exception | None = None):
        self.provider = provider
        self.original_error = original_error
        super().__init__(f"[{provider}] {message}")
