import json

from django.contrib import admin
from django.utils.html import format_html

from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'name', 'account', 'created_at']
    list_filter = ['account', 'created_at']
    search_fields = ['phone_number', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'metadata_formatted']
    list_select_related = ['account']

    fieldsets = (
        ('Contact Info', {'fields': ('id', 'account', 'phone_number', 'name', 'profile_picture_url')}),
        ('Metadata', {'fields': ('metadata_formatted',), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Metadata (JSON)')
    def metadata_formatted(self, obj):
        if obj.metadata:
            formatted_json = json.dumps(obj.metadata, indent=2, ensure_ascii=False)
            return format_html('<pre style="margin:0; white-space:pre-wrap;">{}</pre>', formatted_json)
        return '-'
