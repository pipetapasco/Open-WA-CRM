from rest_framework import serializers
from .models import WhatsAppAccount, WhatsAppTemplate


class WhatsAppAccountSerializer(serializers.ModelSerializer):
    """
    Serializer para gestionar cuentas de WhatsApp Business.
    Los tokens sensibles son write_only para seguridad.
    """
    
    class Meta:
        model = WhatsAppAccount
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'access_token': {'write_only': True},
            'webhook_verify_token': {'write_only': True},
        }
    
    def to_representation(self, instance):
        """
        Incluye indicadores de si los tokens están configurados
        sin exponer los valores reales.
        """
        data = super().to_representation(instance)
        data['has_access_token'] = bool(instance.access_token)
        data['has_webhook_token'] = bool(instance.webhook_verify_token)
        return data


class WhatsAppTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer para plantillas de WhatsApp.
    """
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = WhatsAppTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
