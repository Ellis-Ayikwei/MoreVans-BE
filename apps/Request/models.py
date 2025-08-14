from datetime import timezone, datetime, timedelta
import uuid
import random
import string
from django.db import models
from django.conf import settings  # Import settings instead
from apps.Driver.models import Driver
from apps.Location.models import Location
from apps.Notification.models import Notification
from apps.Tracking.models import TrackingUpdate
from apps.Basemodel.models import Basemodel

from django_fsm import FSMField, transition


class Request(Basemodel):
    REQUEST_TYPE_CHOICES = [
        ("biddable", "Biddable"),
        ("instant", "Instant"),
        ("journey", "Journey"),
    ]

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

    PAYMENT_STATUSES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    TIME_SLOT_CHOICES = [
        ("morning", "Morning (8AM - 12PM)"),
        ("afternoon", "Afternoon (12PM - 4PM)"),
        ("evening", "Evening (4PM - 8PM)"),
        ("flexible", "Flexible (Any time)"),
    ]

    PRIORITY_CHOICES = [
        ("standard", "Standard"),
        ("express", "Express"),
        ("same_day", "Same Day"),
        ("scheduled", "Scheduled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    provider = models.ForeignKey(
        "Provider.ServiceProvider", on_delete=models.SET_NULL, null=True, blank=True
    )
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPE_CHOICES)
    status = FSMField(default="draft", choices=STATUS_CHOICES)
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="standard",
        help_text="Priority level of the request",
    )
    service_level = models.CharField(
        max_length=20,
        choices=[
            ("standard", "Standard (2-3 business days)"),
            ("express", "Express (1-2 business days)"),
            ("same_day", "Same Day Delivery"),
            ("scheduled", "Scheduled (Flexible Date)"),
        ],
        default="standard",
    )
    service_type = models.CharField(
        max_length=50, blank=True, help_text="Type of service requested"
    )

    # Contact Information
    contact_name = models.CharField(max_length=255, blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    contact_phone = models.CharField(max_length=20, blank=True, default="")
    booking_code = models.CharField(max_length=20, blank=True)
    # Locations for non-journey requests
    pickup_location = models.ForeignKey(
        Location,
        related_name="pickup_requests_direct",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    dropoff_location = models.ForeignKey(
        Location,
        related_name="dropoff_requests_direct",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Legacy/Multiple Locations through M2M
    pickup_locations = models.ManyToManyField(Location, related_name="pickup_requests")
    dropoff_locations = models.ManyToManyField(
        Location, related_name="dropoff_requests"
    )

    # Timing
    preferred_pickup_date = models.DateField(null=True, blank=True)
    preferred_pickup_time = models.CharField(
        max_length=10, choices=TIME_SLOT_CHOICES, null=True, blank=True
    )
    preferred_pickup_time_window = models.JSONField(
        null=True, blank=True
    )  # Store time window
    preferred_delivery_date = models.DateField(null=True, blank=True)
    preferred_delivery_time = models.CharField(
        max_length=10, choices=TIME_SLOT_CHOICES, null=True, blank=True
    )
    is_flexible = models.BooleanField(
        default=False, help_text="Whether schedule is flexible"
    )

    # Cargo Details
    items_description = models.TextField(blank=True)
    total_weight = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )  # in kg
    dimensions = models.JSONField(null=True, blank=True)  # Store length, width, height
    requires_special_handling = models.BooleanField(default=False)
    special_instructions = models.TextField(blank=True)
    staff_required = models.IntegerField(default=1, null=True, blank=True)

    # Moving items for non-journey requests
    moving_items = models.JSONField(
        null=True, blank=True, help_text="JSON array of moving items"
    )

    # Photos
    photo_urls = models.JSONField(null=True, blank=True, help_text="List of photo URLs")

    # Pricing
    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, default=0.0
    )
    final_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_factors = models.JSONField(
        null=True, blank=True
    )  # Store factors affecting price

    # Additional Fields
    tracking_number = models.CharField(
        max_length=60, unique=True, blank=True, null=True
    )
    insurance_required = models.BooleanField(default=False)
    insurance_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUSES, default="pending"
    )
    cancellation_reason = models.TextField(blank=True)
    cancellation_time = models.DateTimeField(null=True, blank=True)
    cancellation_fee = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    route_optimization_data = models.JSONField(null=True, blank=True)
    weather_conditions = models.JSONField(null=True, blank=True)
    carbon_footprint = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )

    estimated_fuel_consumption = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )

    estimated_completion_time = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.DurationField(null=True, blank=True)

    estimated_distance = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    route_waypoints = models.JSONField(null=True, blank=True)
    loading_time = models.DurationField(null=True, blank=True)
    unloading_time = models.DurationField(null=True, blank=True)
    # applied_promotions = models.ManyToManyField('Promotion')
    price_breakdown = models.JSONField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Generate tracking number if not already set
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()

        # Initialize moving items if needed
        if self.request_type == "instant" and not self.moving_items:
            self.moving_items = []

        # Validate dates
        if self.preferred_pickup_date:
            today = datetime.now().date()
            if self.preferred_pickup_date < today:
                raise ValueError("Pickup date cannot be in the past")

            # If it's a same-day request, ensure it's today
            if self.priority == "same_day" and self.preferred_pickup_date != today:
                raise ValueError("Same-day requests must be for today")

            # If it's an express request, ensure it's within next 2 days
            if self.priority == "express":
                max_date = today + timedelta(days=2)
                if self.preferred_pickup_date > max_date:
                    raise ValueError("Express requests must be within 2 days")

        super().save(*args, **kwargs)

    def generate_tracking_number(self):
        """
        Generates a unique tracking number for the request.
        Format: MV-{YEAR}{MONTH}{DAY}-{REQUEST_ID}-{RANDOM_CHARS}
        Example: MV-20250421-12345-XY2Z
        """
        if self.tracking_number and self.tracking_number.strip():
            return self.tracking_number

        # Get current date
        now = datetime.now()
        date_part = now.strftime("%Y%m%d")

        # Get request ID, padded to 5 digits
        # Use a temporary ID if this is a new object
        id_part = str(self.id or random.randint(10000, 99999)).zfill(5)

        # Generate 4 random alphanumeric characters
        random_chars = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=8)
        )

        # Combine parts to form tracking number
        tracking_number = f"MV-{random_chars}"

        # Check for uniqueness
        while (
            Request.objects.filter(tracking_number=tracking_number)
            .exclude(id=self.id)
            .exists()
        ):
            random_chars = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=4)
            )
            tracking_number = f"MV-{date_part}-{id_part}-{random_chars}"

        return tracking_number

    def calculate_base_price(self):
        """Calculate the base job price (what providers get paid) based on distance, weight, and type"""
        from apps.pricing.services import PricingService

        # Get active pricing configuration
        active_config = PricingService.get_active_configuration()
        if not active_config:
            raise ValueError("No active pricing configuration found")

        # Get base price from configuration (this is the base job price)
        base_price = float(active_config.base_price)

        # Different calculation based on request type
        if self.request_type == "journey":
            # For journey, calculate based on total distance and items
            if self.estimated_distance:
                # Get distance factor from configuration
                distance_factor = active_config.distance_factors.filter(
                    is_active=True
                ).first()
                if distance_factor:
                    base_price += float(self.estimated_distance) * float(
                        distance_factor.base_rate_per_km
                    )

            # Add fees for each stop
            stop_count = self.stops.count()
            if stop_count > 2:  # More than pickup and dropoff
                base_price += (stop_count - 2) * 10  # £10 for each additional stop

            # Add item based pricing
            item_count = self.get_total_item_count()
            base_price += item_count * 5  # £5 per item
        else:
            # For instant/biddable requests
            # Add distance factor
            if self.estimated_distance:
                distance_factor = active_config.distance_factors.filter(
                    is_active=True
                ).first()
                if distance_factor:
                    base_price += float(self.estimated_distance) * float(
                        distance_factor.base_rate_per_km
                    )

            # Add weight factor
            if self.total_weight:
                weight_factor = active_config.weight_factors.filter(
                    is_active=True
                ).first()
                if weight_factor:
                    base_price += float(self.total_weight) * float(
                        weight_factor.base_rate_per_kg
                    )

        # Get service level multiplier from configuration
        service_level_factor = active_config.service_level_factors.filter(
            is_active=True, service_level=self.service_level
        ).first()
        if service_level_factor:
            base_price *= float(service_level_factor.price_multiplier)

        # Get priority multiplier from configuration
        priority_factor = active_config.service_level_factors.filter(
            is_active=True, service_level=self.priority
        ).first()
        if priority_factor:
            base_price *= float(priority_factor.price_multiplier)

        # Add special handling factor
        if self.requires_special_handling:
            special_req_factor = active_config.special_requirement_factors.filter(
                is_active=True
            ).first()
            if special_req_factor:
                base_price *= float(special_req_factor.fragile_items_multiplier)

        # Add fuel surcharge
        fuel_surcharge = base_price * (
            float(active_config.fuel_surcharge_percentage) / 100
        )
        base_price += fuel_surcharge

        # Add carbon offset
        carbon_offset = base_price * (float(active_config.carbon_offset_rate) / 100)
        base_price += carbon_offset

        # Ensure minimum price
        base_price = max(base_price, float(active_config.min_price))

        # Apply maximum price constraint
        max_price = base_price * float(active_config.max_price_multiplier)
        base_price = min(base_price, max_price)

        self.base_price = round(base_price, 2)
        return self.base_price

    def calculate_base_job_price_from_final_price(self):
        """Calculate the base job price (what providers get paid) from the final customer price"""
        from apps.Request.driver_compensation import calculate_driver_payment_simple

        # Use the new clean driver compensation service
        final_price = self.final_price or self.base_price or 0
        base_job_price = calculate_driver_payment_simple(self, final_price)

        # Update the base price field
        self.base_price = base_job_price
        return self.base_price

    def get_total_item_count(self):
        """Get the total number of items in the request"""
        count = 0

        # Count items from journey stops
        count += sum(stop.pickup_items.count() for stop in self.stops.all())

        # Count moving items (for non-journey requests)
        if self.moving_items and isinstance(self.moving_items, list):
            count += len(self.moving_items)

        # Count related RequestItem objects
        count += self.items.count()

        return count

    def get_or_add_base_price(self):
        """Get the base price for the request"""
        print(f"Getting or adding base price for request {self.id}")
        if not self.base_price:
            self.calculate_base_price()
            self.base_price = self.calculate_base_price()
            self.save()
        print(f"Base price for request {self.id}: {self.base_price}")
        return self.base_price

    def update_status(self, new_status):
        """Update request status and handle notifications"""
        if new_status not in dict(self.STATUS_CHOICES).keys():
            raise ValueError(f"Invalid status: {new_status}")

        old_status = self.status
        self.status = new_status

        # Update payment status based on request status
        if new_status == "cancelled":
            self.payment_status = "failed"
        elif new_status == "completed":
            # Only update to completed if there was a successful payment
            if self.payments.filter(status="completed").exists():
                self.payment_status = "completed"

        self.save()

        # Create tracking update
        TrackingUpdate.objects.create(
            request=self,
            update_type="status",
            status_message=f"Status changed from {old_status} to {new_status}",
        )

        # Create notifications for relevant parties
        Notification.objects.create(
            user=self.user,
            notification_type="request_update",
            title="Request Status Update",
            message=f"Your request status has been updated to {new_status}",
            data={"request_id": self.id, "status": new_status},
        )

        if self.driver:
            Notification.objects.create(
                user=self.driver.user,
                notification_type="request_update",
                title="Request Status Update",
                message=f"Request status has been updated to {new_status}",
                data={"request_id": self.id, "status": new_status},
            )

    def get_all_locations(self):
        """Return all locations associated with this request"""
        locations = []
        for stop in self.stops.all():
            if stop.location:
                location_data = {
                    "id": stop.id,
                    "type": stop.type,
                    "address": stop.location.address or "Unknown location",
                    "postcode": stop.location.postcode,
                    "latitude": stop.location.latitude,
                    "longitude": stop.location.longitude,
                    "contact_name": stop.location.contact_name,
                    "contact_phone": stop.location.contact_phone,
                    "special_instructions": stop.location.special_instructions,
                    "unit_number": stop.unit_number,
                    "floor": stop.floor,
                    "has_elevator": stop.has_elevator,
                    "parking_info": stop.parking_info,
                    "instructions": stop.instructions,
                    "estimated_time": (
                        stop.scheduled_time.strftime("%H:%M")
                        if stop.scheduled_time
                        else None
                    ),
                    "property_type": stop.property_type,
                    "number_of_rooms": stop.number_of_rooms,
                    "number_of_floors": stop.number_of_floors,
                    "service_type": stop.service_type,
                    "sequence": stop.sequence,
                }
                locations.append(location_data)
        return locations

    def get_journey_stops(self):
        """Get all journey stops in sequence order"""
        return self.stops.all().order_by("sequence")

    @transition(field=status, source="draft", target="pending")
    def submit(self):
        """Submit the request for processing"""
        # Set submission timestamp
        self.submitted_at = datetime.now(timezone.utc)

        # Calculate price using the pricing service
        from pricing.views import PricingConfigurationViewSet
        from pricing.serializers import PriceCalculationSerializer

        # Prepare data for price calculation
        price_data = {
            "distance": (
                float(self.estimated_distance) if self.estimated_distance else 0
            ),
            "weight": float(self.total_weight) if self.total_weight else 0,
            "service_level": self.service_level,
            "staff_required": self.staff_required or 1,
            "property_type": (
                self.pickup_location.property_type if self.pickup_location else "other"
            ),
            "number_of_rooms": (
                self.pickup_location.number_of_rooms if self.pickup_location else 1
            ),
            "floor_number": self.pickup_location.floor if self.pickup_location else 0,
            "has_elevator": (
                self.pickup_location.has_elevator if self.pickup_location else False
            ),
            "loading_time": self.loading_time,
            "unloading_time": self.unloading_time,
            "weather_condition": (
                self.weather_conditions.get("condition", "normal")
                if self.weather_conditions
                else "normal"
            ),
            "has_fragile_items": any(item.fragile for item in self.items.all()),
            "requires_assembly": any(
                item.needs_disassembly for item in self.items.all()
            ),
            "requires_special_equipment": self.requires_special_handling,
            "insurance_required": self.insurance_required,
            "insurance_value": (
                float(self.insurance_value) if self.insurance_value else 0
            ),
            "pickup_city": self.pickup_location.city if self.pickup_location else None,
            "dropoff_city": (
                self.dropoff_location.city if self.dropoff_location else None
            ),
            "carbon_offset": True,  # Default to True for environmental responsibility
            "request_id": self.id,
        }

        # Validate price data
        serializer = PriceCalculationSerializer(data=price_data)
        if not serializer.is_valid():
            raise ValueError(f"Invalid price calculation data: {serializer.errors}")

        # Create a request-like object to pass to the pricing view
        pricing_request = type("Request", (), {"data": serializer.validated_data})()
        pricing_view = PricingConfigurationViewSet()
        response = pricing_view.calculate_price(pricing_request)

        if response.status_code == 200:
            price_data = response.data
            self.base_price = price_data["total_price"]
            self.price_breakdown = price_data["price_breakdown"]

            # Print the price in yellow after it's generated
            print("\033[93m" + f"Request Price: £{self.base_price:.2f}" + "\033[0m")
            if self.price_breakdown:
                print("\033[93m" + "Price Breakdown:" + "\033[0m")
                for key, value in self.price_breakdown.items():
                    print("\033[93m" + f"  {key}: £{value:.2f}" + "\033[0m")
        else:
            raise ValueError("Failed to calculate price")

        # Generate tracking number if not already set
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()

        # Save all changes
        self.save()

        # Notify admins of new request
        # Implementation depends on your notification system

    @transition(field=status, source=["pending", "bidding"], target="accepted")
    def accept(self):
        """Mark the request as accepted"""
        # Implementation
        pass

    @transition(field=status, source=["pending", "accepted"], target="cancelled")
    def cancel(self, reason=None):
        """Cancel the request"""
        self.cancellation_reason = reason
        self.cancellation_time = timezone.now()

        # Update payment status to failed when request is cancelled
        self.payment_status = "failed"
        self.save()

        # Cancel any pending payments
        for payment in self.payments.filter(status__in=["pending", "processing"]):
            try:
                payment.cancel_payment(reason=reason)
            except Exception as e:
                print(f"Error cancelling payment {payment.id}: {str(e)}")

    @transition(field=status, source=["pending"], target="payment_completed")
    def complete_payment(self):
        """Mark the request as payment completed and create a job"""
        from apps.Job.models import Job

        # Verify payment status
        latest_payment = self.payments.order_by("-created_at").first()
        if not latest_payment or latest_payment.status != "completed":
            raise ValueError("Cannot complete payment: No successful payment found")

        # Update payment status
        self.payment_status = "completed"
        self.save()

        # Create the job
        try:
            Job.create_job_after_payment(self)
        except Exception as e:
            # Log the error but don't prevent the transition
            print(f"Error creating job after payment completion: {str(e)}")

        # Create tracking update
        TrackingUpdate.objects.create(
            request=self,
            update_type="payment",
            status_message="Payment completed successfully",
        )

    def confirm_as_job(self, **kwargs):
        """Confirm the request as a job"""
        from apps.Job.models import Job

        # Check if the request is eligible to be converted to a job
        if self.status not in ["accepted", "in_transit"]:
            raise ValueError("Request must be accepted or in transit to confirm as job")

        if self.job:
            raise ValueError("Job Cretad Already")

        # Create a new job instance using strategy service
        from apps.Job.services import JobService

        job = JobService.create_job_with_strategy(self)

        # Update request status
        self.status = "assigned"
        self.save()

        return job

    def generate_booking_code(self):
        """Generate a unique booking code"""
        random_part = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=8)
        )
        code = f"MV-{random_part}"
        return code

    def create_job_from_payment(self, payment):
        """
        Create a job from a completed payment
        Returns the created job or None if job already exists
        """
        from apps.Job.models import Job, TimelineEvent

        # Check if job already exists
        existing_job = Job.objects.filter(request=self).first()
        if existing_job:
            return existing_job

        # Create job
        job = Job.create_job(
            request_obj=self,
            price=payment.amount,
            status="pending",
            is_instant=self.request_type == "instant",
        )

        # Update request status based on payment type
        old_status = self.status
        self.payment_status = "completed"

        if payment.payment_type == "deposit":
            if self.status == "draft":
                self.status = "pending"
        elif payment.payment_type in ["full_payment", "final_payment"]:
            if self.status in ["draft", "pending"]:
                self.status = "accepted"

        # Save request if status changed
        if old_status != self.status or self.payment_status != "completed":
            self.save()

        # Add timeline event
        try:
            TimelineEvent.objects.create(
                job=job,
                event_type="payment_processed",
                description=f"Job created from payment {payment.id}",
                visibility="all",
                metadata={
                    "payment_id": payment.id,
                    "payment_amount": str(payment.amount),
                    "payment_type": payment.payment_type,
                    "manually_triggered": True,
                },
            )
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create timeline event: {str(e)}")

        return job

    def get_or_create_job_from_payments(self):
        """
        Get existing job or create one from the most recent completed payment
        Returns the job object
        """
        from apps.Job.models import Job
        from apps.Payment.models import Payment

        # Check if job already exists
        existing_job = Job.objects.filter(request=self).first()
        if existing_job:
            return existing_job

        # Get the most recent completed payment
        latest_payment = (
            Payment.objects.filter(request=self, status="completed")
            .order_by("-completed_at")
            .first()
        )

        if latest_payment:
            return self.create_job_from_payment(latest_payment)

        return None

    @staticmethod
    def reconcile_statuses(
        date_from=None, date_to=None, status_filter=None, stripe_service=None
    ):
        """
        Reconcile request statuses by checking payments and jobs.
        This function checks for inconsistencies and fixes them:
        1. Requests with completed payments but wrong status
        2. Requests with jobs but wrong status
        3. Requests stuck in processing state
        4. Requests with mismatched payment status

        Args:
            date_from: Optional start date for filtering requests
            date_to: Optional end date for filtering requests
            status_filter: Optional status to filter requests
            stripe_service: Optional StripeService instance for payment polling

        Returns:
            dict: Summary of reconciliation actions taken
        """
        from apps.Payment.models import Payment
        from apps.Job.models import Job
        from django.utils import timezone
        from django.db.models import Q

        summary = {
            "total_checked": 0,
            "status_updated": 0,
            "payment_fixed": 0,
            "jobs_created": 0,
            "payments_polled": 0,
            "errors": [],
            "details": [],
        }

        # Build filter query
        filter_query = Q(status__in=["pending", "draft", "payment_completed"]) | Q(
            payment_status="pending"
        )

        if date_from:
            filter_query &= Q(created_at__gte=date_from)
        if date_to:
            filter_query &= Q(created_at__lte=date_to)
        if status_filter:
            filter_query &= Q(status=status_filter)

        # Get all requests that might need reconciliation
        requests = Request.objects.filter(filter_query)

        summary["total_checked"] = requests.count()

        for request in requests:
            try:
                # Get the latest payment for this request
                latest_payment = (
                    Payment.objects.filter(request=request)
                    .order_by("-created_at")
                    .first()
                )

                # Get associated job
                job = Job.objects.filter(request=request).first()

                action_taken = []

                # Poll payment status if stripe_service is provided
                if (
                    stripe_service
                    and latest_payment
                    and latest_payment.status in ["pending", "processing"]
                ):
                    try:
                        poll_result = stripe_service.poll_payment_status(
                            latest_payment.id
                        )
                        if poll_result["success"]:
                            summary["payments_polled"] += 1
                            if poll_result.get("changes_made"):
                                action_taken.append(
                                    f"Polled payment status: {poll_result['original_status']} -> {poll_result['current_status']}"
                                )
                                # Refresh payment after polling
                                latest_payment.refresh_from_db()
                    except Exception as e:
                        error_msg = (
                            f"Failed to poll payment {latest_payment.id}: {str(e)}"
                        )
                        summary["errors"].append(error_msg)
                        action_taken.append(error_msg)

                # Case 1: Payment completed but request not marked
                if latest_payment and latest_payment.status == "completed":
                    if request.status != "payment_completed":
                        old_status = request.status
                        request.status = "payment_completed"
                        request.payment_status = "completed"
                        request.save()
                        action_taken.append(
                            f"Updated status from {old_status} to payment_completed"
                        )
                        summary["status_updated"] += 1

                # Case 2: Payment completed but no job created
                if request.status == "payment_completed" and not job:
                    try:
                        Job.create_job_after_payment(request)
                        action_taken.append("Created missing job")
                        summary["jobs_created"] += 1
                    except Exception as e:
                        error_msg = (
                            f"Failed to create job for request {request.id}: {str(e)}"
                        )
                        summary["errors"].append(error_msg)
                        action_taken.append(error_msg)

                # Case 3: Request stuck in processing
                processing_timeout = timezone.now() - timezone.timedelta(hours=1)
                if (
                    latest_payment
                    and latest_payment.status == "processing"
                    and latest_payment.created_at < processing_timeout
                ):
                    if stripe_service:
                        try:
                            # Try to poll payment status again with longer timeout
                            poll_result = stripe_service.poll_payment_until_complete(
                                latest_payment.id, max_attempts=5, base_delay=2.0
                            )
                            if poll_result["success"]:
                                summary["payments_polled"] += 1
                                action_taken.append(
                                    f"Resolved stuck payment: {poll_result['original_status']} -> {poll_result['final_status']}"
                                )
                                # Refresh payment after polling
                                latest_payment.refresh_from_db()
                        except Exception as e:
                            error_msg = f"Failed to resolve stuck payment {latest_payment.id}: {str(e)}"
                            summary["errors"].append(error_msg)
                            action_taken.append(error_msg)
                    else:
                        action_taken.append(
                            "Found stuck processing payment (no polling service available)"
                        )
                        summary["payment_fixed"] += 1

                # Case 4: Mismatched payment status
                if latest_payment:
                    # Map Stripe payment status to our defined PAYMENT_STATUSES
                    expected_payment_status = {
                        "completed": "completed",  # Payment model -> Request model status
                        "processing": "pending",
                        "requires_payment_method": "pending",
                        "requires_confirmation": "pending",
                        "requires_action": "pending",
                        "failed": "failed",
                        "cancelled": "failed",  # Treat cancelled as failed
                        "refunded": "refunded",
                        "partially_refunded": "refunded",  # Map partial refunds to refunded since we don't have that status
                    }.get(latest_payment.status, "pending")

                    # Validate that the status is in our choices
                    if (
                        expected_payment_status
                        not in dict(Request.PAYMENT_STATUSES).keys()
                    ):
                        error_msg = (
                            f"Invalid payment status mapping: {expected_payment_status}"
                        )
                        summary["errors"].append(error_msg)
                        action_taken.append(error_msg)
                        expected_payment_status = (
                            "pending"  # Default to pending if invalid
                        )

                    if request.payment_status != expected_payment_status:
                        old_status = request.payment_status
                        request.payment_status = expected_payment_status
                        request.save()
                        action_taken.append(
                            f"Fixed payment status from {old_status} to {expected_payment_status}"
                        )
                        summary["payment_fixed"] += 1

                if action_taken:
                    summary["details"].append(
                        {
                            "request_id": request.id,
                            "tracking_number": request.tracking_number,
                            "actions": action_taken,
                        }
                    )

            except Exception as e:
                error_msg = f"Error processing request {request.id}: {str(e)}"
                summary["errors"].append(error_msg)

        return summary

    def __str__(self):
        return f"{self.tracking_number or 'New'} - {self.request_type}"

    class Meta:
        db_table = "request"
        managed = True
        verbose_name = "Request"
        verbose_name_plural = "Requests"


# Add this new model to your Request/models.py
class MoveMilestone(Basemodel):
    """Tracks different stages of a move and their associated times"""

    MILESTONE_CHOICES = [
        ("preparation", "Preparation"),
        ("loading", "Loading"),
        ("in_transit", "In Transit"),
        ("unloading", "Unloading"),
        ("setup", "Setup"),
        ("completion", "Completion"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("delayed", "Delayed"),
    ]

    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, related_name="milestones"
    )
    milestone_type = models.CharField(max_length=20, choices=MILESTONE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    estimated_duration = models.DurationField(
        help_text="Estimated time to complete this milestone"
    )
    actual_duration = models.DurationField(
        null=True, blank=True, help_text="Actual time taken to complete"
    )
    scheduled_start = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    delay_reason = models.TextField(blank=True, help_text="Reason for any delays")
    sequence = models.IntegerField(
        default=0, help_text="Order of milestones in the move process"
    )

    class Meta:
        db_table = "move_milestone"
        managed = True
        verbose_name = "Move Milestone"
        verbose_name_plural = "Move Milestones"
        ordering = ["sequence"]

    def __str__(self):
        return f"{self.get_milestone_type_display()} - {self.request.tracking_number}"

    def calculate_actual_duration(self):
        """Calculate the actual duration if start and end times are available"""
        if self.actual_start and self.actual_end:
            self.actual_duration = self.actual_end - self.actual_start
            self.save()
        return self.actual_duration

    def update_status(self, new_status):
        """Update milestone status and handle related timestamps"""
        if new_status == "in_progress" and not self.actual_start:
            self.actual_start = timezone.now()
        elif new_status == "completed" and not self.actual_end:
            self.actual_end = timezone.now()
            self.calculate_actual_duration()

        self.status = new_status
        self.save()

    def create_job_if_confirmed(self):
        """
        Checks if the request is confirmed and creates a job if it is.
        Returns the created job or None if not confirmed.
        """
        from apps.Job.models import Job

        if self.status == "confirmed":
            # Check if a job already exists for this request
            existing_job = self.job
            if existing_job:
                return existing_job

            # Create a new job with strategy
            from apps.Job.services import JobService

            job = JobService.create_job_with_strategy(self)
            return job
        return None


class PickupSchedule(Basemodel):
    request = models.ForeignKey("Request", on_delete=models.CASCADE)
    location = models.ForeignKey("Location.Location", on_delete=models.CASCADE)
    # Add other fields needed for pickup scheduling
    objects: models.Manager = models.Manager()


class DropoffSchedule(Basemodel):
    request = models.ForeignKey("Request", on_delete=models.CASCADE)
    location = models.ForeignKey("Location.Location", on_delete=models.CASCADE)
    # Add other fields needed for dropoff scheduling
    objects: models.Manager = models.Manager()
