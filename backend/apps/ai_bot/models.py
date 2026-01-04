from django.db import models
from apps.common.models import TimeStampedModel
from apps.common.fields import EncryptedTextField


class AIProvider(models.TextChoices):
    """Proveedores de IA soportados."""
    GEMINI = 'gemini', 'Google Gemini'
    # Futuros proveedores:
    # OPENAI = 'openai', 'OpenAI GPT'
    # ANTHROPIC = 'anthropic', 'Anthropic Claude'


class AIConfig(TimeStampedModel):
    """
    Configuración de IA para una cuenta de WhatsApp.
    
    Cada cuenta puede tener su propia configuración de IA con
    diferentes proveedores, API keys y prompts del sistema.
    """
    
    account = models.OneToOneField(
        'config_api.WhatsAppAccount',
        on_delete=models.CASCADE,
        related_name='ai_config',
        help_text='Cuenta de WhatsApp asociada'
    )
    enabled = models.BooleanField(
        default=False,
        help_text='Si el bot de IA está activo para esta cuenta'
    )
    provider = models.CharField(
        max_length=50,
        choices=AIProvider.choices,
        default=AIProvider.GEMINI,
        help_text='Proveedor de IA a utilizar'
    )
    api_key = EncryptedTextField(
        help_text='API Key del proveedor (encriptada)'
    )
    system_prompt = models.TextField(
        blank=True,
        default='',
        help_text='Prompt del sistema que define el comportamiento del asistente'
    )
    max_history_messages = models.PositiveIntegerField(
        default=10,
        help_text='Número máximo de mensajes de historial a enviar al modelo'
    )
    
    class Meta:
        verbose_name = 'AI Configuration'
        verbose_name_plural = 'AI Configurations'
    
    def __str__(self):
        status = '✓' if self.enabled else '✗'
        return f'{self.account.name} - {self.get_provider_display()} [{status}]'
