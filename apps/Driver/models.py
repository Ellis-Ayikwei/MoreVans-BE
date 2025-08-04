from unittest.mock import Base
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator

from django.db import models
from apps.Basemodel.models import Basemodel
from apps.User.models import User
from apps.Provider.models import ServiceProvider


class Driver(Basemodel):
    """
    Driver model enhanced for UK logistics operations with required compliance fields.
    """

    # Core driver details linked to user account
    # user = models.OneToOneField(
    #     User,
    #     on_delete=models.CASCADE,
    #     related_name="driver_profile",
    #     null=True,
    #     blank=True,
    #     help_text=_("User account associated with this driver"),
    # )

    # Driver basic information
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)
    national_insurance_number = models.CharField(
        max_length=9,
        null=True,
        blank=True,
        # validators=[
        #     RegexValidator(
        #         r"^[A-CEGHJ-PR-TW-Z]{1}[A-CEGHJ-NPR-TW-Z]{1}[0-9]{6}[A-D]{1}$",
        #         "Valid NI number required",
        #     )
        # ],
        help_text=_("National Insurance Number (e.g., AB123456C)"),
    )
    address = models.TextField(blank=True)
    postcode = models.CharField(max_length=10, blank=True)

    # Current location tracking
    location = gis_models.PointField(srid=4326, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)

    # Employment details
    provider = models.ForeignKey(
        ServiceProvider,
        null=True,
        on_delete=models.CASCADE,
        related_name="drivers",
        help_text=_("Service provider this driver works for"),
    )

    EMPLOYMENT_TYPES = [
        ("employee", "Employee"),
        ("contractor", "Self-employed Contractor"),
        ("agency", "Agency Driver"),
        ("temporary", "Temporary Worker"),
    ]

    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPES,
        default="employee",
        help_text=_("Type of employment relationship"),
    )

    date_started = models.DateField(
        default=None, help_text=_("Date driver started with the company")
    )

    # Driver license information - UK specific
    LICENSE_CATEGORIES = [
        ("B", "Category B - Car and small van up to 3.5t"),
        ("C1", "Category C1 - Medium-sized vehicles 3.5-7.5t"),
        ("C", "Category C - Large vehicles over 3.5t"),
        ("C+E", "Category C+E - Large vehicle with trailer"),
        ("D1", "Category D1 - Minibuses"),
        ("D", "Category D - Buses"),
    ]

    license_number = models.CharField(
        null=True, max_length=20, help_text=_("Driver license number")
    )
    license_country_of_issue = models.CharField(
        max_length=50,
        default="United Kingdom",
        help_text=_("Country where license was issued"),
    )
    license_categories = models.JSONField(
        default=list, help_text=_("Categories on driver's license")
    )
    license_expiry_date = models.DateField(
        default=None, help_text=_("License expiry date")
    )
    digital_tachograph_card_number = models.CharField(
        max_length=20, blank=True, help_text=_("Digital tachograph card number")
    )
    tacho_card_expiry_date = models.DateField(
        null=True, blank=True, help_text=_("Tachograph card expiry date")
    )

    # Driver qualifications
    has_cpc = models.BooleanField(
        default=False, help_text=_("Driver has Certificate of Professional Competence")
    )
    cpc_expiry_date = models.DateField(
        null=True, blank=True, help_text=_("CPC qualification expiry date")
    )
    has_adr = models.BooleanField(
        default=False, help_text=_("Qualified for dangerous goods transport (ADR)")
    )
    adr_expiry_date = models.DateField(
        null=True, blank=True, help_text=_("ADR certification expiry date")
    )

    # Training and compliance
    induction_completed = models.BooleanField(default=False)
    induction_date = models.DateField(null=True, blank=True)

    # Working time directive tracking
    max_weekly_hours = models.PositiveIntegerField(
        default=48, help_text=_("Maximum weekly working hours")
    )
    opted_out_of_working_time_directive = models.BooleanField(
        default=False, help_text=_("Driver has opted out of 48-hour working week limit")
    )

    # Driver status
    STATUS_CHOICES = [
        ("available", "Available"),
        ("on_job", "On Job"),
        ("off_duty", "Off Duty"),
        ("on_break", "On Break"),
        ("unavailable", "Unavailable"),
        ("suspended", "Suspended"),
        ("inactive", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available",
        help_text=_("Current driver status"),
    )

    # Verification status
    VERIFICATION_STATUSES = [
        ("unverified", "Unverified"),
        ("pending", "Pending Review"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    ]

    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUSES,
        default="unverified",
        help_text=_("Driver verification status based on document verification"),
    )
    last_verified = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(
        blank=True, help_text=_("Notes about verification process")
    )

    # Driving record
    penalty_points = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(12)],
        help_text=_("Number of penalty points on license"),
    )

    # Additional fields
    preferred_vehicle_types = models.JSONField(
        null=True, blank=True, help_text=_("Preferred vehicle types for this driver")
    )
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        verbose_name = "Driver"
        verbose_name_plural = "Drivers"
        db_table = "driver"
        indexes = [
            models.Index(fields=["provider"]),
            models.Index(fields=["status"]),
            models.Index(fields=["license_expiry_date"]),
        ]

    @property
    def is_license_valid(self):
        """Check if driver's license is currently valid"""
        from django.utils import timezone

        return self.license_expiry_date >= timezone.now().date()

    @property
    def is_cpc_valid(self):
        """Check if driver's CPC qualification is valid"""
        from django.utils import timezone

        if not self.has_cpc or not self.cpc_expiry_date:
            return False
        return self.cpc_expiry_date >= timezone.now().date()

    @property
    def assigned_vehicles(self):
        """Get all vehicles this driver is assigned to as primary driver"""
        return self.primary_vehicles.all()

    @property
    def needs_license_renewal(self):
        """Check if license needs renewal soon (within 30 days)"""
        from django.utils import timezone
        from datetime import timedelta

        if not self.license_expiry_date:
            return False

        thirty_days_from_now = timezone.now().date() + timedelta(days=30)
        return self.license_expiry_date <= thirty_days_from_now

    @property
    def all_documents_verified(self):
        """Check if all driver documents are verified"""
        documents = self.documents.all()
        if not documents.exists():
            return False

        # Check if all documents are verified
        return all(doc.is_verified for doc in documents)

    @property
    def has_required_documents(self):
        """Check if driver has all required documents"""
        required_doc_types = ["license", "cpc"]
        existing_doc_types = list(
            self.documents.values_list("document_type", flat=True)
        )

        return all(doc_type in existing_doc_types for doc_type in required_doc_types)

    def update_verification_status(self):
        """Update verification status based on document verification"""
        from django.utils import timezone

        if not self.has_required_documents:
            self.verification_status = "unverified"
        elif self.all_documents_verified:
            self.verification_status = "verified"
            self.last_verified = timezone.now()
        else:
            self.verification_status = "pending"

        self.save(update_fields=["verification_status", "last_verified"])

    def verify_driver(self, notes=""):
        """Manually verify the driver"""
        from django.utils import timezone

        self.verification_status = "verified"
        self.last_verified = timezone.now()
        if notes:
            self.verification_notes = notes
        self.save(
            update_fields=["verification_status", "last_verified", "verification_notes"]
        )

    def reject_verification(self, notes=""):
        """Reject driver verification"""
        self.verification_status = "rejected"
        if notes:
            self.verification_notes = notes
        self.save(update_fields=["verification_status", "verification_notes"])


# Keeping original related models
class DriverLocation(Basemodel):
    driver = models.ForeignKey("Driver", on_delete=models.CASCADE)
    location = gis_models.PointField(geography=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Additional tracking metadata
    speed = models.FloatField(null=True)
    heading = models.FloatField(null=True)
    accuracy = models.FloatField(null=True)

    class Meta:
        db_table = "driver_location"
        managed = True
        get_latest_by = "timestamp"
        ordering = ["-timestamp"]


class DriverAvailability(Basemodel):
    """Detailed driver availability schedule"""

    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, related_name="availability_slots"
    )
    date = models.DateField()
    time_slots = models.JSONField()  # Available time slots
    service_areas = models.ManyToManyField("Provider.ServiceArea")
    max_jobs = models.IntegerField(default=1)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "driver_availability"
        managed = True
        verbose_name = _("Driver Availability")
        verbose_name_plural = _("Driver Availabilities")


# Add new models for Driver documentation and compliance
class DriverDocument(Basemodel):
    """Model for storing driver-related documents such as license, CPC, and training certificates"""

    objects: models.Manager = models.Manager()

    DOCUMENT_STATUS = [
        ("rejected", "Rejected"),
        ("verified", "Verified"),
        ("pending", "pending"),
    ]

    DOCUMENT_TYPES = [
        ("license", "Driving License"),
        ("cpc", "CPC Qualification Card"),
        ("tacho", "Tachograph Card"),
        ("adr", "ADR Certificate"),
        ("insurance", "Insurance Document"),
        ("training", "Training Certificate"),
        ("employment", "Employment Contract"),
        ("id", "ID Document"),
        ("medical", "Medical Certificate"),
        ("other", "Other Document"),
    ]

    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    has_two_sides = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True, null=True)
    verification_note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=DOCUMENT_STATUS, default="pending")

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.driver.name}"

    def get_upload_path(instance, filename):
        # Get the file extension
        ext = filename.split(".")[-1]
        # Create a shorter filename using timestamp
        from django.utils import timezone

        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        # Create new filename with timestamp and extension
        new_filename = f"{timestamp}.{ext}"
        return f"docs/drivers/{instance.driver.id}/{instance.id}/{new_filename}"

    document_front = models.FileField(
        upload_to=get_upload_path, blank=True, null=True, max_length=255
    )
    document_back = models.FileField(
        upload_to=get_upload_path, blank=True, null=True, max_length=255
    )

    class Meta:
        db_table = "driver_document"
        managed = True
        verbose_name = _("Driver Document")
        verbose_name_plural = _("Driver Documents")
        ordering = ["-issue_date"]

    def save(self, *args, **kwargs):
        """Override save to update driver verification status"""
        super().save(*args, **kwargs)
        # Update driver verification status when document is saved
        if hasattr(self, "driver"):
            self.driver.update_verification_status()


class DriverInfringement(Basemodel):
    """Model for tracking driver infringements and compliance issues"""

    INFRINGEMENT_TYPES = [
        ("drivers_hours", "Drivers Hours Violation"),
        ("speeding", "Speeding"),
        ("maintenance", "Vehicle Maintenance Negligence"),
        ("documentation", "Missing Documentation"),
        ("procedure", "Procedure Violation"),
        ("accident", "Accident"),
        ("other", "Other Infringement"),
    ]

    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, related_name="infringements"
    )
    infringement_type = models.CharField(max_length=20, choices=INFRINGEMENT_TYPES)
    infringement_date = models.DateField()
    description = models.TextField()
    penalty_points_added = models.PositiveIntegerField(default=0)
    fine_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    reported_by = models.CharField(max_length=100)

    # Resolution details
    is_resolved = models.BooleanField(default=False)
    resolution_date = models.DateField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        db_table = "driver_infringement"
        managed = True
        verbose_name = _("Driver Infringement")
        verbose_name_plural = _("Driver Infringements")
        ordering = ["-infringement_date"]

    def __str__(self):
        return f"{self.get_infringement_type_display()} - {self.driver.name} - {self.infringement_date}"
