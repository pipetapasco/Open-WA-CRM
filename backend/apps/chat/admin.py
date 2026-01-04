import json

from django.contrib import admin
from django.utils.html import format_html

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['whatsapp_id', 'direction', 'message_type', 'body', 'media_url', 'delivery_status', 'created_at']
    fields = ['direction', 'message_type', 'body', 'delivery_status', 'created_at']
    ordering = ['created_at']
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['short_id', 'contact', 'account', 'status', 'last_message_at', 'created_at']
    list_filter = ['status', 'account', 'created_at']
    search_fields = ['contact__phone_number', 'contact__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_select_related = ['account', 'contact']
    inlines = [MessageInline]

    fieldsets = (
        ('Conversation Info', {'fields': ('id', 'account', 'contact', 'status')}),
        ('Activity', {'fields': ('last_message_at',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='ID')
    def short_id(self, obj):
        return str(obj.id)[:8] + '...'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'short_whatsapp_id',
        'direction',
        'message_type',
        'delivery_status',
        'conversation_link',
        'created_at',
    ]
    list_filter = ['direction', 'message_type', 'delivery_status', 'created_at']
    search_fields = ['whatsapp_id', 'body']
    readonly_fields = ['id', 'whatsapp_id', 'body', 'metadata_formatted', 'created_at', 'updated_at']
    list_select_related = ['conversation', 'conversation__contact']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Message Info', {'fields': ('id', 'conversation', 'whatsapp_id')}),
        ('Content', {'fields': ('direction', 'message_type', 'body', 'media_url', 'delivery_status')}),
        (
            'Raw Metadata',
            {
                'fields': ('metadata_formatted',),
                'classes': ('collapse',),
                'description': 'Original payload from Meta API',
            },
        ),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='WhatsApp ID')
    def short_whatsapp_id(self, obj):
        if len(obj.whatsapp_id) > 20:
            return obj.whatsapp_id[:20] + '...'
        return obj.whatsapp_id

    @admin.display(description='Conversation')
    def conversation_link(self, obj):
        return format_html(
            '<a href="/admin/chat/conversation/{}/change/">{}</a>',
            obj.conversation.id,
            obj.conversation.contact.phone_number,
        )

    @admin.display(description='Metadata (JSON)')
    def metadata_formatted(self, obj):
        if obj.metadata:
            formatted_json = json.dumps(obj.metadata, indent=2, ensure_ascii=False)
            return format_html(
                '<pre style="margin:0; white-space:pre-wrap; max-height:300px; overflow:auto;">{}</pre>', formatted_json
            )
        return '-'
