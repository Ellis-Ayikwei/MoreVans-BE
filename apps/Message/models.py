from django.db import models
import os
from apps.Basemodel.models import Basemodel
from apps.Request.models import Request
from apps.User.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone


def message_attachment_upload_path(instance, filename):
    """Generate upload path for message attachments"""
    from datetime import datetime

    now = datetime.now()
    return f"messages/{instance.request.id}/{now.year}/{now.month:02d}/{filename}"


def chat_attachment_upload_path(instance, filename):
    """Generate upload path for chat attachments"""
    from datetime import datetime

    now = datetime.now()
    chat_room_id = instance.chat_room.id if instance.chat_room else 'general'
    return f"chats/{chat_room_id}/{now.year}/{now.month:02d}/{filename}"


class ChatRoom(Basemodel):
    """
    Chat room model that can be associated with different contexts
    like requests, jobs, bids, support tickets, etc.
    """
    ROOM_TYPES = [
        ("request", "Request Chat"),
        ("job", "Job Chat"),
        ("bidding", "Bidding Chat"),
        ("support", "Support Chat"),
        ("general", "General Chat"),
        ("provider_customer", "Provider-Customer Chat"),
    ]

    name = models.CharField(max_length=255, blank=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default="general")
    
    # Generic relation to any model (Request, Job, Bid, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Participants
    participants = models.ManyToManyField(User, related_name="chat_rooms")
    
    # Room settings
    is_active = models.BooleanField(default=True)
    is_private = models.BooleanField(default=True)
    
    # Metadata
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "chat_room"
        ordering = ["-last_message_at", "-created_at"]
        
    def __str__(self):
        if self.name:
            return self.name
        return f"{self.get_room_type_display()} - {self.id}"
    
    def add_participant(self, user):
        """Add a user to the chat room"""
        self.participants.add(user)
    
    def remove_participant(self, user):
        """Remove a user from the chat room"""
        self.participants.remove(user)
    
    def get_last_message(self):
        """Get the last message in this room"""
        return self.chat_messages.first()
    
    @property
    def unread_count_for_user(self, user):
        """Get unread message count for a specific user"""
        return self.chat_messages.filter(
            read_by__isnull=True
        ).exclude(sender=user).count()


class ChatMessage(Basemodel):
    """
    Enhanced chat message model for multi-context messaging
    """
    MESSAGE_TYPES = [
        ("text", "Text"),
        ("image", "Image"),
        ("file", "File"),
        ("system", "System Message"),
        ("bid_update", "Bid Update"),
        ("status_update", "Status Update"),
    ]

    chat_room = models.ForeignKey(
        ChatRoom, 
        on_delete=models.CASCADE, 
        related_name="chat_messages"
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="sent_chat_messages"
    )
    content = models.TextField(blank=True)
    message_type = models.CharField(
        max_length=25, 
        choices=MESSAGE_TYPES, 
        default="text"
    )
    
    # File attachment
    attachment = models.FileField(
        upload_to=chat_attachment_upload_path, 
        null=True, 
        blank=True
    )
    attachment_name = models.CharField(max_length=255, blank=True)
    attachment_size = models.PositiveIntegerField(null=True, blank=True)
    attachment_type = models.CharField(max_length=100, blank=True)
    
    # Message status
    read_by = models.ManyToManyField(
        User, 
        through='ChatMessageRead', 
        related_name="read_chat_messages",
        blank=True
    )
    
    # Reply functionality
    reply_to = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='replies'
    )
    
    # System message metadata
    system_data = models.JSONField(null=True, blank=True, help_text="Additional data for system messages")
    
    class Meta:
        db_table = "chat_message"
        ordering = ["-created_at"]
        
    def __str__(self):
        return f"Message from {self.sender.username} in {self.chat_room}"
    
    def save(self, *args, **kwargs):
        """Auto-determine message type and attachment info"""
        if self.attachment:
            # Store original filename and size
            if hasattr(self.attachment, "name") and self.attachment.name:
                self.attachment_name = os.path.basename(self.attachment.name)

            if hasattr(self.attachment, "size"):
                self.attachment_size = self.attachment.size

            # Determine attachment type
            if hasattr(self.attachment, "content_type"):
                self.attachment_type = self.attachment.content_type

            # Set message type if not already set
            if self.message_type == "text":
                if self.is_image():
                    self.message_type = "image"
                else:
                    self.message_type = "file"
        
        super().save(*args, **kwargs)
        
        # Update chat room's last message time
        self.chat_room.last_message_at = self.created_at
        self.chat_room.save(update_fields=['last_message_at'])
    
    def is_image(self):
        """Check if attachment is an image"""
        if not self.attachment:
            return False

        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"]
        image_mimes = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/bmp",
            "image/webp",
            "image/svg+xml",
        ]

        # Check by file extension
        if self.attachment_name:
            _, ext = os.path.splitext(self.attachment_name.lower())
            if ext in image_extensions:
                return True

        # Check by MIME type
        if self.attachment_type in image_mimes:
            return True

        return False
    
    def mark_as_read(self, user):
        """Mark this message as read by a user"""
        ChatMessageRead.objects.get_or_create(
            message=self,
            user=user,
            defaults={'read_at': timezone.now()}
        )
    
    @property
    def attachment_url(self):
        """Get the full URL for the attachment"""
        if self.attachment:
            return self.attachment.url
        return None

    @property
    def formatted_file_size(self):
        """Get human-readable file size"""
        if not self.attachment_size:
            return None

        size = self.attachment_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class ChatMessageRead(Basemodel):
    """
    Track when users read specific messages
    """
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "chat_message_read"
        unique_together = ['message', 'user']


# Keep the original Message model for backward compatibility
class Message(Basemodel):
    MESSAGE_TYPES = [
        ("text", "Text"),
        ("image", "Image"),
        ("file", "File"),
        ("text_with_attachment", "Text with Attachment"),
    ]

    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    content = models.TextField(
        blank=True
    )  # Make content optional for attachment-only messages

    # File/Image attachment
    attachment = models.FileField(
        upload_to=message_attachment_upload_path, null=True, blank=True
    )
    attachment_name = models.CharField(max_length=255, blank=True)  # Original filename
    attachment_size = models.PositiveIntegerField(
        null=True, blank=True
    )  # File size in bytes
    attachment_type = models.CharField(max_length=100, blank=True)  # MIME type

    message_type = models.CharField(
        max_length=25, choices=MESSAGE_TYPES, default="text"
    )
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"

    def save(self, *args, **kwargs):
        """Auto-determine message type and attachment info"""
        if self.attachment:
            # Store original filename and size
            if hasattr(self.attachment, "name") and self.attachment.name:
                self.attachment_name = os.path.basename(self.attachment.name)

            if hasattr(self.attachment, "size"):
                self.attachment_size = self.attachment.size

            # Determine attachment type
            if hasattr(self.attachment, "content_type"):
                self.attachment_type = self.attachment.content_type

            # Set message type
            if self.content.strip():
                self.message_type = "text_with_attachment"
            elif self.is_image():
                self.message_type = "image"
            else:
                self.message_type = "file"
        else:
            self.message_type = "text"

        super().save(*args, **kwargs)

    def is_image(self):
        """Check if attachment is an image"""
        if not self.attachment:
            return False

        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"]
        image_mimes = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/bmp",
            "image/webp",
            "image/svg+xml",
        ]

        # Check by file extension
        if self.attachment_name:
            _, ext = os.path.splitext(self.attachment_name.lower())
            if ext in image_extensions:
                return True

        # Check by MIME type
        if self.attachment_type in image_mimes:
            return True

        return False

    @property
    def attachment_url(self):
        """Get the full URL for the attachment"""
        if self.attachment:
            return self.attachment.url
        return None

    @property
    def formatted_file_size(self):
        """Get human-readable file size"""
        if not self.attachment_size:
            return None

        size = self.attachment_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @property
    def file_extension(self):
        """Get file extension"""
        if self.attachment_name:
            _, ext = os.path.splitext(self.attachment_name)
            return ext.lower()
        return None

    class Meta:
        db_table = "message"
        managed = True
        ordering = ["-created_at"]
