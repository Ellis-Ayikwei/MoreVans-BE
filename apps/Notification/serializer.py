from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    delivery_status = serializers.ReadOnlyField()
    is_urgent = serializers.ReadOnlyField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "notification_type",
            "title",
            "message",
            "data",
            "created_at",
            "read",
            "read_at",
            "priority",
            "delivery_channels",
            "scheduled_for",
            "delivered_at",
            "email_sent",
            "sms_sent",
            "push_sent",
            "related_object_type",
            "related_object_id",
            "action_url",
            "action_text",
            "expires_at",
            "delivery_status",
            "is_urgent",
            "is_expired",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "delivered_at",
            "email_sent",
            "sms_sent",
            "push_sent",
            "delivery_status",
            "is_urgent",
            "is_expired",
        ]

    def get_is_expired(self, obj):
        return obj.is_expired()


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications (admin/internal use)"""

    class Meta:
        model = Notification
        fields = [
            "user",
            "notification_type",
            "title",
            "message",
            "data",
            "priority",
            "delivery_channels",
            "scheduled_for",
            "expires_at",
            "related_object_type",
            "related_object_id",
            "action_url",
            "action_text",
        ]


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating notification (marking as read, etc.)"""

    class Meta:
        model = Notification
        fields = ["read", "read_at"]
        read_only_fields = ["read_at"]

    def update(self, instance, validated_data):
        if validated_data.get("read", False):
            instance.mark_as_read()
        return instance


class NotificationPreferenceSerializer(serializers.Serializer):
    """Serializer for user notification preferences"""

    email_notifications = serializers.BooleanField(default=True)
    sms_notifications = serializers.BooleanField(default=False)
    push_notifications = serializers.BooleanField(default=True)
    notification_types = serializers.DictField(
        child=serializers.BooleanField(), default=dict
    )
