import logging
from typing import Dict, List, Optional, Any, Union
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Notification
from apps.User.models import User

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Comprehensive notification service that handles creating, sending, and managing
    notifications across multiple channels (in-app, email, SMS, push).
    """

    # Default templates mapping
    NOTIFICATION_TEMPLATES = {
        # Booking/Request Related
        "booking_created": {
            "subject": "Booking Created Successfully",
            "email_template": "booking_created",
            "default_channels": ["in_app", "email"],
        },
        "booking_confirmed": {
            "subject": "Booking Confirmed",
            "email_template": "booking_confirmed",
            "default_channels": ["in_app", "email", "push"],
        },
        "booking_cancelled": {
            "subject": "Booking Cancelled",
            "email_template": "booking_cancelled",
            "default_channels": ["in_app", "email", "push"],
        },
        # Provider/Job Related
        "provider_accepted": {
            "subject": "Provider Accepted Your Job",
            "email_template": "provider_accepted",
            "default_channels": ["in_app", "email", "push"],
        },
        "provider_assigned": {
            "subject": "Provider Assigned to Your Job",
            "email_template": "provider_assigned",
            "default_channels": ["in_app", "email"],
        },
        "job_started": {
            "subject": "Your Job Has Started",
            "email_template": "job_started",
            "default_channels": ["in_app", "email", "push"],
        },
        "job_in_transit": {
            "subject": "Your Items Are In Transit",
            "email_template": "job_in_transit",
            "default_channels": ["in_app", "push"],
        },
        "job_completed": {
            "subject": "Job Completed Successfully",
            "email_template": "job_completed",
            "default_channels": ["in_app", "email", "push"],
        },
        # Account/Verification Related
        "account_verified": {
            "subject": "Account Verified Successfully",
            "email_template": "account_verified",
            "default_channels": ["in_app", "email"],
        },
        "provider_verified": {
            "subject": "Provider Account Verified",
            "email_template": "provider_verified",
            "default_channels": ["in_app", "email"],
        },
        # Payment Related
        "payment_confirmed": {
            "subject": "Payment Confirmed",
            "email_template": "payment_confirmed",
            "default_channels": ["in_app", "email", "push"],
        },
        "payment_failed": {
            "subject": "Payment Failed",
            "email_template": "payment_failed",
            "default_channels": ["in_app", "email", "push"],
        },
        "deposit_received": {
            "subject": "Deposit Received",
            "email_template": "deposit_received",
            "default_channels": ["in_app", "email"],
        },
        # Bidding Related
        "bid_received": {
            "subject": "New Bid Received",
            "email_template": "bid_received",
            "default_channels": ["in_app", "email", "push"],
        },
        "bid_accepted": {
            "subject": "Your Bid Was Accepted",
            "email_template": "bid_accepted",
            "default_channels": ["in_app", "email", "push"],
        },
        "bid_rejected": {
            "subject": "Bid Update",
            "email_template": "bid_rejected",
            "default_channels": ["in_app", "email"],
        },
        # Communication Related
        "message_received": {
            "subject": "New Message Received",
            "email_template": "message_received",
            "default_channels": ["in_app", "push"],
        },
        # Rating/Review Related
        "review_received": {
            "subject": "New Review Received",
            "email_template": "review_received",
            "default_channels": ["in_app", "email"],
        },
        "rating_reminder": {
            "subject": "Please Rate Your Experience",
            "email_template": "rating_reminder",
            "default_channels": ["in_app", "email"],
        },
        # System/Admin
        "system_test": {
            "subject": "System Test Notification",
            "email_template": "system_test",
            "default_channels": ["in_app", "email"],
        },
    }

    @classmethod
    def create_notification(
        cls,
        user: User,
        notification_type: str,
        title: str = None,
        message: str = None,
        data: Dict = None,
        priority: str = "normal",
        channels: List[str] = None,
        related_object_type: str = None,
        related_object_id: str = None,
        action_url: str = None,
        action_text: str = None,
        scheduled_for: datetime = None,
        expires_at: datetime = None,
        send_immediately: bool = True,
        **context,
    ) -> Notification:
        """
        Create a new notification with smart defaults based on notification type.

        Args:
            user: User to send notification to
            notification_type: Type of notification
            title: Custom title (will use template default if not provided)
            message: Custom message (will use template default if not provided)
            data: Additional data to store with notification
            priority: Priority level ('low', 'normal', 'high', 'urgent')
            channels: Delivery channels (will use template defaults if not provided)
            related_object_type: Type of related object (e.g., 'request', 'job', 'payment')
            related_object_id: ID of related object
            action_url: URL for notification action
            action_text: Text for action button
            scheduled_for: Schedule notification for later
            expires_at: When notification expires
            send_immediately: Whether to send immediately
            **context: Additional context for template rendering
        """
        try:
            # Get template config
            template_config = cls.NOTIFICATION_TEMPLATES.get(notification_type, {})

            # Use template defaults if not provided
            if not title and template_config.get("subject"):
                title = template_config["subject"]

            if not channels:
                channels = template_config.get("default_channels", ["in_app"])

            # Generate message if not provided
            if not message:
                message = cls._generate_message(notification_type, user, context)

            # Create notification
            notification = Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data or {},
                priority=priority,
                delivery_channels=channels,
                related_object_type=related_object_type,
                related_object_id=str(related_object_id) if related_object_id else None,
                action_url=action_url,
                action_text=action_text,
                scheduled_for=scheduled_for,
                expires_at=expires_at,
            )

            logger.info(f"Created notification {notification.id} for user {user.id}")

            # Send immediately if requested and not scheduled
            if send_immediately and not scheduled_for:
                cls.send_notification(notification, **context)

            return notification

        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            raise

    @classmethod
    def send_notification(cls, notification: Notification, **context):
        """Send notification across all specified channels."""
        try:
            # Send to each channel
            for channel in notification.delivery_channels:
                if channel == "email":
                    cls._send_email_notification(notification, **context)
                elif channel == "sms":
                    cls._send_sms_notification(notification, **context)
                elif channel == "push":
                    cls._send_push_notification(notification, **context)
                # in_app is always handled by database storage

            # Mark as delivered
            notification.mark_as_delivered()
            logger.info(f"Sent notification {notification.id} to all channels")

        except Exception as e:
            logger.error(f"Error sending notification {notification.id}: {str(e)}")

    @classmethod
    def _send_email_notification(cls, notification: Notification, **context):
        """Send email notification using templates."""
        try:
            template_config = cls.NOTIFICATION_TEMPLATES.get(
                notification.notification_type, {}
            )
            template_name = template_config.get(
                "email_template", "generic_notification"
            )

            # Prepare context
            email_context = {
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
                "notification_data": notification.data,
                **context,
            }

            # Render templates
            html_content = render_to_string(
                f"emails/notifications/{template_name}.html", email_context
            )
            text_content = render_to_string(
                f"emails/notifications/{template_name}.txt", email_context
            )

            # Create and send email
            email = EmailMultiAlternatives(
                subject=notification.title,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[notification.user.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

            notification.mark_as_delivered("email")
            logger.info(f"Email sent for notification {notification.id}")

        except Exception as e:
            logger.error(
                f"Error sending email for notification {notification.id}: {str(e)}"
            )

    @classmethod
    def _send_sms_notification(cls, notification: Notification, **context):
        """Send SMS notification (placeholder for future implementation)."""
        # TODO: Implement SMS sending using Twilio or similar service
        logger.info(
            f"SMS sending not implemented yet for notification {notification.id}"
        )
        notification.mark_as_delivered("sms")

    @classmethod
    def _send_push_notification(cls, notification: Notification, **context):
        """Send push notification (placeholder for future implementation)."""
        # TODO: Implement push notifications using Firebase or similar
        logger.info(
            f"Push notification sending not implemented yet for notification {notification.id}"
        )
        notification.mark_as_delivered("push")

    @classmethod
    def _generate_message(
        cls, notification_type: str, user: User, context: Dict
    ) -> str:
        """Generate default message based on notification type and context."""
        messages = {
            "booking_created": f"Your booking request has been created successfully. We'll notify you when providers start bidding.",
            "booking_confirmed": f"Great news! Your booking has been confirmed and assigned to a provider.",
            "booking_cancelled": f"Your booking has been cancelled. If this was unexpected, please contact support.",
            "provider_accepted": f"A provider has accepted your job and will be in touch shortly.",
            "provider_assigned": f"We've assigned a provider to your job. They'll contact you with details.",
            "job_started": f"Your job has started! You can track progress in your dashboard.",
            "job_in_transit": f"Your items are now in transit. You'll be notified when they arrive.",
            "job_completed": f"Your job has been completed successfully. Please rate your experience.",
            "account_verified": f"Congratulations! Your account has been verified and is now fully active.",
            "provider_verified": f"Your provider account has been verified. You can now start accepting jobs.",
            "payment_confirmed": f"Your payment has been processed successfully.",
            "payment_failed": f"We couldn't process your payment. Please update your payment method.",
            "deposit_received": f"We've received your deposit. Your booking is now confirmed.",
            "bid_received": f"You've received a new bid on your job. Check it out and decide!",
            "bid_accepted": f"Congratulations! Your bid has been accepted. Time to get to work!",
            "bid_rejected": f"Your bid wasn't selected this time, but don't worry - more opportunities await!",
            "message_received": f"You have a new message. Click to view and respond.",
            "review_received": f"You've received a new review. See what your customer had to say!",
            "rating_reminder": f"How was your experience? We'd love to hear your feedback.",
        }

        return messages.get(notification_type, "You have a new notification.")

    @classmethod
    def has_sent_email_for(
        cls,
        user: User,
        notification_type: str,
        related_object_type: str,
        related_object_id: Any,
    ) -> bool:
        """Check if an email for this notification context has already been sent."""
        try:
            return Notification.objects.filter(
                user=user,
                notification_type=notification_type,
                related_object_type=related_object_type,
                related_object_id=str(related_object_id),
                email_sent=True,
            ).exists()
        except Exception as e:
            logger.error("Error checking sent email for notification: %s", str(e))
            return False

    # Convenience methods for common notification types

    @classmethod
    def notify_booking_created(cls, user: User, request_obj, **kwargs):
        """Notify user that booking was created."""
        return cls.create_notification(
            user=user,
            notification_type="booking_created",
            related_object_type="request",
            related_object_id=request_obj.id,
            action_url=f"/requests/{request_obj.id}",
            request=request_obj,
            **kwargs,
        )

    @classmethod
    def notify_booking_confirmed(cls, user: User, request_obj, provider=None, **kwargs):
        """Notify user that booking was confirmed."""
        return cls.create_notification(
            user=user,
            notification_type="booking_confirmed",
            related_object_type="request",
            related_object_id=request_obj.id,
            action_url=f"/requests/{request_obj.id}",
            priority="high",
            request=request_obj,
            provider=provider,
            **kwargs,
        )

    @classmethod
    def notify_payment_confirmed(cls, user: User, payment_obj, **kwargs):
        """Notify user that payment was confirmed."""
        return cls.create_notification(
            user=user,
            notification_type="payment_confirmed",
            related_object_type="payment",
            related_object_id=payment_obj.id,
            action_url=f"/payments/{payment_obj.id}",
            priority="high",
            payment=payment_obj,
            amount=payment_obj.amount,
            **kwargs,
        )

    @classmethod
    def notify_provider_verified(cls, user: User, provider_obj, **kwargs):
        """Notify provider that their account was verified."""
        return cls.create_notification(
            user=user,
            notification_type="provider_verified",
            related_object_type="provider",
            related_object_id=provider_obj.id,
            action_url="/dashboard/provider",
            priority="high",
            provider=provider_obj,
            **kwargs,
        )

    @classmethod
    def notify_bid_received(cls, user: User, bid_obj, **kwargs):
        """Notify user they received a new bid."""
        return cls.create_notification(
            user=user,
            notification_type="bid_received",
            related_object_type="bid",
            related_object_id=bid_obj.id,
            action_url=f"/jobs/{bid_obj.job.id}/bids",
            priority="high",
            bid=bid_obj,
            amount=bid_obj.amount,
            provider=bid_obj.provider,
            **kwargs,
        )

    @classmethod
    def notify_message_received(cls, user: User, message_obj, sender, **kwargs):
        """Notify user they received a new message."""
        return cls.create_notification(
            user=user,
            notification_type="message_received",
            related_object_type="message",
            related_object_id=message_obj.id,
            action_url=f"/messages/{message_obj.conversation.id if hasattr(message_obj, 'conversation') else message_obj.id}",
            message_obj=message_obj,
            sender=sender,
            **kwargs,
        )

    @classmethod
    def notify_job_status_change(
        cls, user: User, job_obj, old_status, new_status, **kwargs
    ):
        """Notify user about job status changes."""
        notification_type = f"job_{new_status}"

        # Map status to notification types
        status_mapping = {
            "started": "job_started",
            "in_transit": "job_in_transit",
            "completed": "job_completed",
            "cancelled": "job_cancelled",
        }

        notification_type = status_mapping.get(new_status, "request_update")

        return cls.create_notification(
            user=user,
            notification_type=notification_type,
            related_object_type="job",
            related_object_id=job_obj.id,
            action_url=f"/jobs/{job_obj.id}",
            priority="high" if new_status in ["started", "completed"] else "normal",
            job=job_obj,
            old_status=old_status,
            new_status=new_status,
            **kwargs,
        )

    @classmethod
    def notify_system_test(
        cls,
        user: User,
        title: Optional[str] = None,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """Send a simple system test notification to a user."""
        return cls.create_notification(
            user=user,
            notification_type="system_test",
            title=title or "System Test",
            message=message or "This is a test notification from the system.",
            data=data or {},
            related_object_type="system",
            related_object_id=None,
            priority="normal",
            **kwargs,
        )


class NotificationPreferenceService:
    """Service to manage user notification preferences."""

    @classmethod
    def get_user_preferences(cls, user: User) -> Dict:
        """Get user notification preferences."""
        default_prefs = {
            "email_notifications": True,
            "sms_notifications": False,
            "push_notifications": True,
            "notification_types": {
                "booking_updates": True,
                "payment_updates": True,
                "job_updates": True,
                "messages": True,
                "bids": True,
                "marketing": False,
            },
        }

        # Get from user model or use defaults
        prefs = (
            user.notification_preferences
            if hasattr(user, "notification_preferences")
            else {}
        )

        # Merge with defaults
        for key, value in default_prefs.items():
            if key not in prefs:
                prefs[key] = value

        return prefs

    @classmethod
    def update_user_preferences(cls, user: User, preferences: Dict):
        """Update user notification preferences."""
        current_prefs = cls.get_user_preferences(user)
        current_prefs.update(preferences)
        user.notification_preferences = current_prefs
        user.save(update_fields=["notification_preferences"])

    @classmethod
    def should_send_notification(
        cls, user: User, notification_type: str, channel: str
    ) -> bool:
        """Check if user wants to receive this type of notification on this channel."""
        prefs = cls.get_user_preferences(user)

        # Check channel preference
        if channel == "email" and not prefs.get("email_notifications", True):
            return False
        elif channel == "sms" and not prefs.get("sms_notifications", False):
            return False
        elif channel == "push" and not prefs.get("push_notifications", True):
            return False

        # Check notification type preference
        type_prefs = prefs.get("notification_types", {})

        # Map notification types to preference categories
        if notification_type.startswith("booking_") or notification_type.startswith(
            "request_"
        ):
            return type_prefs.get("booking_updates", True)
        elif notification_type.startswith("payment_"):
            return type_prefs.get("payment_updates", True)
        elif notification_type.startswith("job_"):
            return type_prefs.get("job_updates", True)
        elif notification_type.startswith("message_"):
            return type_prefs.get("messages", True)
        elif notification_type.startswith("bid_"):
            return type_prefs.get("bids", True)

        return True
