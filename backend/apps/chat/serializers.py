from rest_framework import serializers
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Conversation, Message
from apps.contacts.models import Contact
from apps.config_api.models import WhatsAppAccount


class ContactSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para Contact (usado en conversaciones)."""
    
    class Meta:
        model = Contact
        fields = ['id', 'name', 'phone_number', 'profile_picture_url']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer para mensajes de chat."""
    
    is_from_me = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id',
            'body',
            'message_type',
            'direction',
            'delivery_status',
            'created_at',
            'media_url',
            'is_from_me',
            'metadata',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_is_from_me(self, obj):
        """True si el mensaje fue enviado por nosotros."""
        return obj.direction == 'outgoing'


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer para listar conversaciones con info del contacto."""
    
    contact = ContactSimpleSerializer(read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_id = serializers.UUIDField(source='account.id', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField(read_only=True)
    can_send_free_message = serializers.SerializerMethodField()
    last_incoming_message_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id',
            'contact',
            'account_name',
            'account_id',
            'status',
            'last_message',
            'last_message_at',
            'unread_count',
            'can_send_free_message',
            'last_incoming_message_at',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'last_message_at']
    
    def get_last_message(self, obj):
        """Retorna el cuerpo o tipo del último mensaje."""
        last_msg = obj.messages.order_by('-created_at').first()
        if not last_msg:
            return None
        
        if last_msg.message_type == 'text':
            # Truncar si es muy largo
            return last_msg.body[:100] if last_msg.body else None
        else:
            # Para media, mostrar el tipo
            return f"[{last_msg.message_type.upper()}]"
    
    def get_last_incoming_message_at(self, obj):
        """Retorna la fecha del último mensaje entrante."""
        last_incoming = obj.messages.filter(direction='incoming').order_by('-created_at').first()
        if last_incoming:
            return last_incoming.created_at
        return None
    
    def get_can_send_free_message(self, obj):
        """
        Retorna True si la ventana de 24 horas está abierta.
        La ventana de 24h de WhatsApp se abre cuando el cliente envía un mensaje.
        """
        last_incoming = obj.messages.filter(direction='incoming').order_by('-created_at').first()
        if not last_incoming:
            return False
        
        # La ventana se cierra 24 horas después del último mensaje entrante
        window_end = last_incoming.created_at + timedelta(hours=24)
        return timezone.now() < window_end


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para una conversación individual."""
    
    contact = ContactSimpleSerializer(read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_id = serializers.UUIDField(source='account.id', read_only=True)
    can_send_free_message = serializers.SerializerMethodField()
    last_incoming_message_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id',
            'contact',
            'account_name',
            'account_id',
            'status',
            'last_message_at',
            'can_send_free_message',
            'last_incoming_message_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_message_at']
    
    def get_last_incoming_message_at(self, obj):
        """Retorna la fecha del último mensaje entrante."""
        last_incoming = obj.messages.filter(direction='incoming').order_by('-created_at').first()
        if last_incoming:
            return last_incoming.created_at
        return None
    
    def get_can_send_free_message(self, obj):
        """Retorna True si la ventana de 24 horas está abierta."""
        last_incoming = obj.messages.filter(direction='incoming').order_by('-created_at').first()
        if not last_incoming:
            return False
        
        window_end = last_incoming.created_at + timedelta(hours=24)
        return timezone.now() < window_end


class SendTextMessageSerializer(serializers.Serializer):
    """Serializer para enviar mensajes de texto."""
    
    message = serializers.CharField(max_length=4096, required=True)


class SendTemplateMessageSerializer(serializers.Serializer):
    """Serializer para enviar mensajes de plantilla."""
    
    template_name = serializers.CharField(max_length=255, required=True)
    template_language = serializers.CharField(max_length=10, required=True)
    components = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
        help_text='Lista de componentes con variables (ej: [{"type": "body", "parameters": [...]}])'
    )


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear una nueva conversación."""
    
    contact = serializers.PrimaryKeyRelatedField(queryset=Contact.objects.all())
    account = serializers.PrimaryKeyRelatedField(queryset=WhatsAppAccount.objects.all())
    
    class Meta:
        model = Conversation
        fields = ['id', 'contact', 'account', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']
        validators = []

    def create(self, validated_data):
        conversation, created = Conversation.objects.get_or_create(
            contact=validated_data['contact'],
            account=validated_data['account'],
            defaults=validated_data
        )
        return conversation
