from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from apps.Basemodel.models import Basemodel
from apps.Provider.models import ServiceProvider
from apps.Driver.models import Driver


class Vehicle(Basemodel):
    """
    Vehicle model for tracking fleet vehicles in the MoreVans system.
    Includes UK-specific regulatory fields and business logic.
    """

    # Vehicle types aligned with UK classifications

    FUEL_TYPES = [
        ("diesel", "Diesel"),
        ("petrol", "Petrol"),
        ("electric", "Electric"),
        ("hybrid", "Hybrid"),
        ("plugin_hybrid", "Plug-in Hybrid"),
        ("hydrogen", "Hydrogen"),
        ("lpg", "LPG"),
        ("cng", "CNG"),
    ]

    TRANSMISSION_TYPES = [
        ("manual", "Manual"),
        ("automatic", "Automatic"),
    ]

    COMPLIANCE_STATUSES = [
        ("compliant", "Compliant"),
        ("non_compliant", "Non-Compliant"),
        ("exempt", "Exempt"),
    ]

    # Core vehicle identity
    registration = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                r"^[A-Z0-9 ]{1,10}$", "Valid UK vehicle registration required"
            )
        ],
        help_text="UK Vehicle Registration Number (e.g., AB12 CDE, WK20 ABC, YK23 XYZ)",
    )

    # Vehicle details
    make = models.CharField(max_length=50, help_text="Vehicle manufacturer")
    model = models.CharField(max_length=50, help_text="Vehicle model")
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1980), MaxValueValidator(2030)],
        help_text="Year of manufacture",
    )
    seats = models.IntegerField(default=2)
    vehicle_type = models.ForeignKey(
        "CommonItems.VehicleType", on_delete=models.SET_NULL, null=True, blank=True
    )
    vehicle_category = models.ForeignKey(
        "CommonItems.VehicleCategory", on_delete=models.SET_NULL, null=True, blank=True
    )
    fuel_type = models.CharField(max_length=15, choices=FUEL_TYPES)
    transmission = models.CharField(max_length=10, choices=TRANSMISSION_TYPES)
    color = models.CharField(max_length=50, blank=True)

    # Capacity details
    payload_capacity_kg = models.PositiveIntegerField(help_text="Maximum payload in kg")
    gross_vehicle_weight_kg = models.PositiveIntegerField(
        help_text="Gross vehicle weight in kg (GVW)"
    )
    max_length_m = models.IntegerField(null=True, blank=True)
    load_volume_m3 = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Load volume in cubic meters"
    )

    # Insurance and fleet management
    insurance_policy_number = models.CharField(max_length=50, blank=True)
    insurance_expiry_date = models.DateField(null=True, blank=True)

    # Equipment and features
    has_tail_lift = models.BooleanField(default=False)
    has_tracking_device = models.BooleanField(default=False)
    has_dash_cam = models.BooleanField(default=False)
    additional_features = models.JSONField(
        null=True, blank=True, help_text="Additional vehicle features"
    )

    # Ownership and assignment
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name="provider_vehicles",
        help_text="Service provider that owns this vehicle",
    )
    primary_driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_vehicles",
        help_text="Driver primarily assigned to this vehicle",
    )
    is_active = models.BooleanField(
        default=True, help_text="Vehicle is currently active in the fleet"
    )

    # Tracking and utilization
    location = models.JSONField(null=True, blank=True, help_text="Last known location")
    last_location_update = models.DateTimeField(null=True, blank=True)
    primary_location = models.JSONField(
        null=True, blank=True, help_text="Primary location where this vehicle is based"
    )
    is_available = models.BooleanField(
        default=True, help_text="Vehicle is available for jobs"
    )

    class Meta:
        db_table = "vehicle"
        managed = True
        verbose_name = _("Vehicle")
        verbose_name_plural = _("Vehicles")
        ordering = ["provider", "registration"]
        indexes = [
            models.Index(fields=["registration"]),
            models.Index(fields=["provider"]),
            models.Index(fields=["vehicle_type"]),
            models.Index(fields=["is_active", "is_available"]),
        ]

    def __str__(self):
        return f"{self.registration} - {self.make} {self.model}"


class VehicleImages(Basemodel):
    """Model for storing vehicle photos (up to 5 photos per vehicle)"""

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(upload_to="vehicle_photos/%Y/%m/")
    description = models.TextField(
        blank=True, help_text="Optional description of the photo"
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order (1-5)")

    class Meta:
        db_table = "vehicle_images"
        managed = True
        verbose_name = "Vehicle Photo"
        verbose_name_plural = "Vehicle Photos"
        ordering = ["vehicle", "order", "-created_at"]

    def __str__(self):
        return f"{self.vehicle.registration} - Photo {self.order}"


class VehicleDocuments(Basemodel):
    """Model for storing vehicle-related documents"""

    DOCUMENT_TYPES = [
        ("log_book", "Log Book"),
        ("mot", "MOT Certificate"),
        ("v5", "V5 Document"),
        ("insurance", "Insurance Certificate"),
        ("service_book", "Service Book"),
        ("other", "Other Document"),
    ]

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document = models.FileField(upload_to="vehicle_documents/%Y/%m/")
    description = models.TextField(
        blank=True, help_text="Optional description of the document"
    )
    expiry_date = models.DateField(
        null=True, blank=True, help_text="Document expiry date if applicable"
    )

    class Meta:
        db_table = "vehicle_documents"
        managed = True
        verbose_name = "Vehicle Document"
        verbose_name_plural = "Vehicle Documents"
        ordering = ["vehicle", "document_type", "-created_at"]
        unique_together = ["vehicle", "document_type"]

    def __str__(self):
        return f"{self.vehicle.registration} - {self.document_type}"
