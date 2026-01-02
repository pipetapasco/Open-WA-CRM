from django.db import models
from apps.common.models import TimeStampedModel
from apps.config_api.models import WhatsAppAccount
from apps.contacts.models import Contact


class Conversation(TimeStampedModel):
    """
    Hilo de conversación entre un contacto y una cuenta de WhatsApp Business.
    """
    
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        RESOLVED = 'resolved', 'Resolved'
        PENDING = 'pending', 'Pending'
    
    account = models.ForeignKey(
        WhatsAppAccount,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Fecha del último mensaje para ordenar inbox'
    )
    
    class Meta:
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        unique_together = ['account', 'contact']
        indexes = [
            models.Index(fields=['last_message_at']),
            models.Index(fields=['status', 'last_message_at']),
        ]
        ordering = ['-last_message_at']
    
    def __str__(self):
        return f'Conversation with {self.contact} ({self.status})'


class Message(TimeStampedModel):
    """
    Mensaje individual dentro de una conversación.
    Puede ser entrante (del cliente) o saliente (del negocio).
    """
    
    class Direction(models.TextChoices):
        INCOMING = 'incoming', 'Incoming'
        OUTGOING = 'outgoing', 'Outgoing'
    
    class MessageType(models.TextChoices):
        TEXT = 'text', 'Text'
        IMAGE = 'image', 'Image'
        VIDEO = 'video', 'Video'
        AUDIO = 'audio', 'Audio'
        DOCUMENT = 'document', 'Document'
        TEMPLATE = 'template', 'Template'
        INTERACTIVE = 'interactive', 'Interactive'
        STICKER = 'sticker', 'Sticker'
        LOCATION = 'location', 'Location'
        CONTACTS = 'contacts', 'Contacts'
    
    class DeliveryStatus(models.TextChoices):
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        READ = 'read', 'Read'
        FAILED = 'failed', 'Failed'
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    whatsapp_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text='wamid de WhatsApp (identificador único del mensaje)'
    )
    direction = models.CharField(
        max_length=10,
        choices=Direction.choices
    )
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT
    )
    body = models.TextField(
        blank=True,
        null=True,
        help_text='Contenido del mensaje (para mensajes de texto)'
    )
    media_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text='URL del archivo adjunto'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Payload completo del mensaje de Meta'
    )
    delivery_status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.SENT
    )
    
    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['whatsapp_id']),
            models.Index(fields=['conversation', 'created_at']),
        ]
        ordering = ['created_at']
    
    def __str__(self):
        preview = self.body[:50] if self.body else f'[{self.message_type}]'
        return f'{self.direction}: {preview}'
