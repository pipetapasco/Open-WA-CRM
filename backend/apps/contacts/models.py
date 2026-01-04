from django.db import models

from apps.common.models import TimeStampedModel
from apps.config_api.models import WhatsAppAccount


class Contact(TimeStampedModel):
    """
    Representa un contacto/cliente de WhatsApp.
    Cada contacto pertenece a una cuenta de WhatsApp Business específica.
    """

    account = models.ForeignKey(WhatsAppAccount, on_delete=models.CASCADE, related_name='contacts')
    phone_number = models.CharField(
        max_length=20, db_index=True, help_text='Número de teléfono con código de país (ej: 573001234567)'
    )
    name = models.CharField(max_length=255, blank=True, default='', help_text='Nombre del contacto')
    profile_picture_url = models.URLField(
        max_length=500, blank=True, null=True, help_text='URL de la foto de perfil de WhatsApp'
    )
    metadata = models.JSONField(default=dict, blank=True, help_text='Información adicional del contacto')

    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        unique_together = ['account', 'phone_number']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['account', 'phone_number']),
        ]
        ordering = ['name', 'phone_number']

    def __str__(self):
        if self.name:
            return f'{self.name} ({self.phone_number})'
        return self.phone_number
