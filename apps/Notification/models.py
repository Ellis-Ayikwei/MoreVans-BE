from django.db import models
from apps.Basemodel.models import Basemodel
from apps.User.models import User


class Notification(Basemodel):
    NOTIFICATION_TYPES = [
        # Booking/Request Related
        ("booking_created", "Booking Created"),
        ("booking_confirmed", "Booking Confirmed"),
        ("booking_cancelled", "Booking Cancelled"),
        ("request_update", "Request Status Update"),
        # Provider/Job Related
        ("provider_accepted", "Provider Accepted Job"),
        ("provider_assigned", "Provider Assigned"),
        ("job_started", "Job Started"),
        ("job_in_transit", "Job In Transit"),
        ("job_completed", "Job Completed"),
        ("job_cancelled", "Job Cancelled"),
        # Account/Verification Related
        ("account_verified", "Account Verified"),
        ("provider_verified", "Provider Account Verified"),
        ("account_suspended", "Account Suspended"),
        ("account_reactivated", "Account Reactivated"),
        # Payment Related
        ("payment_pending", "Payment Pending"),
        ("payment_confirmed", "Payment Confirmed"),
        ("payment_failed", "Payment Failed"),
        ("payment_refunded", "Payment Refunded"),
        ("deposit_received", "Deposit Received"),
        # Bidding Related
        ("bid_received", "New Bid Received"),
        ("bid_accepted", "Bid Accepted"),
        ("bid_rejected", "Bid Rejected"),
        ("bid_counter_offer", "Counter Offer Made"),
        # Communication Related
        ("message_received", "New Message"),
        ("support_ticket_created", "Support Ticket Created"),
        ("support_ticket_updated", "Support Ticket Updated"),
        # Rating/Review Related
        ("review_received", "New Review Received"),
        ("rating_reminder", "Rating Reminder"),
        # System/Admin Related
        ("system_maintenance", "System Maintenance"),
        ("policy_update", "Policy Update"),
        ("feature_announcement", "New Feature"),
        ("account_warning", "Account Warning"),
        ("system_test", "System Test"),
        # Legacy types for backward compatibility
        ("payment", "Payment Notification"),
        ("bid", "Bid Notification"),
        ("message", "New Message"),
        ("system", "System Notification"),
    ]

    PRIORITY_LEVELS = [
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    DELIVERY_CHANNELS = [
        ("in_app", "In-App Notification"),
        ("email", "Email"),
        ("sms", "SMS"),
        ("push", "Push Notification"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(null=True, blank=True)  # Additional data
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # New fields for enhanced functionality
    priority = models.CharField(
        max_length=10, choices=PRIORITY_LEVELS, default="normal"
    )
    delivery_channels = models.JSONField(
        default=list, help_text="List of channels to deliver notification"
    )
    scheduled_for = models.DateTimeField(
        null=True, blank=True, help_text="Schedule notification for later"
    )
    delivered_at = models.DateTimeField(null=True, blank=True)
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)

    # Related object tracking
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    related_object_id = models.CharField(max_length=100, null=True, blank=True)

    # Action tracking
    action_url = models.URLField(
        null=True, blank=True, help_text="URL for notification action"
    )
    action_text = models.CharField(
        max_length=100, null=True, blank=True, help_text="Text for action button"
    )
    expires_at = models.DateTimeField(
        null=True, blank=True, help_text="When notification expires"
    )

    def __str__(self):
        return str(self.title or f"Notification {self.pk}")

    class Meta:
        db_table = "notification"
        managed = True
        ordering = ["-created_at"]

    def mark_as_read(self):
        from django.utils import timezone

        self.read = True
        self.read_at = timezone.now()
        self.save(update_fields=["read", "read_at"])

    def mark_as_delivered(self, channel=None):
        from django.utils import timezone

        self.delivered_at = timezone.now()
        if channel == "email":
            self.email_sent = True
        elif channel == "sms":
            self.sms_sent = True
        elif channel == "push":
            self.push_sent = True
        self.save()

    def is_expired(self):
        from django.utils import timezone

        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def is_urgent(self):
        return self.priority in ["high", "urgent"]

    @property
    def delivery_status(self):
        """Get delivery status across all channels"""
        status = {}
        channels = self.delivery_channels or []
        if not isinstance(channels, list):
            try:
                channels = list(channels)
            except Exception:
                channels = []

        if "email" in channels:
            status["email"] = self.email_sent
        if "sms" in channels:
            status["sms"] = self.sms_sent
        if "push" in channels:
            status["push"] = self.push_sent
        status["in_app"] = True  # Always available in-app
        return status
