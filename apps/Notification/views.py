from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import Notification
from .serializer import (
    NotificationSerializer,
    NotificationCreateSerializer,
    NotificationUpdateSerializer,
    NotificationPreferenceSerializer,
)
from .services import NotificationService, NotificationPreferenceService


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Notification instances.
    """

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter notifications to current user and apply query parameters"""
        queryset = Notification.objects.filter(user=self.request.user)

        # Filter parameters
        notification_type = self.request.query_params.get("type", None)
        read = self.request.query_params.get("read", None)
        priority = self.request.query_params.get("priority", None)
        unread_only = (
            self.request.query_params.get("unread_only", "false").lower() == "true"
        )
        urgent_only = (
            self.request.query_params.get("urgent_only", "false").lower() == "true"
        )

        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        if read is not None:
            read_bool = read.lower() == "true"
            queryset = queryset.filter(read=read_bool)
        if priority:
            queryset = queryset.filter(priority=priority)
        if unread_only:
            queryset = queryset.filter(read=False)
        if urgent_only:
            queryset = queryset.filter(priority__in=["high", "urgent"])

        # Exclude expired notifications unless specifically requested
        include_expired = (
            self.request.query_params.get("include_expired", "false").lower() == "true"
        )
        if not include_expired:
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )

        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "create":
            return NotificationCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return NotificationUpdateSerializer
        return NotificationSerializer

    def create(self, request, *args, **kwargs):
        """Create notification (admin/staff only)"""
        if not request.user.is_staff:
            return Response(
                {"detail": "Only staff can create notifications directly."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        if notification.user != request.user:
            return Response(
                {"detail": "You can only mark your own notifications as read."},
                status=status.HTTP_403_FORBIDDEN,
            )

        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def mark_all_as_read(self, request):
        """Mark all notifications for the current user as read."""
        notifications = Notification.objects.filter(user=request.user, read=False)
        count = notifications.count()

        for notification in notifications:
            notification.mark_as_read()

        return Response(
            {"detail": f"Marked {count} notifications as read.", "count": count}
        )

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """Get count of unread notifications for current user."""
        count = Notification.objects.filter(user=request.user, read=False).count()
        urgent_count = Notification.objects.filter(
            user=request.user, read=False, priority__in=["high", "urgent"]
        ).count()

        return Response({"unread_count": count, "urgent_count": urgent_count})

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get notification summary for current user."""
        queryset = self.get_queryset()

        summary = {
            "total": queryset.count(),
            "unread": queryset.filter(read=False).count(),
            "urgent": queryset.filter(priority__in=["high", "urgent"]).count(),
            "by_type": {},
            "recent": [],
        }

        # Count by type
        for notification_type, _ in Notification.NOTIFICATION_TYPES:
            count = queryset.filter(notification_type=notification_type).count()
            if count > 0:
                summary["by_type"][notification_type] = count

        # Recent notifications (last 5)
        recent = queryset[:5]
        summary["recent"] = NotificationSerializer(recent, many=True).data

        return Response(summary)

    @action(detail=False, methods=["delete"])
    def clear_read(self, request):
        """Delete all read notifications for current user."""
        count = Notification.objects.filter(user=request.user, read=True).delete()[0]
        return Response(
            {"detail": f"Deleted {count} read notifications.", "count": count}
        )

    @action(detail=False, methods=["get", "post"])
    def preferences(self, request):
        """Get or update notification preferences."""
        if request.method == "GET":
            prefs = NotificationPreferenceService.get_user_preferences(request.user)
            return Response(prefs)

        elif request.method == "POST":
            serializer = NotificationPreferenceSerializer(data=request.data)
            if serializer.is_valid():
                NotificationPreferenceService.update_user_preferences(
                    request.user, serializer.validated_data
                )
                return Response({"detail": "Preferences updated successfully."})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def test_notification(self, request):
        """Send a test notification (staff only)."""
        if not request.user.is_staff:
            return Response(
                {"detail": "Only staff can send test notifications."},
                status=status.HTTP_403_FORBIDDEN,
            )

        notification_type = request.data.get("notification_type", "system_test")
        test_data = request.data.get("test_data", {})

        notification = NotificationService.create_notification(
            user=request.user,
            notification_type=notification_type,
            title="Test Notification",
            message="This is a test notification to verify the system is working correctly.",
            data=test_data,
            priority="normal",
            send_immediately=True,
        )

        serializer = self.get_serializer(notification)
        return Response(serializer.data)
