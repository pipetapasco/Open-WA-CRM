from rest_framework import serializers

from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Contact.
    Incluye un campo calculado para contar conversaciones.
    """

    conversations_count = serializers.IntegerField(read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = Contact
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
