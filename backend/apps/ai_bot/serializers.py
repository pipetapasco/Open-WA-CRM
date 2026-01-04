from rest_framework import serializers
from .models import AIConfig
from apps.config_api.models import WhatsAppAccount

class AIConfigSerializer(serializers.ModelSerializer):
    """
    Serializer para configuración de AI.
    Permite leer y actualizar la configuración.
    La API key es write_only por seguridad.
    """
    
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = AIConfig
        fields = [
            'id', 'account', 'account_name', 'enabled', 'provider', 
            'api_key', 'system_prompt', 'max_history_messages',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True},
        }
    
    def __init__(self, *args, **kwargs):
        """
        Restringir la selección de cuentas a las que pertenecen al usuario.
        """
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            self.fields['account'].queryset = WhatsAppAccount.objects.filter(owner=request.user)
            
    def to_representation(self, instance):
        """
        Incluye indicador de si la API key está configurada.
        """
        data = super().to_representation(instance)
        # Indicator field so frontend knows a key is set without seeing it
        data['has_api_key'] = bool(instance.api_key)
        return data
