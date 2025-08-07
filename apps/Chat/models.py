from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.Basemodel.models import Basemodel
from apps.User.models import User
import os


def chat_attachment_upload_path(instance, filename):
    """Generate upload path for chat attachments"""
    from datetime import datetime
    now = datetime.now()
    return f"chat/{instance.conversation.id}/{now.year}/{now.month:02d}/{filename}"


class Conversation(Basemodel):
    """
    Represents a chat conversation that can be linked to any model
    (Job, Bid, Request, Dispute, etc.)
    """
    CONVERSATION_TYPES = [
        ('direct', 'Direct Message'),
        ('job', 'Job Discussion'),
        ('bid', 'Bid Negotiation'),
        ('request', 'Request Discussion'),
        ('support', 'Support Chat'),
        ('dispute', 'Dispute Resolution'),
        ('general', 'General Chat'),
    ]
    
    title = models.CharField(max_length=255, blank=True)
    conversation_type = models.CharField(
        max_length=20, 
        choices=CONVERSATION_TYPES, 
        default='general'
    )
    
    # Generic relation to link to any model
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Conversation settings
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    allow_attachments = models.BooleanField(default=True)
    max_attachment_size = models.IntegerField(
        default=10485760  # 10MB in bytes
    )
    
    class Meta:
        db_table = 'chat_conversation'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['conversation_type']),
        ]
    
    def __str__(self):
        return self.title or f"{self.conversation_type} - {self.id}"
    
    def get_participants(self):
        """Get all participants in this conversation"""
        return self.participants.filter(is_active=True).select_related('user')
    
    def add_participant(self, user, role='participant'):
        """Add a participant to the conversation"""
        participant, created = ConversationParticipant.objects.get_or_create(
            conversation=self,
            user=user,
            defaults={'role': role}
        )
        if not created and not participant.is_active:
            participant.is_active = True
            participant.save()
        return participant
    
    def remove_participant(self, user):
        """Remove a participant from the conversation"""
        try:
            participant = self.participants.get(user=user)
            participant.is_active = False
            participant.left_at = models.DateTimeField(auto_now=True)
            participant.save()
            return True
        except ConversationParticipant.DoesNotExist:
            return False
    
    def get_unread_count(self, user):
        """Get unread message count for a specific user"""
        participant = self.participants.filter(user=user).first()
        if not participant:
            return 0
        return self.messages.filter(
            created_at__gt=participant.last_read_at
        ).exclude(sender=user).count()


class ConversationParticipant(Basemodel):
    """Represents a participant in a conversation"""
    ROLES = [
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('participant', 'Participant'),
        ('observer', 'Observer'),
    ]
    
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='participants'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chat_participations'
    )
    role = models.CharField(max_length=20, choices=ROLES, default='participant')
    is_active = models.BooleanField(default=True)
    last_read_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    # Notification preferences
    notify_on_message = models.BooleanField(default=True)
    notify_on_mention = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'chat_participant'
        unique_together = ['conversation', 'user']
        ordering = ['joined_at']
    
    def __str__(self):
        return f"{self.user.username} in {self.conversation}"
    
    def mark_as_read(self):
        """Mark all messages as read up to now"""
        from django.utils import timezone
        self.last_read_at = timezone.now()
        self.save()


class ChatMessage(Basemodel):
    """Represents a message in a conversation"""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('location', 'Location'),
        ('system', 'System Message'),
    ]
    
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='sent_chat_messages'
    )
    content = models.TextField(blank=True)
    message_type = models.CharField(
        max_length=20, 
        choices=MESSAGE_TYPES, 
        default='text'
    )
    
    # File/Media attachments
    attachment = models.FileField(
        upload_to=chat_attachment_upload_path, 
        null=True, 
        blank=True
    )
    attachment_name = models.CharField(max_length=255, blank=True)
    attachment_size = models.PositiveIntegerField(null=True, blank=True)
    attachment_type = models.CharField(max_length=100, blank=True)
    
    # Additional message data
    metadata = models.JSONField(null=True, blank=True)
    
    # Message status
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Reply functionality
    reply_to = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='replies'
    )
    
    class Meta:
        db_table = 'chat_message'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender.username if self.sender else 'System'}: {self.content[:50]}"
    
    def save(self, *args, **kwargs):
        """Auto-determine message type and attachment info"""
        if self.attachment:
            # Store original filename and size
            if hasattr(self.attachment, 'name') and self.attachment.name:
                self.attachment_name = os.path.basename(self.attachment.name)
            
            if hasattr(self.attachment, 'size'):
                self.attachment_size = self.attachment.size
            
            # Determine attachment type
            if hasattr(self.attachment, 'content_type'):
                self.attachment_type = self.attachment.content_type
            
            # Auto-set message type based on attachment
            if not self.message_type or self.message_type == 'text':
                if self.is_image():
                    self.message_type = 'image'
                elif self.is_video():
                    self.message_type = 'video'
                elif self.is_audio():
                    self.message_type = 'audio'
                else:
                    self.message_type = 'file'
        
        # Update conversation's updated_at
        if not self.pk:  # Only on creation
            self.conversation.save()  # This will update updated_at
        
        super().save(*args, **kwargs)
    
    def is_image(self):
        """Check if attachment is an image"""
        if not self.attachment:
            return False
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
        image_mimes = [
            'image/jpeg', 'image/png', 'image/gif', 
            'image/bmp', 'image/webp', 'image/svg+xml'
        ]
        
        if self.attachment_name:
            _, ext = os.path.splitext(self.attachment_name.lower())
            if ext in image_extensions:
                return True
        
        if self.attachment_type in image_mimes:
            return True
        
        return False
    
    def is_video(self):
        """Check if attachment is a video"""
        if not self.attachment:
            return False
        
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        video_mimes = [
            'video/mp4', 'video/avi', 'video/quicktime',
            'video/x-ms-wmv', 'video/x-flv', 'video/webm'
        ]
        
        if self.attachment_name:
            _, ext = os.path.splitext(self.attachment_name.lower())
            if ext in video_extensions:
                return True
        
        if self.attachment_type and any(mime in self.attachment_type for mime in video_mimes):
            return True
        
        return False
    
    def is_audio(self):
        """Check if attachment is audio"""
        if not self.attachment:
            return False
        
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        audio_mimes = [
            'audio/mpeg', 'audio/wav', 'audio/ogg',
            'audio/mp4', 'audio/flac'
        ]
        
        if self.attachment_name:
            _, ext = os.path.splitext(self.attachment_name.lower())
            if ext in audio_extensions:
                return True
        
        if self.attachment_type in audio_mimes:
            return True
        
        return False
    
    def get_recipients(self):
        """Get all recipients of this message"""
        return User.objects.filter(
            chat_participations__conversation=self.conversation,
            chat_participations__is_active=True
        ).exclude(id=self.sender_id if self.sender else None)


class MessageReaction(Basemodel):
    """Represents reactions to messages"""
    message = models.ForeignKey(
        ChatMessage, 
        on_delete=models.CASCADE, 
        related_name='reactions'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='message_reactions'
    )
    emoji = models.CharField(max_length=10)
    
    class Meta:
        db_table = 'chat_message_reaction'
        unique_together = ['message', 'user', 'emoji']
    
    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to message"


class MessageRead(Basemodel):
    """Track read receipts for messages"""
    message = models.ForeignKey(
        ChatMessage, 
        on_delete=models.CASCADE, 
        related_name='read_receipts'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='read_messages'
    )
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_message_read'
        unique_together = ['message', 'user']
        indexes = [
            models.Index(fields=['message', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} read message at {self.read_at}"