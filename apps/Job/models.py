from django.db import models
from apps.Basemodel.models import Basemodel
from django.utils.translation import gettext_lazy as _


class Job(Basemodel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending"),
        ("bidding", "Bidding in Progress"),
        ("accepted", "Accepted"),
        ("assigned", "Assigned"),
        ("in_transit", "In Transit"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    is_instant = models.BooleanField(default=False)
    request = models.ForeignKey(
        "Request.Request", on_delete=models.CASCADE, related_name="jobs"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    bidding_end_time = models.DateTimeField(null=True, blank=True)
    minimum_bid = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    preferred_vehicle_types = models.JSONField(null=True, blank=True)
    required_qualifications = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")
        ordering = ["-created_at"]
        db_table = "job"
        managed = True

    def __str__(self):
        return f"Job for {self.request.tracking_number}"

    def start_bidding(self):
        """Start the bidding process for the job"""
        if self.status == "draft":
            self.status = "bidding"
            self.save()
            return True
        return False

    def accept_bid(self, bid):
        """Accept a bid for this job"""
        if self.status == "bidding":
            self.status = "accepted"
            self.save()
            return True
        return False


class TimelineEvent(Basemodel):
    """Tracks events in the job timeline with different visibility levels"""

    EVENT_TYPE_CHOICES = [
        ("created", "Job Created"),
        ("updated", "Job Updated"),
        ("status_changed", "Status Changed"),
        ("provider_assigned", "Provider Assigned"),
        ("provider_accepted", "Provider Accepted"),
        ("job_started", "Job Started"),
        ("in_transit", "In Transit"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("document_uploaded", "Document Uploaded"),
        ("message_sent", "Message Sent"),
        ("payment_processed", "Payment Processed"),
        ("rating_submitted", "Rating Submitted"),
        ("system_notification", "System Notification"),
    ]

    VISIBILITY_CHOICES = [
        ("all", "Visible to All"),
        ("provider", "Provider Only"),
        ("customer", "Customer Only"),
        ("system", "System Only"),
    ]

    job = models.ForeignKey(
        Job, on_delete=models.CASCADE, related_name="timeline_events"
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    description = models.TextField()
    visibility = models.CharField(
        max_length=20, choices=VISIBILITY_CHOICES, default="all"
    )
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "User.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "timeline_event"
        managed = True
        ordering = ["-created_at"]
        verbose_name = "Timeline Event"
        verbose_name_plural = "Timeline Events"

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.job.request.tracking_number}"
