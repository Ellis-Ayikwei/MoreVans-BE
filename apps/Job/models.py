from django.db import models
from apps.Basemodel.models import Basemodel
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta


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
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    is_completed = models.BooleanField(default=False)
    bidding_end_time = models.DateTimeField(null=True, blank=True)
    minimum_bid = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    preferred_vehicle_types = models.JSONField(null=True, blank=True)
    required_qualifications = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_provider = models.ForeignKey(
        "Provider.ServiceProvider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_jobs",
    )

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")
        ordering = ["-created_at"]
        db_table = "job"
        managed = True

    @staticmethod
    def create_job_after_payment(request_obj):
        """
        Creates a job after payment has been completed for a request.
        If a job already exists for this request, returns the existing job.

        Args:
            request_obj: The Request instance that has been paid for

        Returns:
            Job: The created or existing job instance

        Raises:
            ValueError: If the request is not in a valid state or payment is not completed
        """
        from apps.JourneyStop.models import JourneyStop
        import random

        # Verify request is in a valid state
        if request_obj.payment_status != "completed":
            raise ValueError("Request must have completed payment to create a job")

        # Check if a job already exists for this request
        existing_job = Job.objects.filter(request=request_obj).first()
        if existing_job:
            return existing_job

        # Get location information from journey stops
        pickup_stop = request_obj.stops.filter(type="pickup").first()
        dropoff_stop = request_obj.stops.filter(type="dropoff").first()

        pickup_city = "Unknown location"
        dropoff_city = "Unknown location"

        if pickup_stop and pickup_stop.location:
            pickup_city = pickup_stop.location.address
        if dropoff_stop and dropoff_stop.location:
            dropoff_city = dropoff_stop.location.address

        # Create job title and description
        title = f"Moving Service Request #{request_obj.id}"
        description = f"Moving service job created from request {request_obj.id}"
        if request_obj.total_weight:
            description = f"Moving {request_obj.total_weight}kg of items"

        # TODO A Function Determine if job should be instant (50% chance)
        is_instant = random.choice([True, False])

        # Create the job
        base_price = 0.0
        if request_obj.base_price is not None:
            base_price = request_obj.base_price

        job = Job.objects.create(
            request=request_obj,
            title=title,
            description=description,
            price=base_price,
            status="draft",
            is_instant=is_instant,
            minimum_bid=request_obj.base_price * (0.8 if is_instant else 0.6),
        )

        # Create timeline event
        TimelineEvent.objects.create(
            job=job,
            event_type="created",
            description="Job created after payment completion",
            metadata={
                "request_id": str(request_obj.id),
                "is_instant": is_instant,
                "payment_completed": True,
            },
        )

        # Make the job either instant or biddable
        if is_instant:
            job.make_instant()
        else:
            job.make_biddable(bidding_duration_hours=24, minimum_bid=job.minimum_bid)

        return job

    def accept(self, provider):
        """Accept a job"""
        if self.status == "accepted":
            raise ValueError("Job has already been accepted")

        if self.assigned_provider is not None:
            raise ValueError("Job already has an assigned provider")

        if self.status not in ["pending", "bidding"]:
            raise ValueError(f"Job cannot be accepted from status '{self.status}'")

        self.status = "accepted"
        self.assigned_provider = provider
        self.save()

    def __str__(self):
        return f"Job for {self.request.tracking_number}"

    def make_biddable(self, bidding_duration_hours=24, minimum_bid=None):
        """
        Convert the job to a biddable job with a specified bidding duration.

        Args:
            bidding_duration_hours (int): Duration of the bidding period in hours
            minimum_bid (Decimal, optional): Minimum bid amount for the job
        """
        if self.status != "draft":
            raise ValueError("Only draft jobs can be made biddable")

        self.is_instant = False
        self.status = "bidding"
        self.bidding_end_time = timezone.now() + timedelta(hours=bidding_duration_hours)
        if minimum_bid:
            self.minimum_bid = minimum_bid
        self.save()

        # Create a timeline event
        TimelineEvent.objects.create(
            job=self,
            event_type="status_changed",
            description="Job converted to biddable",
            metadata={
                "bidding_end_time": self.bidding_end_time.isoformat(),
                "minimum_bid": str(self.minimum_bid) if self.minimum_bid else None,
            },
        )

        return True

    def make_instant(self):
        """
        Convert the job to an instant job that can be assigned immediately.
        """
        if self.status != "draft":
            raise ValueError("Only draft jobs can be made instant")

        self.is_instant = True
        self.status = "pending"
        self.bidding_end_time = None
        self.minimum_bid = None
        self.save()

        # Create a timeline event
        TimelineEvent.objects.create(
            job=self,
            event_type="status_changed",
            description="Job converted to instant",
            metadata={"is_instant": True},
        )

        return True

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

    def complete_job(self, completed_by=None):
        """
        Mark a job as completed.

        Args:
            completed_by: The user who marked the job as completed

        Raises:
            ValueError: If job is not in a valid state to be completed
        """
        valid_states = ["in_transit", "assigned"]
        if self.status not in valid_states:
            raise ValueError(
                f"Job can only be completed from states: {', '.join(valid_states)}"
            )

        old_status = self.status
        self.status = "completed"
        self.is_completed = True
        self.save()

        # Create timeline event
        TimelineEvent.objects.create(
            job=self,
            event_type="completed",
            description="Job has been marked as completed",
            created_by=completed_by,
            metadata={
                "completed_at": timezone.now().isoformat(),
                "previous_status": old_status,
            },
        )

    def cancel_job(self, cancelled_by=None, reason=None):
        """
        Cancel a job.

        Args:
            cancelled_by: The user who cancelled the job
            reason: The reason for cancellation

        Raises:
            ValueError: If job is not in a valid state to be cancelled
        """
        invalid_states = ["completed", "cancelled"]
        if self.status in invalid_states:
            raise ValueError(f"Cannot cancel job in state: {self.status}")

        old_status = self.status
        self.status = "cancelled"
        self.save()

        # Create timeline event
        TimelineEvent.objects.create(
            job=self,
            event_type="cancelled",
            description=f"Job cancelled: {reason if reason else 'No reason provided'}",
            created_by=cancelled_by,
            metadata={
                "cancelled_at": timezone.now().isoformat(),
                "previous_status": old_status,
                "reason": reason,
            },
        )

    def start_transit(self, started_by=None):
        """
        Mark a job as in transit.

        Args:
            started_by: The user who started the transit

        Raises:
            ValueError: If job is not in a valid state to start transit
        """
        if self.status != "assigned":
            raise ValueError("Job must be assigned before starting transit")

        old_status = self.status
        self.status = "in_transit"
        self.save()

        # Create timeline event
        TimelineEvent.objects.create(
            job=self,
            event_type="in_transit",
            description="Job is now in transit",
            created_by=started_by,
            metadata={
                "transit_started_at": timezone.now().isoformat(),
                "previous_status": old_status,
            },
        )

    def assign_provider(self, provider, assigned_by=None):
        """
        Assign a provider to the job.

        Args:
            provider: The ServiceProvider instance to assign
            assigned_by: The user making the assignment

        Raises:
            ValueError: If job is not in a valid state for provider assignment
        """
        valid_states = ["pending", "bidding", "accepted"]
        if self.status not in valid_states:
            raise ValueError(f"Cannot assign provider in state: {self.status}")

        if self.assigned_provider:
            raise ValueError("Job already has an assigned provider")

        old_status = self.status
        self.status = "assigned"
        self.assigned_provider = provider
        self.save()

        # Create timeline event
        TimelineEvent.objects.create(
            job=self,
            event_type="provider_assigned",
            description=f"Provider {provider.user.get_full_name()} assigned to job",
            created_by=assigned_by,
            metadata={
                "assigned_at": timezone.now().isoformat(),
                "previous_status": old_status,
                "provider_id": str(provider.id),
            },
        )

    def accept_job(self, accepted_by):
        """
        Mark a job as accepted by a provider.

        Args:
            accepted_by: The user accepting the job

        Raises:
            ValueError: If job is not in a valid state to be accepted
        """
        if self.status not in ["pending", "bidding"]:
            raise ValueError(f"Cannot accept job in state: {self.status}")

        old_status = self.status
        self.status = "accepted"
        self.save()

        # Create timeline event
        TimelineEvent.objects.create(
            job=self,
            event_type="provider_accepted",
            description="Job has been accepted",
            created_by=accepted_by,
            metadata={
                "accepted_at": timezone.now().isoformat(),
                "previous_status": old_status,
            },
        )

    @property
    def can_be_completed(self):
        """Check if job can be completed"""
        return self.status in ["in_transit", "assigned"]

    @property
    def can_be_cancelled(self):
        """Check if job can be cancelled"""
        return self.status not in ["completed", "cancelled"]

    @property
    def can_start_transit(self):
        """Check if job can start transit"""
        return self.status == "assigned"

    @property
    def can_be_assigned(self):
        """Check if provider can be assigned"""
        return self.status in ["pending", "bidding", "accepted"]


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
