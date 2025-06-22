from django.db import models
import os
from apps.Basemodel.models import Basemodel
from apps.Request.models import Request
from apps.User.models import User


def message_attachment_upload_path(instance, filename):
    """Generate upload path for message attachments"""
    from datetime import datetime

    now = datetime.now()
    return f"messages/{instance.request.id}/{now.year}/{now.month:02d}/{filename}"


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
