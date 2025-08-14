import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .services import NotificationService

logger = logging.getLogger(__name__)


@receiver(post_save, sender="Request.Request")
def handle_request_created(sender, instance, created, **kwargs):
    """Send notification when a new request is created"""
    if created and instance.user:
        try:
            NotificationService.notify_booking_created(
                user=instance.user, request_obj=instance
            )
            logger.info(f"Sent booking created notification for request {instance.id}")
        except Exception as e:
            logger.error(f"Error sending booking created notification: {str(e)}")


@receiver(post_save, sender="Request.Request")
def handle_request_status_change(sender, instance, created, **kwargs):
    """Send notification when request status changes"""
    if not created and instance.user:
        try:
            # Get the previous state from database
            try:
                old_instance = sender.objects.get(pk=instance.pk)
                if hasattr(old_instance, "_state") and old_instance._state.db:
                    # This is an update, check if status changed
                    pass
            except sender.DoesNotExist:
                return

            # Handle specific status changes
            if instance.status == "accepted":
                # Deduplicate: if email for booking_confirmed was already sent for this request, skip
                if not NotificationService.has_sent_email_for(
                    user=instance.user,
                    notification_type="booking_confirmed",
                    related_object_type="request",
                    related_object_id=instance.id,
                ):
                    NotificationService.notify_booking_confirmed(
                        user=instance.user,
                        request_obj=instance,
                        provider=instance.provider,
                    )
            elif instance.status == "cancelled":
                if not NotificationService.has_sent_email_for(
                    user=instance.user,
                    notification_type="booking_cancelled",
                    related_object_type="request",
                    related_object_id=instance.id,
                ):
                    NotificationService.create_notification(
                        user=instance.user,
                        notification_type="booking_cancelled",
                        related_object_type="request",
                        related_object_id=instance.id,
                        action_url=f"/requests/{instance.id}",
                        priority="high",
                        request=instance,
                    )

            logger.info(f"Sent status change notification for request {instance.id}")
        except Exception as e:
            logger.error(f"Error sending request status notification: {str(e)}")


@receiver(post_save, sender="Payment.Payment")
def handle_payment_status_change(sender, instance, created, **kwargs):
    """Send notification when payment status changes"""
    if not created and instance.request and instance.request.user:
        try:
            if instance.status == "completed":
                if not NotificationService.has_sent_email_for(
                    user=instance.request.user,
                    notification_type="payment_confirmed",
                    related_object_type="payment",
                    related_object_id=instance.id,
                ):
                    NotificationService.notify_payment_confirmed(
                        user=instance.request.user, payment_obj=instance
                    )
            elif instance.status == "failed":
                if not NotificationService.has_sent_email_for(
                    user=instance.request.user,
                    notification_type="payment_failed",
                    related_object_type="payment",
                    related_object_id=instance.id,
                ):
                    NotificationService.create_notification(
                        user=instance.request.user,
                        notification_type="payment_failed",
                        related_object_type="payment",
                        related_object_id=instance.id,
                        action_url=f"/payments/{instance.id}",
                        priority="high",
                        payment=instance,
                        amount=instance.amount,
                    )

            logger.info(f"Sent payment notification for payment {instance.id}")
        except Exception as e:
            logger.error(f"Error sending payment notification: {str(e)}")


@receiver(post_save, sender="Provider.ServiceProvider")
def handle_provider_verification(sender, instance, created, **kwargs):
    """Send notification when provider is verified"""
    if not created and instance.user:
        try:
            # Check if verification status changed (you may need to add this field)
            if hasattr(instance, "is_verified") and instance.is_verified:
                if not NotificationService.has_sent_email_for(
                    user=instance.user,
                    notification_type="provider_verified",
                    related_object_type="provider",
                    related_object_id=instance.id,
                ):
                    NotificationService.notify_provider_verified(
                        user=instance.user, provider_obj=instance
                    )
                logger.info(
                    f"Sent provider verification notification for {instance.id}"
                )
        except Exception as e:
            logger.error(f"Error sending provider verification notification: {str(e)}")


@receiver(post_save, sender="Bidding.Bid")
def handle_bid_created(sender, instance, created, **kwargs):
    """Send notification when a new bid is placed"""
    if created and instance.job and instance.job.request and instance.job.request.user:
        try:
            if not NotificationService.has_sent_email_for(
                user=instance.job.request.user,
                notification_type="bid_received",
                related_object_type="bid",
                related_object_id=instance.id,
            ):
                NotificationService.notify_bid_received(
                    user=instance.job.request.user, bid_obj=instance
                )
            logger.info(f"Sent bid received notification for bid {instance.id}")
        except Exception as e:
            logger.error(f"Error sending bid notification: {str(e)}")


@receiver(post_save, sender="Bidding.Bid")
def handle_bid_status_change(sender, instance, created, **kwargs):
    """Send notification when bid status changes"""
    if not created and instance.provider and instance.provider.user:
        try:
            if instance.status == "accepted":
                if not NotificationService.has_sent_email_for(
                    user=instance.provider.user,
                    notification_type="bid_accepted",
                    related_object_type="bid",
                    related_object_id=instance.id,
                ):
                    NotificationService.create_notification(
                        user=instance.provider.user,
                        notification_type="bid_accepted",
                        related_object_type="bid",
                        related_object_id=instance.id,
                        action_url=f"/bids/{instance.id}",
                        priority="high",
                        bid=instance,
                        amount=instance.amount,
                    )
            elif instance.status == "rejected":
                if not NotificationService.has_sent_email_for(
                    user=instance.provider.user,
                    notification_type="bid_rejected",
                    related_object_type="bid",
                    related_object_id=instance.id,
                ):
                    NotificationService.create_notification(
                        user=instance.provider.user,
                        notification_type="bid_rejected",
                        related_object_type="bid",
                        related_object_id=instance.id,
                        action_url=f"/bids/{instance.id}",
                        bid=instance,
                        amount=instance.amount,
                    )

            logger.info(f"Sent bid status notification for bid {instance.id}")
        except Exception as e:
            logger.error(f"Error sending bid status notification: {str(e)}")


@receiver(post_save, sender="Job.Job")
def handle_job_status_change(sender, instance, created, **kwargs):
    """Send notification when job status changes"""
    if not created and instance.request and instance.request.user:
        try:
            # Get old status (you might need to implement this)
            old_status = getattr(instance, "_original_status", None)

            if old_status and old_status != instance.status:
                status_mapping = {
                    "started": "job_started",
                    "in_transit": "job_in_transit",
                    "completed": "job_completed",
                    "cancelled": "job_cancelled",
                }
                notification_type = status_mapping.get(
                    instance.status, "request_update"
                )

                if not NotificationService.has_sent_email_for(
                    user=instance.request.user,
                    notification_type=notification_type,
                    related_object_type="job",
                    related_object_id=instance.id,
                ):
                    NotificationService.notify_job_status_change(
                        user=instance.request.user,
                        job_obj=instance,
                        old_status=old_status,
                        new_status=instance.status,
                    )

                # Also notify the provider if assigned
                if instance.assigned_provider and instance.assigned_provider.user:
                    if not NotificationService.has_sent_email_for(
                        user=instance.assigned_provider.user,
                        notification_type=notification_type,
                        related_object_type="job",
                        related_object_id=instance.id,
                    ):
                        NotificationService.notify_job_status_change(
                            user=instance.assigned_provider.user,
                            job_obj=instance,
                            old_status=old_status,
                            new_status=instance.status,
                        )

            logger.info(f"Sent job status notification for job {instance.id}")
        except Exception as e:
            logger.error(f"Error sending job status notification: {str(e)}")


@receiver(post_save, sender="Message.Message")
def handle_message_created(sender, instance, created, **kwargs):
    """Send notification when a new message is sent"""
    if created and hasattr(instance, "conversation"):
        try:
            # Get conversation participants
            conversation = instance.conversation
            sender_user = instance.sender if hasattr(instance, "sender") else None

            # Notify all participants except the sender
            participants = (
                conversation.participants.exclude(user=sender_user)
                if sender_user
                else conversation.participants.all()
            )

            for participant in participants:
                if participant.user:
                    NotificationService.notify_message_received(
                        user=participant.user, message_obj=instance, sender=sender_user
                    )

            logger.info(f"Sent message notifications for message {instance.id}")
        except Exception as e:
            logger.error(f"Error sending message notification: {str(e)}")


@receiver(post_save, sender="User.User")
def handle_user_verification(sender, instance, created, **kwargs):
    """Send notification when user account is verified"""
    if not created and instance.is_active:
        try:
            # Check if user was just activated (you may need to track this)
            if hasattr(instance, "_was_inactive") and instance._was_inactive:
                if not NotificationService.has_sent_email_for(
                    user=instance,
                    notification_type="account_verified",
                    related_object_type="user",
                    related_object_id=instance.id,
                ):
                    NotificationService.create_notification(
                        user=instance,
                        notification_type="account_verified",
                        related_object_type="user",
                        related_object_id=instance.id,
                        action_url="/dashboard",
                        priority="high",
                    )
                logger.info(
                    f"Sent account verification notification for user {instance.id}"
                )
        except Exception as e:
            logger.error(f"Error sending user verification notification: {str(e)}")


# Signal to track original status for job status changes
@receiver(pre_save, sender="Job.Job")
def track_job_status_changes(sender, instance, **kwargs):
    """Track original status before save"""
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except sender.DoesNotExist:
            instance._original_status = None


# Signal to track user activation status
@receiver(pre_save, sender="User.User")
def track_user_activation(sender, instance, **kwargs):
    """Track if user was inactive before activation"""
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._was_inactive = not original.is_active and instance.is_active
        except sender.DoesNotExist:
            instance._was_inactive = False


# System maintenance notifications (can be triggered manually)
def send_system_maintenance_notification(maintenance_info):
    """Send system maintenance notification to all users"""
    from apps.User.models import User

    try:
        users = User.objects.filter(is_active=True)
        count = 0

        for user in users:
            NotificationService.create_notification(
                user=user,
                notification_type="system_maintenance",
                title="Scheduled System Maintenance",
                message=f"We have scheduled system maintenance on {maintenance_info.get('date', 'TBD')}. Expected downtime: {maintenance_info.get('duration', 'TBD')}.",
                data=maintenance_info,
                priority="normal",
                channels=["in_app", "email"],
                expires_at=maintenance_info.get("expires_at"),
            )
            count += 1

        logger.info(f"Sent system maintenance notification to {count} users")
        return count
    except Exception as e:
        logger.error(f"Error sending system maintenance notifications: {str(e)}")
        return 0


def send_bulk_notification(user_ids, notification_type, title, message, **kwargs):
    """Send bulk notifications to specific users"""
    from apps.User.models import User

    try:
        users = User.objects.filter(id__in=user_ids, is_active=True)
        count = 0

        for user in users:
            NotificationService.create_notification(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                **kwargs,
            )
            count += 1

        logger.info(f"Sent bulk notification to {count} users")
        return count
    except Exception as e:
        logger.error(f"Error sending bulk notifications: {str(e)}")
        return 0
