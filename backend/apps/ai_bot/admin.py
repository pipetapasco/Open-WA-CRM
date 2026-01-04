from django.contrib import admin
from .models import AIConfig


@admin.register(AIConfig)
class AIConfigAdmin(admin.ModelAdmin):
    """Admin para configuración de AI Bot."""
    
    list_display = [
        'account',
        'provider',
        'enabled',
        'max_history_messages',
        'created_at',
        'updated_at',
    ]
    list_filter = ['enabled', 'provider']
    search_fields = ['account__name', 'account__phone_number_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Cuenta', {
            'fields': ('account',)
        }),
        ('Configuración del Bot', {
            'fields': ('enabled', 'provider', 'api_key', 'max_history_messages')
        }),
        ('Prompt del Sistema', {
            'fields': ('system_prompt',),
            'description': 'Define el comportamiento y personalidad del asistente.',
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
