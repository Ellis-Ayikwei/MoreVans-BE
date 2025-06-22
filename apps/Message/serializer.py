from rest_framework import serializers
from .models import Message
from apps.User.serializer import UserSerializer


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True, required=False)
    receiver_id = serializers.UUIDField(write_only=True, required=True)
    request_id = serializers.UUIDField(write_only=True, required=True)

    # Attachment-related fields
    attachment_url = serializers.SerializerMethodField()
    formatted_file_size = serializers.CharField(read_only=True)
    file_extension = serializers.CharField(read_only=True)
    is_image = serializers.BooleanField(read_only=True)

    # Computed fields
    time_since_sent = serializers.SerializerMethodField()
    is_sender = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "request",
            "request_id",
            "sender",
            "sender_id",
            "receiver",
            "receiver_id",
            "content",
            "attachment",
            "attachment_url",
            "attachment_name",
            "attachment_size",
            "attachment_type",
            "formatted_file_size",
            "file_extension",
            "is_image",
            "message_type",
            "read",
            "read_at",
            "created_at",
            "updated_at",
            "time_since_sent",
            "is_sender",
        ]
        read_only_fields = [
            "id",
            "request",
            "created_at",
            "updated_at",
            "read_at",
            "message_type",
            "attachment_name",
            "attachment_size",
            "attachment_type",
        ]

    def get_attachment_url(self, obj):
        """Get full attachment URL"""
        if obj.attachment:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            return obj.attachment.url
        return None

    def get_time_since_sent(self, obj):
        """Get human-readable time since message was sent"""
        from django.utils import timezone

        if obj.created_at:
            delta = timezone.now() - obj.created_at
            if delta.days > 0:
                return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif delta.seconds > 60:
                minutes = delta.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"
        return None

    def get_is_sender(self, obj):
        """Check if current user is the sender"""
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return obj.sender == request.user
        return False

    def validate(self, attrs):
        """Validate that message has either content or attachment"""
        content = attrs.get("content", "").strip()
        attachment = attrs.get("attachment")

        if not content and not attachment:
            raise serializers.ValidationError(
                "Message must have either text content or an attachment"
            )

        # Validate file size (max 10MB)
        if attachment and hasattr(attachment, "size"):
            max_size = 10 * 1024 * 1024  # 10MB
            if attachment.size > max_size:
                raise serializers.ValidationError(
                    f"File size must be less than {max_size // (1024*1024)}MB"
                )

        return attrs

    def create(self, validated_data):
        """Custom create method"""
        request_id = validated_data.pop("request_id")
        receiver_id = validated_data.pop("receiver_id")
        sender_id = validated_data.pop("sender_id", None)

        # Get the request object
        try:
            from apps.Request.models import Request

            request_obj = Request.objects.get(id=request_id)
            validated_data["request"] = request_obj
        except Request.DoesNotExist:
            raise serializers.ValidationError("Request not found")

        # Get receiver
        try:
            from apps.User.models import User

            receiver = User.objects.get(id=receiver_id)
            validated_data["receiver"] = receiver
        except User.DoesNotExist:
            raise serializers.ValidationError("Receiver not found")

        return super().create(validated_data)
