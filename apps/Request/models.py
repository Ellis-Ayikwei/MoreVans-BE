from datetime import timezone, datetime, timedelta
import uuid
import random
import string
from django.db import models
from apps.Driver.models import Driver
from apps.Location.models import Location
from apps.Notification.models import Notification
from apps.Tracking.models import TrackingUpdate
from apps.Basemodel.models import Basemodel

from apps.User.models import User
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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
        help_text="Priority level of the request"
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
    contact_name = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
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
    estimated_completion_time = models.DateTimeField(null=True, blank=True)
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
    stuff_required = models.IntegerField(default=0, null=True, blank=True)

    # Moving items for non-journey requests
    moving_items = models.JSONField(
        null=True, blank=True, help_text="JSON array of moving items"
    )

    # Photos
    photo_urls = models.JSONField(null=True, blank=True, help_text="List of photo URLs")

    # Pricing
    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
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
    payment_status = models.CharField(max_length=20, default="pending")
    cancellation_reason = models.TextField(blank=True)
    cancellation_time = models.DateTimeField(null=True, blank=True)
    cancellation_fee = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    route_optimization_data = models.JSONField(null=True, blank=True)
    weather_conditions = models.JSONField(null=True, blank=True)
    estimated_fuel_consumption = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    carbon_footprint = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
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
        """Calculate the base price based on distance, weight, and type"""
        from pricing.services import PricingService
        
        # Get active pricing configuration
        active_config = PricingService.get_active_configuration()
        if not active_config:
            raise ValueError("No active pricing configuration found")

        # Get base price from configuration
        base_price = float(active_config.base_price)

        # Different calculation based on request type
        if self.request_type == "journey":
            # For journey, calculate based on total distance and items
            if self.estimated_distance:
                # Get distance factor from configuration
                distance_factor = active_config.distance_factors.filter(is_active=True).first()
                if distance_factor:
                    base_price += float(self.estimated_distance) * float(distance_factor.base_rate_per_km)

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
                distance_factor = active_config.distance_factors.filter(is_active=True).first()
                if distance_factor:
                    base_price += float(self.estimated_distance) * float(distance_factor.base_rate_per_km)

            # Add weight factor
            if self.total_weight:
                weight_factor = active_config.weight_factors.filter(is_active=True).first()
                if weight_factor:
                    base_price += float(self.total_weight) * float(weight_factor.base_rate_per_kg)

        # Get service level multiplier from configuration
        service_level_factor = active_config.service_level_factors.filter(
            is_active=True, 
            service_level=self.service_level
        ).first()
        if service_level_factor:
            base_price *= float(service_level_factor.price_multiplier)

        # Get priority multiplier from configuration
        priority_factor = active_config.service_level_factors.filter(
            is_active=True, 
            service_level=self.priority
        ).first()
        if priority_factor:
            base_price *= float(priority_factor.price_multiplier)

        # Add special handling factor
        if self.requires_special_handling:
            special_req_factor = active_config.special_requirement_factors.filter(is_active=True).first()
            if special_req_factor:
                base_price *= float(special_req_factor.fragile_items_multiplier)

        # Add fuel surcharge
        fuel_surcharge = base_price * (float(active_config.fuel_surcharge_percentage) / 100)
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

    def update_status(self, new_status):
        """Update request status and handle notifications"""
        if new_status not in dict(self.STATUS_CHOICES).keys():
            raise ValueError(f"Invalid status: {new_status}")

        old_status = self.status
        self.status = new_status
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
            location_data = {
                "id": stop.id,
                "type": stop.type,
                "address": stop.address or "Unknown location",
                "unit_number": stop.unit_number,
                "floor": stop.floor,
                "has_elevator": stop.has_elevator,
                "parking_info": stop.parking_info,
                "instructions": stop.instructions,
                "estimated_time": stop.estimated_time,
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
            "staff_required": self.stuff_required or 1,
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
        self.cancellation_reason = reason or "Cancelled by user"
        self.cancellation_time = datetime.now(timezone.utc)
        # Calculate cancellation fee if applicable

    def generate_booking_code(self):
        """Generate a unique booking code for the request."""
        random_part = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=8)
        )
        code = f"MV-{random_part}"
        return code

    def __str__(self):
        return f"{self.tracking_number or 'New'} - {self.user.username} - {self.request_type}"

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
        if self.status == "confirmed":
            # Check if a job already exists for this request
            existing_job = self.jobs.first()
            if existing_job:
                return existing_job

            # Create a new job
            job = Job.objects.create(
                request=self,
                status="draft",  # Start as draft, will be updated to bidding when ready
                bidding_end_time=None,  # Will be set when bidding starts
                minimum_bid=None,  # Will be set based on request details
                preferred_vehicle_types=self.vehicle_type,  # Use the request's vehicle type
                required_qualifications=self.required_qualifications,  # Copy from request
                notes=f"Job created for request {self.tracking_number}",
            )
            return job
        return None


class PickupSchedule(models.Model):
    request = models.ForeignKey("Request", on_delete=models.CASCADE)
    location = models.ForeignKey("Location.Location", on_delete=models.CASCADE)
    # Add other fields needed for pickup scheduling


class DropoffSchedule(models.Model):
    request = models.ForeignKey("Request", on_delete=models.CASCADE)
    location = models.ForeignKey("Location.Location", on_delete=models.CASCADE)
    # Add other fields needed for dropoff scheduling
