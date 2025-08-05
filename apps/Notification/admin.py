from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from .models import Notification
from .services import NotificationService


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user_email",
        "notification_type",
        "title_truncated",
        "priority",
        "read_status",
        "delivery_status_display",
        "created_at",
        "delivered_at",
    ]
    list_filter = [
        "notification_type",
        "priority",
        "read",
        "email_sent",
        "sms_sent",
        "push_sent",
        "created_at",
    ]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "title",
        "message",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "delivered_at",
        "email_sent",
        "sms_sent",
        "push_sent",
        "delivery_status",
        "is_urgent",
        "is_expired",
    ]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "notification_type", "title", "message", "priority")},
        ),
        (
            "Delivery Settings",
            {"fields": ("delivery_channels", "scheduled_for", "expires_at")},
        ),
        (
            "Related Object",
            {
                "fields": ("related_object_type", "related_object_id"),
                "classes": ("collapse",),
            },
        ),
        (
            "Action Settings",
            {"fields": ("action_url", "action_text"), "classes": ("collapse",)},
        ),
        ("Additional Data", {"fields": ("data",), "classes": ("collapse",)}),
        (
            "Status Information",
            {
                "fields": (
                    "read",
                    "read_at",
                    "delivered_at",
                    "email_sent",
                    "sms_sent",
                    "push_sent",
                    "delivery_status",
                    "is_urgent",
                    "is_expired",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = [
        "mark_as_read",
        "mark_as_unread",
        "resend_notifications",
        "delete_read_notifications",
    ]

    def user_email(self, obj):
        return obj.user.email if obj.user else "No User"

    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"

    def title_truncated(self, obj):
        if len(obj.title) > 50:
            return f"{obj.title[:47]}..."
        return obj.title

    title_truncated.short_description = "Title"
    title_truncated.admin_order_field = "title"

    def read_status(self, obj):
        if obj.read:
            return format_html('<span style="color: green;">✓ Read</span>')
        else:
            if obj.is_urgent:
                return format_html(
                    '<span style="color: red; font-weight: bold;">⚠ Urgent Unread</span>'
                )
            return format_html('<span style="color: orange;">● Unread</span>')

    read_status.short_description = "Status"

    def delivery_status_display(self, obj):
        status = obj.delivery_status
        html_parts = []

        if status.get("in_app"):
            html_parts.append('<span style="color: blue;">📱 App</span>')
        if status.get("email"):
            html_parts.append('<span style="color: green;">📧 Email</span>')
        else:
            if "email" in obj.delivery_channels:
                html_parts.append('<span style="color: red;">📧 Failed</span>')

        if status.get("sms"):
            html_parts.append('<span style="color: green;">📱 SMS</span>')
        if status.get("push"):
            html_parts.append('<span style="color: green;">🔔 Push</span>')

        return format_html(" | ".join(html_parts)) if html_parts else "None"

    delivery_status_display.short_description = "Delivery Status"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user")

    def mark_as_read(self, request, queryset):
        updated = 0
        for notification in queryset:
            if not notification.read:
                notification.mark_as_read()
                updated += 1

        self.message_user(request, f"{updated} notifications marked as read.")

    mark_as_read.short_description = "Mark selected notifications as read"

    def mark_as_unread(self, request, queryset):
        updated = queryset.filter(read=True).update(read=False, read_at=None)
        self.message_user(request, f"{updated} notifications marked as unread.")

    mark_as_unread.short_description = "Mark selected notifications as unread"

    def resend_notifications(self, request, queryset):
        count = 0
        for notification in queryset:
            try:
                NotificationService.send_notification(notification)
                count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Failed to resend notification {notification.id}: {str(e)}",
                    level="ERROR",
                )

        if count > 0:
            self.message_user(request, f"{count} notifications resent successfully.")

    resend_notifications.short_description = "Resend selected notifications"

    def delete_read_notifications(self, request, queryset):
        read_notifications = queryset.filter(read=True)
        count = read_notifications.count()
        read_notifications.delete()
        self.message_user(request, f"{count} read notifications deleted.")

    delete_read_notifications.short_description = "Delete read notifications"

    def changelist_view(self, request, extra_context=None):
        # Add summary statistics to the changelist
        extra_context = extra_context or {}

        # Get counts for the dashboard
        total_notifications = Notification.objects.count()
        unread_notifications = Notification.objects.filter(read=False).count()
        urgent_notifications = Notification.objects.filter(
            priority__in=["high", "urgent"], read=False
        ).count()

        # Email delivery stats
        email_sent = Notification.objects.filter(email_sent=True).count()
        email_failed = Notification.objects.filter(
            delivery_channels__contains=["email"], email_sent=False
        ).count()

        # Recent activity (last 24 hours)
        recent_cutoff = timezone.now() - timezone.timedelta(hours=24)
        recent_notifications = Notification.objects.filter(
            created_at__gte=recent_cutoff
        ).count()

        extra_context["notification_stats"] = {
            "total": total_notifications,
            "unread": unread_notifications,
            "urgent": urgent_notifications,
            "email_sent": email_sent,
            "email_failed": email_failed,
            "recent_24h": recent_notifications,
        }

        return super().changelist_view(request, extra_context)


# Register additional admin actions as standalone admin commands
class NotificationAdminActions:
    """Additional admin actions for notifications"""

    @staticmethod
    def send_test_notification(request):
        """Send a test notification to the admin user"""
        try:
            notification = NotificationService.create_notification(
                user=request.user,
                notification_type="system",
                title="Admin Test Notification",
                message="This is a test notification sent from the Django admin interface.",
                priority="normal",
                send_immediately=True,
            )
            return f"Test notification sent successfully (ID: {notification.id})"
        except Exception as e:
            return f"Failed to send test notification: {str(e)}"

    @staticmethod
    def cleanup_old_notifications(days=30):
        """Clean up old read notifications"""
        from .utils import NotificationBatchProcessor

        deleted_count = NotificationBatchProcessor.cleanup_old_notifications(days)
        return f"Deleted {deleted_count} old notifications (older than {days} days)"


# Custom admin site integration
admin.site.site_header = "MoreVans Notification Admin"
admin.site.site_title = "Notification Management"
admin.site.index_title = "Notification Administration"
