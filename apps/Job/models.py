from django.db import models
from apps.Basemodel.models import Basemodel
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import random
import string
from datetime import datetime
from rest_framework import serializers
from .services import JobTimelineService
from apps.Request.serializer import RequestSerializer


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
    request = models.OneToOneField(
        "Request.Request", on_delete=models.CASCADE, related_name="job"
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    job_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique job identifier with prefix",
    )
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

    def save(self, *args, **kwargs):
        # Generate job number if not already set
        if not self.job_number:
            self.job_number = self.generate_job_number()
        super().save(*args, **kwargs)

    def generate_job_number(self):
        """
        Generates a unique job number.
        Format: JOB-{YYYYMM}-{SEQUENTIAL_NUMBER}
        Example: JOB-202406-001, JOB-202406-002
        """
        if self.job_number and self.job_number.strip():
            return self.job_number

        # Get current date for the prefix
        now = datetime.now()
        date_prefix = now.strftime("%Y%m")

        # Get the count of jobs created this month to generate sequential number
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        jobs_this_month = Job.objects.filter(
            created_at__gte=month_start, job_number__startswith=f"JOB-{date_prefix}-"
        ).count()

        # Generate sequential number (padded to 3 digits)
        sequential_number = str(jobs_this_month + 1).zfill(3)

        # Create the job number
        job_number = f"JOB-{date_prefix}-{sequential_number}"

        # Ensure uniqueness (in case of race conditions)
        counter = 1
        original_job_number = job_number
        while Job.objects.filter(job_number=job_number).exclude(id=self.id).exists():
            counter += 1
            sequential_number = str(jobs_this_month + counter).zfill(3)
            job_number = f"JOB-{date_prefix}-{sequential_number}"

            # Prevent infinite loop
            if counter > 1000:
                # Fallback to random string
                random_suffix = "".join(random.choices(string.digits, k=4))
                job_number = f"JOB-{date_prefix}-{random_suffix}"
                break

        return job_number

    @classmethod
    def generate_alternative_job_number(cls):
        """
        Alternative job number format if you prefer shorter numbers.
        Format: MV-{RANDOM_6_CHARS}
        Example: MV-A1B2C3, MV-X9Y8Z7
        """
        while True:
            # Generate 6 random alphanumeric characters
            random_chars = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=6)
            )
            job_number = f"MV-{random_chars}"

            # Check if it's unique
            if not cls.objects.filter(job_number=job_number).exists():
                return job_number

    @classmethod
    def get_next_job_number_preview(cls):
        """
        Preview what the next job number would be without creating a job.
        Useful for displaying to users before job creation.
        """
        now = datetime.now()
        date_prefix = now.strftime("%Y%m")

        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        jobs_this_month = cls.objects.filter(
            created_at__gte=month_start, job_number__startswith=f"JOB-{date_prefix}-"
        ).count()

        sequential_number = str(jobs_this_month + 1).zfill(3)
        return f"JOB-{date_prefix}-{sequential_number}"

    @staticmethod
    def create_job(request_obj, **kwargs):
        """
        Creates a job after payment has been completed for a request.
        If a job already exists for this request, returns the existing job.

        Args:
            request_obj: The Request instance that has been paid for
            kwargs: Additional arguments for job creation

        Returns:
            Job: The created or existing job instance

        Raises:
            ValueError: If the request is not in a valid state or payment is not completed
        """
        from apps.JourneyStop.models import JourneyStop
        import random

        # Check if a job already exists for this request
        existing_job = Job.objects.filter(request=request_obj).first()
        if existing_job:
            return existing_job

        # Get all stops ordered by sequence
        all_stops = request_obj.stops.all().order_by("sequence")
        pickup_stops = all_stops.filter(type="pickup")
        dropoff_stops = all_stops.filter(type="dropoff")
        intermediate_stops = all_stops.filter(type="intermediate")

        # Get first pickup and last dropoff for job title
        first_pickup = pickup_stops.first()
        last_dropoff = dropoff_stops.last()

        # Build location description
        location_parts = []
        if first_pickup and first_pickup.location:
            location_parts.append(f"from {first_pickup.location.address}")

        if intermediate_stops.exists():
            location_parts.append(
                f"with {intermediate_stops.count()} intermediate stop(s)"
            )

        if last_dropoff and last_dropoff.location:
            location_parts.append(f"to {last_dropoff.location.address}")

        location_description = (
            " ".join(location_parts) if location_parts else "Multiple locations"
        )

        # Create job title and description
        total_stops = all_stops.count()
        title = f"Moving Service Request - {total_stops} stops"

        description_parts = [
            f"Moving service job created from request {request_obj.id}",
            f"Total stops: {total_stops}",
            f"Route: {location_description}",
        ]

        if request_obj.total_weight:
            description_parts.insert(1, f"Total weight: {request_obj.total_weight}kg")

        if pickup_stops.count() > 1:
            description_parts.append(
                f"Multiple pickups: {pickup_stops.count()} locations"
            )

        if dropoff_stops.count() > 1:
            description_parts.append(
                f"Multiple dropoffs: {dropoff_stops.count()} locations"
            )

        description = ". ".join(description_parts)

        # Determine if job should be instant (50% chance, but consider complexity)
        complexity_factor = min(total_stops / 10.0, 0.8)  # Max 80% complexity
        instant_probability = max(0.2, 0.5 - complexity_factor)  # Min 20% chance
        is_instant = random.random() < instant_probability

        # Create the job
        base_price = request_obj.base_price or 0.0

        # Adjust minimum bid based on complexity
        if is_instant:
            minimum_bid_multiplier = 0.8 + (
                complexity_factor * 0.1
            )  # 80-90% for instant
        else:
            minimum_bid_multiplier = 0.6 + (
                complexity_factor * 0.2
            )  # 60-80% for bidding

        minimum_bid = base_price * minimum_bid_multiplier if base_price > 0 else None

        job = Job.objects.create(
            request=request_obj,
            title=title,
            description=description,
            price=kwargs["price"] if kwargs["price"] else base_price,
            status="draft",
            is_instant=kwargs["is_instant"] if kwargs["is_instant"] else is_instant,
            minimum_bid= kwargs["minimum_bid"] if kwargs["minimum_bid"] else minimum_bid,
        )

        # The job_number will be automatically generated in the save() method

        print(f"\033[92mJob created with number: {job.job_number}\033[0m")

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
        return f"{self.job_number} - {self.title}"

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
            self.status = "assigned"
            self.provider = bid.provider
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
        valid_states = ["draft", "pending", "bidding", "accepted", "unassigned"]
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
    def unassign_provider(self, unassigned_by=None):
        """
        Unassign a provider to the job.

        Args:
            provider: The ServiceProvider instance to assign
            assigned_by: The user making the assignment

        Raises:
            ValueError: If job is not in a valid state for provider assignment
        """
        valid_states = ["assigned"]
        if self.status not in valid_states:
            raise ValueError(f"Cannot unassign provider in state: {self.status}")

        if not self.assigned_provider:
            raise ValueError("No Provider is assigned yet")

        old_status = self.status
        self.status = "unassigned"
        self.assigned_provider = None
        self.save()

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


class JobSerializer(serializers.ModelSerializer):
    request = RequestSerializer(read_only=True)
    request_id = serializers.CharField(write_only=True)
    time_remaining = serializers.SerializerMethodField()
    timeline_events = serializers.SerializerMethodField()
    job_number = serializers.CharField(read_only=True)  # Add this if not auto-generated

    class Meta:
        model = Job
        fields = [
            "id",
            "job_number",  # Add job number
            "title",  # Add title
            "description",  # Add description
            "is_instant",  # Add instant flag
            "request",
            "request_id",
            "status",
            "is_completed",  # Add completion status
            "price",
            "minimum_bid",
            "bidding_end_time",
            "preferred_vehicle_types",
            "required_qualifications",
            "notes",
            "assigned_provider",  # Add assigned provider
            "time_remaining",
            "timeline_events",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "job_number", "created_at", "updated_at"]

    def get_time_remaining(self, obj):
        if obj.bidding_end_time:
            from django.utils import timezone

            remaining = obj.bidding_end_time - timezone.now()
            return max(0, remaining.total_seconds())
        return None

    def get_timeline_events(self, obj):
        # Import here to avoid circular imports
        from .services import JobTimelineService

        # Get the requesting user
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        # Get timeline events with proper visibility filtering
        events = JobTimelineService.get_job_timeline(job=obj, user=user)
        return TimelineEventSerializer(events, many=True).data
