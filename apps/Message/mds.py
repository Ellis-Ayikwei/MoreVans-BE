# models.py

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
import uuid

class TimeStampedModel(models.Model):
    """Base model with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Conversation(TimeStampedModel):
    """Model representing a chat conversation between users"""
    CONVERSATION_TYPES = [
        ('booking_chat', 'Booking Chat'),
        ('support_chat', 'Support Chat'),
        ('internal_chat', 'Internal Chat'),
        ('broadcast', 'Broadcast Message'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True, null=True)
    conversation_type = models.CharField(max_length=20, choices=CONVERSATION_TYPES)
    last_message_preview = models.CharField(max_length=255, blank=True, null=True)
    last_message_sent_at = models.DateTimeField(null=True, blank=True)
    booking = models.ForeignKey('booking.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['updated_at']), 
            models.Index(fields=['conversation_type']),
            models.Index(fields=['booking']),
        ]
    
    def __str__(self):
        return f"{self.title or 'Untitled'} ({self.conversation_type})"
    
    def get_participants(self):
        """Returns all active participants in this conversation"""
        return self.conversation_participants.filter(is_active=True)
    
    def add_participant(self, user, role='member'):
        """Add a participant to the conversation"""
        return ConversationParticipant.objects.create(
            conversation=self,
            user=user,
            role=role
        )
    
    def update_last_message(self, message_content, sent_at):
        """Update last message information"""
        preview = message_content
        if len(preview) > 50:
            preview = preview[:47] + "..."
            
        self.last_message_preview = preview
        self.last_message_sent_at = sent_at
        self.save(update_fields=['last_message_preview', 'last_message_sent_at', 'updated_at'])


class ConversationParticipant(TimeStampedModel):
    """Model representing a user's participation in a conversation"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('member', 'Member'),
        ('admin', 'Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='conversation_participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_participations')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(default=timezone.now)
    left_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    unread_count = models.PositiveIntegerField(default=0)
    last_read_message = models.ForeignKey('Message', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    is_muted = models.BooleanField(default=False)
    muted_until = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('conversation', 'user')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['conversation', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user} in {self.conversation}"
    
    def mark_as_read(self, message=None):
        """Mark all messages as read up to the given message"""
        self.unread_count = 0
        if message:
            self.last_read_message = message
        self.save(update_fields=['unread_count', 'last_read_message', 'updated_at'])
    
    def increment_unread(self):
        """Increment unread count for this participant"""
        self.unread_count = models.F('unread_count') + 1
        self.save(update_fields=['unread_count', 'updated_at'])
    
    def leave_conversation(self):
        """Mark participant as having left the conversation"""
        self.is_active = False
        self.left_at = timezone.now()
        self.save(update_fields=['is_active', 'left_at', 'updated_at'])


class Message(TimeStampedModel):
    """Model representing an individual message in a conversation"""
    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('image', 'Image'),
        ('file', 'File'),
        ('location', 'Location'),
        ('system', 'System Message'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    metadata = JSONField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['conversation']),
            models.Index(fields=['created_at']),
            models.Index(fields=['sender']),
        ]
    
    def __str__(self):
        return f"Message by {self.sender} in {self.conversation}"
    
    def edit(self, new_content):
        """Edit message content"""
        self.content = new_content
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save(update_fields=['content', 'is_edited', 'edited_at', 'updated_at'])
    
    def soft_delete(self):
        """Soft delete the message"""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])
    
    def mark_read_by(self, user):
        """Mark this message as read by a user"""
        MessageStatus.objects.update_or_create(
            message=self,
            user=user,
            defaults={'status': 'read', 'updated_at': timezone.now()}
        )
    
    def mark_delivered_to(self, user):
        """Mark this message as delivered to a user"""
        MessageStatus.objects.update_or_create(
            message=self,
            user=user,
            defaults={'status': 'delivered', 'updated_at': timezone.now()}
        )
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and not self.is_deleted:
            # Update conversation's last message info
            self.conversation.update_last_message(
                self._get_preview_text(),
                self.created_at
            )
            
            # Increment unread count for all participants except sender
            if self.sender:
                ConversationParticipant.objects.filter(
                    conversation=self.conversation,
                    is_active=True
                ).exclude(
                    user=self.sender
                ).update(
                    unread_count=models.F('unread_count') + 1
                )
    
    def _get_preview_text(self):
        """Generate preview text based on message type"""
        if self.message_type == 'text':
            return self.content or ''
        elif self.message_type == 'image':
            return '📷 Photo'
        elif self.message_type == 'file':
            return '📎 File'
        elif self.message_type == 'location':
            return '📍 Location'
        else:
            return 'New message'


class MessageAttachment(TimeStampedModel):
    """Model for files attached to messages"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)  # MIME type
    file_size = models.BigIntegerField()  # Size in bytes
    file_url = models.URLField(max_length=500)
    thumbnail_url = models.URLField(max_length=500, blank=True, null=True)
    is_image = models.BooleanField(default=False)
    width = models.PositiveIntegerField(null=True, blank=True)  # For images
    height = models.PositiveIntegerField(null=True, blank=True)  # For images
    
    class Meta:
        indexes = [
            models.Index(fields=['message']),
            models.Index(fields=['file_type']),
        ]
    
    def __str__(self):
        return f"Attachment: {self.file_name}"


class MessageStatus(TimeStampedModel):
    """Model tracking delivery and read status of messages"""
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='statuses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    class Meta:
        unique_together = ('message', 'user')
        indexes = [
            models.Index(fields=['message']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"Message {self.message.id} is {self.status} by {self.user}"


class TypingIndicator(models.Model):
    """Model for tracking who's currently typing in a conversation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='typing_indicators')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        unique_together = ('conversation', 'user')
        indexes = [
            models.Index(fields=['conversation']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user} typing in {self.conversation}"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Default expiration is 10 seconds from now
            self.expires_at = timezone.now() + timezone.timedelta(seconds=10)
        super().save(*args, **kwargs)

    @classmethod
    def set_typing(cls, conversation, user):
        """Set or extend a user's typing status"""
        expires_at = timezone.now() + timezone.timedelta(seconds=10)
        cls.objects.update_or_create(
            conversation=conversation, 
            user=user,
            defaults={'expires_at': expires_at}
        )


class MessageReaction(TimeStampedModel):
    """Model for emoji reactions to messages"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=50)  # Emoji code or name
    
    class Meta:
        unique_together = ('message', 'user', 'reaction_type')
        indexes = [
            models.Index(fields=['message']),
            models.Index(fields=['reaction_type']),
        ]
    
    def __str__(self):
        return f"{self.user} reacted with {self.reaction_type} to message {self.message.id}"
    
    
    ......
    
    
    
    # admin.py

from django.contrib import admin
from .models import (
    Conversation, 
    ConversationParticipant, 
    Message, 
    MessageAttachment, 
    MessageStatus, 
    TypingIndicator,
    MessageReaction
)

class ConversationParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 0

class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0

class MessageStatusInline(admin.TabularInline):
    model = MessageStatus
    extra = 0

class MessageReactionInline(admin.TabularInline):
    model = MessageReaction
    extra = 0

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'conversation_type', 'last_message_sent_at', 'is_active')
    list_filter = ('conversation_type', 'is_active', 'created_at')
    search_fields = ('title', 'id')
    inlines = [ConversationParticipantInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'message_type', 'created_at', 'is_edited', 'is_deleted')
    list_filter = ('message_type', 'is_edited', 'is_deleted', 'created_at')
    search_fields = ('content', 'conversation__title', 'sender__username', 'id')
    inlines = [MessageAttachmentInline, MessageStatusInline, MessageReactionInline]

@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'conversation', 'role', 'unread_count', 'is_active')
    list_filter = ('role', 'is_active', 'joined_at')
    search_fields = ('user__username', 'conversation__title')

@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'file_name', 'file_type', 'file_size', 'is_image')
    list_filter = ('file_type', 'is_image', 'created_at')
    search_fields = ('file_name',)

@admin.register(MessageStatus)
class MessageStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'user', 'status', 'updated_at')
    list_filter = ('status', 'updated_at')
    search_fields = ('user__username',)

@admin.register(TypingIndicator)
class TypingIndicatorAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'user', 'started_at', 'expires_at')
    list_filter = ('started_at',)
    search_fields = ('user__username', 'conversation__title')

@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'user', 'reaction_type')
    list_filter = ('reaction_type', 'created_at')
    search_fields = ('user__username', 'reaction_type')
    
    
    
    ........
    # signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Message, MessageStatus, ConversationParticipant

@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    """Updates the conversation timestamp whenever a new message is created"""
    if created and not instance.is_deleted:
        conversation = instance.conversation
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])

@receiver(post_save, sender=MessageStatus)
def handle_message_read(sender, instance, created, **kwargs):
    """Updates participant's last read message and unread count when messages are marked as read"""
    if instance.status == 'read':
        # Find the participant record
        try:
            participant = ConversationParticipant.objects.get(
                conversation=instance.message.conversation,
                user=instance.user,
                is_active=True
            )
            
            # If this message is newer than the last read message, update it
            if not participant.last_read_message or (
                participant.last_read_message.created_at < instance.message.created_at
            ):
                participant.last_read_message = instance.message
            
            # Update unread count - count messages newer than the last read message
            if participant.last_read_message:
                unread_count = Message.objects.filter(
                    conversation=instance.message.conversation,
                    created_at__gt=participant.last_read_message.created_at,
                    is_deleted=False
                ).exclude(sender=instance.user).count()
                
                participant.unread_count = unread_count
            else:
                participant.unread_count = 0
                
            participant.save(update_fields=['last_read_message', 'unread_count', 'updated_at'])
            
        except ConversationParticipant.DoesNotExist:
            pass
        
        
        .....
        
        # serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Conversation, 
    ConversationParticipant, 
    Message, 
    MessageAttachment, 
    MessageStatus,
    MessageReaction
)

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'profile_image')
        
class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ('id', 'file_name', 'file_type', 'file_size', 'file_url', 
                  'thumbnail_url', 'is_image', 'width', 'height')

class MessageStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageStatus
        fields = ('id', 'user', 'status', 'updated_at')

class MessageReactionSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ('id', 'user', 'reaction_type', 'created_at')

class MessageSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    is_read = serializers.SerializerMethodField()
    is_delivered = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ('id', 'conversation', 'sender', 'message_type', 'content', 
                  'created_at', 'updated_at', 'is_edited', 'edited_at', 'is_deleted',
                  'parent_message', 'attachments', 'reactions', 'is_read', 'is_delivered')
    
    def get_is_read(self, obj):
        user = self.context.get('request').user
        if user == obj.sender:
            # For sender, check if any recipient has read it
            return MessageStatus.objects.filter(
                message=obj,
                status='read'
            ).exclude(user=user).exists()
        else:
            # For recipient, check if they've read it
            return MessageStatus.objects.filter(
                message=obj,
                user=user,
                status='read'
            ).exists()
    
    def get_is_delivered(self, obj):
        user = self.context.get('request').user
        if user == obj.sender:
            # For sender, check if delivered to any recipient
            return MessageStatus.objects.filter(
                message=obj,
                status__in=['delivered', 'read']
            ).exclude(user=user).exists()
        else:
            # For recipient, must be delivered if they can see it
            return True

class ConversationParticipantSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    
    class Meta:
        model = ConversationParticipant
        fields = ('id', 'user', 'role', 'joined_at', 'is_active', 'unread_count')

class ConversationListSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ('id', 'title', 'conversation_type', 'participants', 'last_message_preview', 
                  'last_message_sent_at', 'unread_count', 'is_active', 'last_message', 'booking')
    
    def get_participants(self, obj):
        participants = ConversationParticipant.objects.filter(
            conversation=obj,
            is_active=True
        ).select_related('user')
        return ConversationParticipantSerializer(participants, many=True).data
    
    def get_unread_count(self, obj):
        user = self.context.get('request').user
        try:
            participant = ConversationParticipant.objects.get(
                conversation=obj,
                user=user,
                is_active=True
            )
            return participant.unread_count
        except ConversationParticipant.DoesNotExist:
            return 0
    
    def get_last_message(self, obj):
        last_message = obj.messages.filter(is_deleted=False).order_by('-created_at').first()
        if last_message:
            return MessageSerializer(last_message, context=self.context).data
        return None

class ConversationDetailSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ('id', 'title', 'conversation_type', 'participants', 'messages', 
                  'last_message_preview', 'last_message_sent_at', 'is_active', 'booking')
    
    def get_participants(self, obj):
        participants = ConversationParticipant.objects.filter(
            conversation=obj,
            is_active=True
        ).select_related('user')
        return ConversationParticipantSerializer(participants, many=True).data
    
    def get_messages(self, obj):
        messages = obj.messages.filter(is_deleted=False).order_by('created_at')
        return MessageSerializer(messages, many=True, context=self.context).data
    
    
    
    
    
    .....# Creating a new conversation between a client and provider
def create_booking_chat(client, provider, booking):
    # Create the conversation
    conversation = Conversation.objects.create(
        title=f"Booking #{booking.id}",
        conversation_type='booking_chat',
        booking=booking
    )
    
    # Add participants
    conversation.add_participant(client, 'member')
    conversation.add_participant(provider, 'member')
    
    # Add a system message
    Message.objects.create(
        conversation=conversation,
        message_type='system',
        content=f"Chat started for booking #{booking.id}",
        metadata={
            'booking_id': str(booking.id),
            'service_type': booking.service_type
        }
    )
    
    return conversation

# Creating a support conversation
def create_support_chat(user, issue_type="general"):
    # Create the conversation
    conversation = Conversation.objects.create(
        title=f"Support: {issue_type}",
        conversation_type='support_chat'
    )
    
    # Add the user
    conversation.add_participant(user, 'member')
    
    # Find available support agents and add one
    support_agent = get_available_support_agent()
    if support_agent:
        conversation.add_participant(support_agent, 'admin')
    
    # Add a system message
    Message.objects.create(
        conversation=conversation,
        message_type='system',
        content=f"Support chat started for issue: {issue_type}",
        metadata={
            'issue_type': issue_type,
            'user_type': user.user_type  # Assuming user model has a type field
        }
    )
    
    return conversation

# Sending a message
def send_message(user, conversation_id, content, attachments=None):
    try:
        # Find the conversation and verify participant
        conversation = Conversation.objects.get(id=conversation_id)
        participant = ConversationParticipant.objects.get(
            conversation=conversation,
            user=user,
            is_active=True
        )
        
        # Create the message
        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            message_type='text',
            content=content
        )
        
        # Add attachments if any
        if attachments:
            for attachment in attachments:
                MessageAttachment.objects.create(
                    message=message,
                    file_name=attachment.name,
                    file_type=attachment.content_type,
                    file_size=attachment.size,
                    file_url=upload_file_to_storage(attachment),
                    is_image=attachment.content_type.startswith('image/'),
                    # Set width and height if it's an image
                    # width=get_image_width(attachment) if is_image else None,
                    # height=get_image_height(attachment) if is_image else None
                )
        
        # Mark as sent for the sender
        MessageStatus.objects.create(
            message=message,
            user=user,
            status='sent'
        )
        
        # Send notifications to other participants
        notify_new_message(message)
        
        return message
        
    except (Conversation.DoesNotExist, ConversationParticipant.DoesNotExist):
        # User is not a participant or conversation doesn't exist
        return None

# Mark messages as read
def mark_messages_as_read(user, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        participant = ConversationParticipant.objects.get(
            conversation=conversation,
            user=user,
            is_active=True
        )
        
        # Get all unread messages not sent by this user
        unread_messages = conversation.messages.exclude(sender=user).filter(
            created_at__gt=participant.last_read_message.created_at if participant.last_read_message else timezone.datetime.min
        )
        
        # Mark each as read
        for message in unread_messages:
            message.mark_read_by(user)
        
        # This will update the unread count via the signal
        return True
        
    except (Conversation.DoesNotExist, ConversationParticipant.DoesNotExist):
        return False
    
    
    ....
    
    
    # settings.py additions

INSTALLED_APPS = [
    # ...
    'channels',  # For WebSockets
    'chat',      # Your chat app
    # ...
]

# WebSocket configuration
ASGI_APPLICATION = 'yourproject.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379')],
        },
    },
}

# Celery for background tasks
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379')