from django.contrib.auth import get_user_model
from django.db import models

from apps.common.fields import EncryptedTextField
from apps.common.models import TimeStampedModel

User = get_user_model()


class WhatsAppAccount(TimeStampedModel):
    """
    Representa una cuenta de WhatsApp Business conectada.
    Cada cuenta puede tener múltiples contactos, conversaciones y plantillas.
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        DISCONNECTED = 'disconnected', 'Disconnected'

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='whatsapp_accounts',
        help_text='Usuario propietario de esta cuenta',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100, help_text='Nombre interno de la cuenta')
    phone_number_id = models.CharField(max_length=50, unique=True, help_text='Phone Number ID de Meta')
    business_account_id = models.CharField(max_length=50, help_text='Business Account ID de Meta')
    access_token = EncryptedTextField(help_text='Permanent Access Token de Meta (Encriptado)')
    webhook_verify_token = EncryptedTextField(
        max_length=100, help_text='Token para verificar webhooks de Meta (Encriptado)'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        verbose_name = 'WhatsApp Account'
        verbose_name_plural = 'WhatsApp Accounts'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.phone_number_id})'


class WhatsAppTemplate(TimeStampedModel):
    """
    Plantillas de mensajes aprobadas por Meta.
    Se sincronizan desde la API de WhatsApp Business.
    """

    class Category(models.TextChoices):
        MARKETING = 'MARKETING', 'Marketing'
        UTILITY = 'UTILITY', 'Utility'
        AUTHENTICATION = 'AUTHENTICATION', 'Authentication'

    class Status(models.TextChoices):
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        PENDING = 'PENDING', 'Pending'

    account = models.ForeignKey(WhatsAppAccount, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField(max_length=255, help_text='Nombre de la plantilla (ej: hello_world)')
    language = models.CharField(max_length=10, help_text='Código de idioma (ej: es, en_US)')
    category = models.CharField(max_length=20, choices=Category.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    components = models.JSONField(
        default=dict, blank=True, help_text='Estructura de la plantilla (header, body, footer, buttons)'
    )

    class Meta:
        verbose_name = 'WhatsApp Template'
        verbose_name_plural = 'WhatsApp Templates'
        unique_together = ['account', 'name', 'language']
        ordering = ['name', 'language']

    def __str__(self):
        return f'{self.name} ({self.language}) - {self.status}'
