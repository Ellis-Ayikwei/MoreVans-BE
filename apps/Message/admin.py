from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Message, ChatRoom, ChatMessage, ChatMessageRead


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "request",
        "sender",
        "receiver",
        "content_preview",
        "message_type",
        "read",
        "created_at",
    )
    list_filter = ("message_type", "read", "created_at")
    search_fields = ("sender__username", "receiver__username", "content")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "message_type")

    def content_preview(self, obj):
        """Show a preview of the message content"""
        if obj.content:
            return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
        elif obj.attachment:
            return f"[Attachment: {obj.attachment_name}]"
        return "[No content]"

    content_preview.short_description = "Content Preview"


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('created_at', 'sender', 'message_type')
    fields = ('sender', 'content', 'message_type', 'created_at')
    ordering = ('-created_at',)
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name_or_type',
        'room_type',
        'participants_count',
        'related_object_info',
        'is_active',
        'last_message_at',
        'created_at',
    )
    list_filter = ('room_type', 'is_active', 'created_at', 'last_message_at')
    search_fields = ('name', 'participants__username')
    readonly_fields = ('created_at', 'updated_at', 'last_message_at')
    filter_horizontal = ('participants',)
    inlines = [ChatMessageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'room_type', 'is_active', 'is_private')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id'),
            'description': 'The object this chat room is associated with (Request, Job, Bid, etc.)'
        }),
        ('Participants', {
            'fields': ('participants',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_message_at'),
            'classes': ('collapse',)
        }),
    )

    def name_or_type(self, obj):
        """Display room name or type"""
        return obj.name if obj.name else obj.get_room_type_display()
    name_or_type.short_description = 'Name/Type'

    def participants_count(self, obj):
        """Display number of participants"""
        count = obj.participants.count()
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if count > 1 else 'orange',
            count
        )
    participants_count.short_description = 'Participants'

    def related_object_info(self, obj):
        """Display information about the related object"""
        if obj.related_object:
            if hasattr(obj.related_object, '_meta'):
                model_name = obj.related_object._meta.verbose_name
                if hasattr(obj.related_object, 'get_absolute_url'):
                    url = obj.related_object.get_absolute_url()
                    return format_html(
                        '<a href="{}" target="_blank">{}: {}</a>',
                        url, model_name, str(obj.related_object)
                    )
                else:
                    return f"{model_name}: {str(obj.related_object)}"
        return "No related object"
    related_object_info.short_description = 'Related Object'

    def get_queryset(self, request):
        """Optimize queryset with prefetch_related"""
        return super().get_queryset(request).prefetch_related(
            'participants', 'content_type'
        ).select_related('content_type')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'chat_room_link',
        'sender_link',
        'content_preview',
        'message_type',
        'read_count',
        'has_attachment',
        'created_at',
    )
    list_filter = ('message_type', 'created_at', 'chat_room__room_type')
    search_fields = ('content', 'sender__username', 'chat_room__name')
    readonly_fields = (
        'created_at', 'updated_at', 'message_type', 
        'attachment_name', 'attachment_size', 'attachment_type'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Message Information', {
            'fields': ('chat_room', 'sender', 'content', 'message_type')
        }),
        ('Reply Information', {
            'fields': ('reply_to',),
            'classes': ('collapse',)
        }),
        ('Attachment Information', {
            'fields': ('attachment', 'attachment_name', 'attachment_size', 'attachment_type'),
            'classes': ('collapse',)
        }),
        ('System Data', {
            'fields': ('system_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def chat_room_link(self, obj):
        """Create a link to the chat room admin page"""
        url = reverse('admin:Message_chatroom_change', args=[obj.chat_room.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.chat_room))
    chat_room_link.short_description = 'Chat Room'

    def sender_link(self, obj):
        """Create a link to the sender's user admin page"""
        url = reverse('admin:User_user_change', args=[obj.sender.id])
        return format_html('<a href="{}">{}</a>', url, obj.sender.username)
    sender_link.short_description = 'Sender'

    def content_preview(self, obj):
        """Show a preview of the message content"""
        if obj.content:
            content = obj.content[:60] + "..." if len(obj.content) > 60 else obj.content
            return format_html('<span title="{}">{}</span>', obj.content, content)
        elif obj.attachment:
            return format_html(
                '<span style="color: blue;">[Attachment: {}]</span>',
                obj.attachment_name or 'Unknown'
            )
        return format_html('<span style="color: gray;">[System Message]</span>')
    content_preview.short_description = 'Content'

    def read_count(self, obj):
        """Display read count"""
        count = obj.read_by.count()
        total_participants = obj.chat_room.participants.count() - 1  # Exclude sender
        if total_participants > 0:
            color = 'green' if count == total_participants else 'orange'
            return format_html(
                '<span style="color: {};">{}/{}</span>',
                color, count, total_participants
            )
        return format_html('<span style="color: gray;">0/0</span>')
    read_count.short_description = 'Read'

    def has_attachment(self, obj):
        """Display if message has attachment"""
        if obj.attachment:
            return format_html(
                '<span style="color: green;">✓</span>'
            )
        return format_html('<span style="color: gray;">✗</span>')
    has_attachment.short_description = 'Attachment'

    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related(
            'chat_room', 'sender', 'reply_to__sender'
        ).prefetch_related('read_by')


@admin.register(ChatMessageRead)
class ChatMessageReadAdmin(admin.ModelAdmin):
    list_display = ('message_preview', 'user_link', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('message__content', 'user__username')
    readonly_fields = ('read_at',)
    ordering = ('-read_at',)

    def message_preview(self, obj):
        """Show a preview of the message"""
        content = obj.message.content
        if content:
            preview = content[:40] + "..." if len(content) > 40 else content
            return format_html('<span title="{}">{}</span>', content, preview)
        return "[No content]"
    message_preview.short_description = 'Message'

    def user_link(self, obj):
        """Create a link to the user admin page"""
        url = reverse('admin:User_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('message', 'user')


# Admin actions
@admin.action(description='Mark selected chat rooms as active')
def make_active(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description='Mark selected chat rooms as inactive')
def make_inactive(modeladmin, request, queryset):
    queryset.update(is_active=False)


# Add actions to ChatRoomAdmin
ChatRoomAdmin.actions = [make_active, make_inactive]


# Custom admin site configuration
admin.site.site_header = "MoreVans Chat Administration"
admin.site.site_title = "MoreVans Chat Admin"
admin.site.index_title = "Welcome to MoreVans Chat Administration"
