from django.contrib import admin

from .models import WhatsAppAccount, WhatsAppTemplate


@admin.register(WhatsAppAccount)
class WhatsAppAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number_id', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'phone_number_id', 'business_account_id']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Account Info', {'fields': ('id', 'name', 'status')}),
        (
            'Meta Configuration',
            {'fields': ('phone_number_id', 'business_account_id', 'access_token', 'webhook_verify_token')},
        ),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(WhatsAppTemplate)
class WhatsAppTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'language', 'category', 'status', 'account', 'created_at']
    list_filter = ['category', 'status', 'account']
    search_fields = ['name', 'language']
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_select_related = ['account']

    fieldsets = (
        ('Template Info', {'fields': ('id', 'account', 'name', 'language')}),
        ('Status', {'fields': ('category', 'status')}),
        ('Structure', {'fields': ('components',), 'description': 'Template components from Meta API'}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
