from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
import logging

from apps.Payment.models import Payment
from apps.Job.models import Job, TimelineEvent

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def handle_payment_status_change(sender, instance, created, **kwargs):
    """
    Signal handler that listens to payment status changes and creates jobs when payments are completed
    """
    # Only process if this is a payment status change (not creation)
    if created:
        return

    # Check if payment status changed to completed
    if instance.status == "completed" and instance.completed_at:
        try:
            with transaction.atomic():
                request_obj = instance.request

                # Check if job already exists for this request
                existing_job = Job.objects.filter(request=request_obj).first()

                if existing_job:
                    logger.info(
                        f"Job already exists for request {request_obj.id}, skipping auto-creation"
                    )
                    return

                # Create job
                job = Job.create_job(
                    request_obj=request_obj,
                    price=instance.amount,
                    status="pending",
                    is_instant=request_obj.request_type == "instant",
                )

                # Update request status based on payment type
                old_status = request_obj.status
                request_obj.payment_status = "completed"

                if instance.payment_type == "deposit":
                    if request_obj.status == "draft":
                        request_obj.status = "pending"
                elif instance.payment_type in ["full_payment", "final_payment"]:
                    if request_obj.status in ["draft", "pending"]:
                        request_obj.status = "accepted"

                # Save request if status changed
                if (
                    old_status != request_obj.status
                    or request_obj.payment_status != "completed"
                ):
                    request_obj.save()

                # Add timeline event
                try:
                    TimelineEvent.objects.create(
                        job=job,
                        event_type="payment_processed",
                        description=f"Job auto-created from payment {instance.id}",
                        visibility="all",
                        metadata={
                            "payment_id": instance.id,
                            "payment_amount": str(instance.amount),
                            "payment_type": instance.payment_type,
                            "auto_synced": True,
                            "signal_triggered": True,
                        },
                    )
                except Exception as e:
                    logger.warning(f"Failed to create timeline event: {str(e)}")

                logger.info(
                    f"Auto-created job {job.id} for request {request_obj.id} from payment {instance.id}"
                )

        except Exception as e:
            logger.error(
                f"Error in payment status change signal for payment {instance.id}: {str(e)}"
            )


@receiver(post_save, sender=Payment)
def update_request_payment_status(sender, instance, created, **kwargs):
    """
    Signal handler to update request payment status when payment status changes
    """
    if not created and instance.request:
        try:
            request_obj = instance.request

            # Update request payment status based on payment status
            if instance.status == "completed":
                request_obj.payment_status = "completed"
            elif instance.status == "failed":
                request_obj.payment_status = "failed"
            elif instance.status in ["refunded", "partially_refunded"]:
                request_obj.payment_status = "refunded"
            elif instance.status == "pending":
                request_obj.payment_status = "pending"

            # Save request if payment status changed
            if request_obj.payment_status != instance.request.payment_status:
                request_obj.save()
                logger.info(
                    f"Updated request {request_obj.id} payment status to {request_obj.payment_status}"
                )

        except Exception as e:
            logger.error(
                f"Error updating request payment status for payment {instance.id}: {str(e)}"
            )


@receiver(post_save, sender=Payment)
def handle_payment_completion_notification(sender, instance, created, **kwargs):
    """
    Signal handler to send notifications when payments are completed
    """
    if not created and instance.status == "succeeded" and instance.completed_at:
        try:
            from apps.Notification.models import Notification

            request_obj = instance.request
            user = request_obj.user

            if user:
                # Create notification for user
                Notification.objects.create(
                    user=user,
                    title="Payment Completed",
                    message=f"Your payment of £{instance.amount} has been completed successfully. Your job is now being processed.",
                    notification_type="payment_success",
                    related_object_type="payment",
                    related_object_id=instance.id,
                )

                logger.info(
                    f"Created payment completion notification for user {user.id}"
                )

        except Exception as e:
            logger.error(
                f"Error creating payment completion notification for payment {instance.id}: {str(e)}"
            )
