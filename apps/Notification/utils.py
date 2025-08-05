import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db.models import Q
from decimal import Decimal

from .models import Notification

logger = logging.getLogger(__name__)


class NotificationTemplateRenderer:
    """Utility class for rendering notification templates"""

    @staticmethod
    def render_notification_email(
        notification: Notification, **extra_context
    ) -> Dict[str, str]:
        """
        Render HTML and text email templates for a notification.

        Args:
            notification: Notification instance
            **extra_context: Additional context for templates

        Returns:
            Dict with 'html' and 'text' keys containing rendered content
        """
        try:
            # Determine template name
            template_name = f"notifications/{notification.notification_type}"

            # Prepare context
            context = {
                "user": notification.user,
                "user_name": notification.user.first_name
                or notification.user.email.split("@")[0],
                "notification": notification,
                "title": notification.title,
                "message": notification.message,
                "action_url": notification.action_url,
                "action_text": notification.action_text or "View Details",
                "app_name": "MoreVans",
                "current_year": datetime.now().year,
                "notification_data": notification.data or {},
                **extra_context,
            }

            # Try to render specific template, fall back to generic
            try:
                html_content = render_to_string(f"emails/{template_name}.html", context)
                text_content = render_to_string(f"emails/{template_name}.txt", context)
            except Exception as e:
                logger.warning(
                    f"Failed to render specific template {template_name}, using generic: {str(e)}"
                )
                html_content = render_to_string(
                    "emails/notifications/generic_notification.html", context
                )
                text_content = render_to_string(
                    "emails/notifications/generic_notification.txt", context
                )

            return {
                "html": html_content,
                "text": text_content,
                "subject": notification.title,
            }

        except Exception as e:
            logger.error(f"Failed to render notification email: {str(e)}")
            return {
                "html": f"<p>{notification.message}</p>",
                "text": notification.message,
                "subject": notification.title,
            }


class NotificationFormatter:
    """Utility class for formatting notification content"""

    @staticmethod
    def format_currency(amount: Decimal) -> str:
        """Format currency amount"""
        return f"£{amount:,.2f}"

    @staticmethod
    def format_datetime(dt: datetime, include_time: bool = True) -> str:
        """Format datetime for display"""
        if include_time:
            return dt.strftime("%d %b %Y, %H:%M")
        return dt.strftime("%d %b %Y")

    @staticmethod
    def format_notification_title(notification_type: str, context: Dict) -> str:
        """Generate formatted title based on notification type and context"""
        title_formats = {
            "booking_created": "Booking Request Created",
            "booking_confirmed": "Booking Confirmed!",
            "booking_cancelled": "Booking Cancelled",
            "provider_accepted": "Provider Accepted Your Job",
            "provider_assigned": "Provider Assigned",
            "job_started": "Your Job Has Started",
            "job_in_transit": "Items In Transit",
            "job_completed": "Job Completed Successfully",
            "account_verified": "Account Verified!",
            "provider_verified": "Provider Account Verified!",
            "payment_confirmed": "Payment Confirmed",
            "payment_failed": "Payment Failed",
            "deposit_received": "Deposit Received",
            "bid_received": "New Bid Received",
            "bid_accepted": "Your Bid Was Accepted!",
            "bid_rejected": "Bid Not Selected",
            "message_received": "New Message",
            "review_received": "New Review Received",
            "rating_reminder": "Please Rate Your Experience",
        }

        base_title = title_formats.get(notification_type, "Notification")

        # Add context-specific formatting
        if notification_type == "bid_received" and context.get("amount"):
            base_title += f" - £{context['amount']}"
        elif notification_type == "payment_confirmed" and context.get("amount"):
            base_title += f" - £{context['amount']}"

        return base_title

    @staticmethod
    def format_notification_message(notification_type: str, context: Dict) -> str:
        """Generate formatted message based on notification type and context"""
        user_name = context.get("user_name", "there")

        messages = {
            "booking_created": f"Your booking request has been submitted successfully. We'll notify you when providers start bidding on your job.",
            "booking_confirmed": f"Great news! Your booking has been confirmed and assigned to a provider. They'll be in touch shortly.",
            "booking_cancelled": f"Your booking has been cancelled. If this was unexpected, please contact our support team.",
            "provider_accepted": f"A provider has accepted your job and will contact you with the next steps.",
            "provider_assigned": f"We've assigned a qualified provider to your job. Check your dashboard for details.",
            "job_started": f"Your job has officially started! You can track the progress in real-time through your dashboard.",
            "job_in_transit": f"Your items are now in transit. You'll receive another notification when they arrive safely.",
            "job_completed": f"Your job has been completed successfully! Please take a moment to rate your experience.",
            "account_verified": f"Congratulations! Your account has been fully verified and is now active.",
            "provider_verified": f"Your provider account has been verified! You can now start bidding on jobs and accepting assignments.",
            "payment_confirmed": f"Your payment has been processed successfully. Thank you for choosing MoreVans!",
            "payment_failed": f"We couldn't process your payment. Please update your payment method or try again.",
            "deposit_received": f"We've received your deposit payment. Your booking is now confirmed and being processed.",
            "bid_received": f"You've received a new bid on your job! Review the details and choose the best provider for your needs.",
            "bid_accepted": f"Congratulations! Your bid has been accepted. Time to get to work and deliver excellent service!",
            "bid_rejected": f"Your bid wasn't selected this time, but don't worry - there are many more opportunities available.",
            "message_received": f"You have a new message waiting for you. Click to view and respond.",
            "review_received": f"You've received a new review from a customer. See what they had to say about your service!",
            "rating_reminder": f"How was your recent experience with MoreVans? We'd love to hear your feedback!",
        }

        base_message = messages.get(
            notification_type, "You have a new notification from MoreVans."
        )

        # Add context-specific information
        if context.get("provider_name"):
            if notification_type in ["provider_accepted", "provider_assigned"]:
                base_message += f" Provider: {context['provider_name']}"

        if context.get("reference_number"):
            base_message += f" Reference: {context['reference_number']}"

        return base_message


class NotificationQueryHelper:
    """Utility class for complex notification queries"""

    @staticmethod
    def get_user_notification_summary(user, days: int = 30) -> Dict:
        """Get comprehensive notification summary for a user"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        queryset = Notification.objects.filter(user=user, created_at__gte=start_date)

        summary = {
            "total": queryset.count(),
            "unread": queryset.filter(read=False).count(),
            "urgent": queryset.filter(priority__in=["high", "urgent"]).count(),
            "by_type": {},
            "by_priority": {},
            "daily_counts": {},
            "delivery_stats": {
                "email_sent": queryset.filter(email_sent=True).count(),
                "sms_sent": queryset.filter(sms_sent=True).count(),
                "push_sent": queryset.filter(push_sent=True).count(),
            },
        }

        # Count by type
        for notification_type, _ in Notification.NOTIFICATION_TYPES:
            count = queryset.filter(notification_type=notification_type).count()
            if count > 0:
                summary["by_type"][notification_type] = count

        # Count by priority
        for priority, _ in Notification.PRIORITY_LEVELS:
            count = queryset.filter(priority=priority).count()
            if count > 0:
                summary["by_priority"][priority] = count

        # Daily counts for the last 7 days
        for i in range(7):
            date = end_date.date() - timedelta(days=i)
            count = queryset.filter(created_at__date=date).count()
            summary["daily_counts"][date.isoformat()] = count

        return summary

    @staticmethod
    def get_expired_notifications(user=None, batch_size: int = 100):
        """Get expired notifications for cleanup"""
        queryset = Notification.objects.filter(expires_at__lt=timezone.now())

        if user:
            queryset = queryset.filter(user=user)

        return queryset[:batch_size]

    @staticmethod
    def get_scheduled_notifications_due():
        """Get notifications that are scheduled and due to be sent"""
        return Notification.objects.filter(
            scheduled_for__lte=timezone.now(), delivered_at__isnull=True
        )

    @staticmethod
    def get_failed_email_notifications(hours: int = 24):
        """Get notifications where email sending might have failed"""
        cutoff = timezone.now() - timedelta(hours=hours)

        return Notification.objects.filter(
            delivery_channels__contains=["email"],
            email_sent=False,
            created_at__lt=cutoff,
            delivered_at__isnull=False,  # Marked as delivered but email not sent
        )


class NotificationValidator:
    """Utility class for validating notification data"""

    @staticmethod
    def validate_notification_type(notification_type: str) -> bool:
        """Check if notification type is valid"""
        valid_types = [choice[0] for choice in Notification.NOTIFICATION_TYPES]
        return notification_type in valid_types

    @staticmethod
    def validate_priority(priority: str) -> bool:
        """Check if priority level is valid"""
        valid_priorities = [choice[0] for choice in Notification.PRIORITY_LEVELS]
        return priority in valid_priorities

    @staticmethod
    def validate_delivery_channels(channels: List[str]) -> bool:
        """Check if all delivery channels are valid"""
        valid_channels = [choice[0] for choice in Notification.DELIVERY_CHANNELS]
        return all(channel in valid_channels for channel in channels)

    @staticmethod
    def validate_user_preferences(preferences: Dict) -> List[str]:
        """Validate user notification preferences and return list of errors"""
        errors = []

        # Check required fields
        if "notification_types" not in preferences:
            errors.append("notification_types field is required")

        # Validate notification type preferences
        if "notification_types" in preferences:
            notification_types = preferences["notification_types"]
            if not isinstance(notification_types, dict):
                errors.append("notification_types must be a dictionary")
            else:
                valid_type_categories = [
                    "booking_updates",
                    "payment_updates",
                    "job_updates",
                    "messages",
                    "bids",
                    "marketing",
                ]

                for category in notification_types:
                    if category not in valid_type_categories:
                        errors.append(f"Invalid notification type category: {category}")

        # Validate channel preferences
        for channel in [
            "email_notifications",
            "sms_notifications",
            "push_notifications",
        ]:
            if channel in preferences and not isinstance(preferences[channel], bool):
                errors.append(f"{channel} must be a boolean value")

        return errors


class NotificationBatchProcessor:
    """Utility class for processing notifications in batches"""

    @staticmethod
    def send_bulk_notifications(
        notification_data: List[Dict], batch_size: int = 100, delay_seconds: int = 1
    ) -> Dict:
        """
        Send multiple notifications in batches to avoid overwhelming the system.

        Args:
            notification_data: List of dicts with notification parameters
            batch_size: Number of notifications to process at once
            delay_seconds: Delay between batches

        Returns:
            Dict with success/error counts
        """
        from .services import NotificationService
        import time

        results = {
            "total": len(notification_data),
            "success": 0,
            "errors": 0,
            "error_details": [],
        }

        for i in range(0, len(notification_data), batch_size):
            batch = notification_data[i : i + batch_size]

            for data in batch:
                try:
                    NotificationService.create_notification(**data)
                    results["success"] += 1
                except Exception as e:
                    results["errors"] += 1
                    results["error_details"].append({"data": data, "error": str(e)})
                    logger.error(f"Failed to create notification: {str(e)}")

            # Add delay between batches
            if i + batch_size < len(notification_data):
                time.sleep(delay_seconds)

        return results

    @staticmethod
    def cleanup_old_notifications(days_old: int = 30, batch_size: int = 1000) -> int:
        """Clean up old read notifications"""
        cutoff_date = timezone.now() - timedelta(days=days_old)

        total_deleted = 0
        while True:
            # Get batch of old notifications
            old_notifications = list(
                Notification.objects.filter(read=True, read_at__lt=cutoff_date)[
                    :batch_size
                ].values_list("id", flat=True)
            )

            if not old_notifications:
                break

            # Delete batch
            deleted_count = Notification.objects.filter(
                id__in=old_notifications
            ).delete()[0]

            total_deleted += deleted_count

            if deleted_count < batch_size:
                break

        return total_deleted


# Convenience functions for common operations
def format_notification_content(
    notification_type: str, context: Dict
) -> Dict[str, str]:
    """Format notification title and message"""
    return {
        "title": NotificationFormatter.format_notification_title(
            notification_type, context
        ),
        "message": NotificationFormatter.format_notification_message(
            notification_type, context
        ),
    }


def send_email_notification(notification: Notification, **extra_context) -> bool:
    """Send email for a notification"""
    try:
        rendered = NotificationTemplateRenderer.render_notification_email(
            notification, **extra_context
        )

        email = EmailMultiAlternatives(
            subject=rendered["subject"],
            body=rendered["text"],
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[notification.user.email],
        )
        email.attach_alternative(rendered["html"], "text/html")
        email.send(fail_silently=False)

        notification.mark_as_delivered("email")
        return True

    except Exception as e:
        logger.error(
            f"Failed to send email for notification {notification.id}: {str(e)}"
        )
        return False


def get_user_unread_count(user) -> Dict[str, int]:
    """Get unread notification counts for a user"""
    return {
        "total": Notification.objects.filter(user=user, read=False).count(),
        "urgent": Notification.objects.filter(
            user=user, read=False, priority__in=["high", "urgent"]
        ).count(),
    }
