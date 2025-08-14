from django.db import models
from apps.Basemodel.models import Basemodel
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
import string

# Removed unused imports related to serializers and datetime
from apps.Provider.models import ServiceProvider


class JobProviderAcceptance(Basemodel):
    """
    This model is used to track the accepted providers for a job.
    """

    job = models.ForeignKey(
        "Job.Job", on_delete=models.CASCADE, related_name="accepted_provider_links"
    )
    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="accepted_job_links"
    )
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "job_provider_acceptances"
        managed = True
        verbose_name = "Job Provider Acceptance"
        verbose_name_plural = "Job Provider Acceptances"
        unique_together = ("job", "provider")

    def __str__(self):
        return f"JobProviderAcceptance {self.id}"


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
    accepted_providers = models.ManyToManyField(
        "Provider.ServiceProvider",
        related_name="accepted_jobs",
        through="JobProviderAcceptance",
        blank=True,
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), null=True, blank=True
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
        now = timezone.now()
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
        now = timezone.now()
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
        print(f"create_job called with kwargs: {kwargs}")

        # Check if a job already exists for this request
        existing_job = Job.objects.filter(request=request_obj).first()
        print(f"Checking for existing job in create_job method: {existing_job}")
        if existing_job:
            print(f"Returning existing job: {existing_job.id}")
            return existing_job

        # Get all stops ordered by sequence
        all_stops = request_obj.stops.all().order_by("sequence")
        pickup_stops = all_stops.filter(type="pickup")
        dropoff_stops = all_stops.filter(type="dropoff")
        intermediate_stops = all_stops.filter(type="intermediate")

        print(
            f"Stops found: {all_stops.count()} total, {pickup_stops.count()} pickup, {dropoff_stops.count()} dropoff, {intermediate_stops.count()} intermediate"
        )

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
        base_price = request_obj.base_price or Decimal("0.00")
        print(f"Base price: {base_price}, Type: {type(base_price)}")

        # If base price is 0, try to calculate it
        if base_price == Decimal("0.00"):
            print("Base price is 0, attempting to calculate it...")
            try:
                base_price = request_obj.calculate_base_price()
                print(f"Calculated base price: {base_price}")
            except Exception as e:
                print(f"Error calculating base price: {e}")
                # Use a default base price
                base_price = Decimal("50.00")
                print(f"Using default base price: {base_price}")

        # For all jobs, use the base price as the job price (what provider gets paid)
        final_price = base_price

        # Calculate minimum bid based on job type
        if (
            kwargs.get("is_instant", is_instant)
            or request_obj.request_type == "instant"
        ):
            # For instant jobs, minimum bid is 90% of job price
            minimum_bid = base_price * Decimal("0.9") if base_price > 0 else None
        else:
            # For non-instant jobs, use traditional bidding approach
            minimum_bid_multiplier = 0.6 + (
                complexity_factor * 0.2
            )  # 60-80% for bidding
            minimum_bid = (
                base_price * minimum_bid_multiplier if base_price > 0 else None
            )

        print(f"Final price: {final_price}, Minimum bid: {minimum_bid}")
        print(f"Complexity factor: {complexity_factor}, Is instant: {is_instant}")

        job_data = {
            "request": request_obj,
            "title": title,
            "description": description,
            "price": kwargs.get("price", final_price),
            "status": kwargs.get("status", "draft"),
            "is_instant": kwargs.get("is_instant", is_instant),
            "minimum_bid": kwargs.get("minimum_bid", minimum_bid),
        }
        print(f"Creating job with data: {job_data}")
        print(f"About to call Job.objects.create with {len(job_data)} fields")

        try:
            job = Job.objects.create(**job_data)
            print("Job.objects.create() completed successfully")
        except Exception as create_error:
            print(f"Error in Job.objects.create(): {str(create_error)}")
            print(f"Error type: {type(create_error)}")
            import traceback

            print(f"Traceback: {traceback.format_exc()}")
            raise create_error

        # Ensure the job is saved and job number is generated
        job.save()

        print(f"\033[92mJob created with number: {job.job_number}\033[0m")
        print(f"\033[92mJob ID: {job.id}, Status: {job.status}\033[0m")

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
            self.assigned_provider = bid.provider
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
        valid_states = ["draft", "pending", "bidding", "accepted"]
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
        Unassign a provider from the job.

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

        self.status = "pending"
        self.assigned_provider = None
        _ = unassigned_by
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
        return f"TimelineEvent {self.id}"
