from django.contrib import admin
from .models import (
    Conversation, ConversationParticipant, 
    ChatMessage, MessageReaction, MessageRead
)


class ConversationParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 0
    fields = ['user', 'role', 'is_active', 'joined_at', 'left_at']
    readonly_fields = ['joined_at', 'left_at']


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    fields = ['sender', 'content', 'message_type', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['title', 'conversation_type', 'is_active', 'is_archived', 'created_at']
    list_filter = ['conversation_type', 'is_active', 'is_archived', 'created_at']
    search_fields = ['title', 'id']
    inlines = [ConversationParticipantInline, ChatMessageInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'conversation_type', 'is_active', 'is_archived')
        }),
        ('Linked Object', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('allow_attachments', 'max_attachment_size')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'conversation', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__username', 'user__email', 'conversation__title']
    readonly_fields = ['joined_at', 'left_at', 'last_read_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'conversation', 'message_type', 'is_edited', 'is_deleted', 'created_at']
    list_filter = ['message_type', 'is_edited', 'is_deleted', 'created_at']
    search_fields = ['sender__username', 'content', 'conversation__title']
    readonly_fields = ['created_at', 'updated_at', 'edited_at', 'deleted_at']
    
    fieldsets = (
        (None, {
            'fields': ('conversation', 'sender', 'content', 'message_type')
        }),
        ('Attachment', {
            'fields': ('attachment', 'attachment_name', 'attachment_size', 'attachment_type'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_edited', 'edited_at', 'is_deleted', 'deleted_at', 'reply_to')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'emoji', 'created_at']
    list_filter = ['emoji', 'created_at']
    search_fields = ['user__username', 'message__content']
    readonly_fields = ['created_at']


@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'read_at']
    list_filter = ['read_at']
    search_fields = ['user__username', 'message__content']
    readonly_fields = ['read_at']