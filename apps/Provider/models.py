from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from apps.Basemodel.models import Basemodel
from apps.Services.models import ServiceCategory
from django.contrib.postgres.indexes import GistIndex
from django.contrib.gis.db import models as gis_models
from django.utils import timezone


class ServiceProvider(Basemodel):
    # --- Core Identity ---
    user = models.OneToOneField(
        "User.User",
        on_delete=models.CASCADE,
        related_name="service_provider_profile",
        limit_choices_to={"user_type": "provider"},
    )

    # --- Business Details ---
    BUSINESS_TYPES = [
        ("limited", _("Limited Company")),
        ("sole_trader", _("Sole Trader")),
        ("partnership", _("Partnership")),
    ]

    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPES)
    company_name = models.CharField(max_length=200)
    company_reg_number = models.CharField(
        max_length=50,
        blank=True,
        validators=[RegexValidator(r"^[A-Z0-9]+$", "Alphanumeric characters only")],
    )
    vat_registered = models.BooleanField(default=False)
    vat_number = models.CharField(
        max_length=20,
        blank=True,
        # validators=[VATNumberValidator()]
    )
    business_description = models.TextField(max_length=2000, blank=True)

    # --- Service Offerings ---
    service_categories = models.ManyToManyField(
        ServiceCategory, related_name="providers", verbose_name=_("Service Categories")
    )

    specializations = models.ManyToManyField(
        ServiceCategory,
        related_name="specializing_providers",
        limit_choices_to={"is_specialization": True},
        blank=True,
        verbose_name=_("Specializations"),
    )

    service_image = models.ImageField(
        upload_to="service_providers/services/%Y/%m/", null=True, blank=True
    )
    base_location = gis_models.PointField(
        srid=4326,
        help_text=_("Primary service location coordinates"),
        null=True,
        blank=True,
    )
    hourly_rate = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    accepts_instant_bookings = models.BooleanField(default=True)

    # --- Geographic Coverage ---
    service_radius_km = models.PositiveIntegerField(
        default=50, help_text=_("Maximum service radius from base location (km)")
    )

    # --- Insurance & Certifications ---
    insurance_policies = models.ManyToManyField(
        "InsurancePolicy",
        blank=True,
        related_name="service_providers",  # Changed related_name to avoid clash
    )

    # --- Financial Details ---
    payment_methods = models.ManyToManyField(
        "Payment.PaymentMethod",  # Corrected the reference to the PaymentMethod model
        blank=True,
        related_name="providers",
    )
    # stripe_connect_id = EncryptedCharField(max_length=100, blank=True)
    # tax_identification_number = EncryptedCharField(max_length=50, blank=True)

    # --- Operational Preferences ---
    minimum_job_value = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )

    # --- Verification & Compliance ---
    VERIFICATION_STATUSES = [
        ("unverified", _("Unverified")),
        ("pending", _("Pending Review")),
        ("verified", _("Verified")),
        ("premium", _("Premium Verified")),
    ]

    verification_status = models.CharField(
        max_length=20, choices=VERIFICATION_STATUSES, default="unverified"
    )
    last_verified = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "service_provider"
        managed = True
        verbose_name = _("Service Provider")
        verbose_name_plural = _("Service Providers")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["verification_status"]),
            GistIndex(fields=["base_location"]),
        ]

    def __str__(self):
        return f"{self.company_name} - {self.get_verification_status_display()}"

    @property
    def service_coverage(self):
        """Returns combined coverage area"""
        if self.service_areas.exists():
            return self.service_areas.aggregate(models.Union("area"))["area__union"]
        if self.base_location:
            return self.base_location.buffer(self.service_radius_km * 1000)
        return None

    def clean(self):
        if not self.base_location and not self.service_areas.exists():
            raise ValidationError("Must have either base location or service areas")


class ServiceArea(models.Model):
    """Geographic service coverage areas"""

    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name="service_areas",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    area = gis_models.MultiPolygonField(srid=4326, null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)

    class Meta:
        db_table = "service_area"
        managed = True
        verbose_name = _("Service Area")
        verbose_name_plural = _("Service Areas")
        indexes = [
            GistIndex(fields=["area"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.provider.company_name})"


class InsurancePolicy(models.Model):
    """Insurance policy details"""

    POLICY_TYPES = [
        ("transit", _("Goods in Transit")),
        ("cmr", _("CMR Insurance")),
        ("liability", _("Public Liability")),
    ]

    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name="provider_insurance_policies",  # Changed related_name to avoid clash
    )
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES)
    coverage_amount = models.DecimalField(max_digits=10, decimal_places=2)
    policy_number = models.CharField(max_length=100)
    expiry_date = models.DateField()

    class Meta:
        db_table = "insurance_policy"
        managed = True
        verbose_name = _("Insurance Policy")
        verbose_name_plural = _("Insurance Policies")


class SavedJob(Basemodel):
    """Jobs saved by providers for later reference"""

    provider = models.ForeignKey(
        "User.User", on_delete=models.CASCADE, related_name="saved_jobs"
    )
    job = models.ForeignKey(
        "Job.Job", on_delete=models.CASCADE, related_name="saved_by"
    )
    saved_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "provider_saved_job"
        managed = True
        unique_together = ["job", "provider"]
        verbose_name = "Saved Job"
        verbose_name_plural = "Saved Jobs"

    def __str__(self):
        return f"{self.provider} saved job #{self.job.id}"


class WatchedJob(Basemodel):
    """Jobs being watched by providers for updates"""

    provider = models.ForeignKey(
        "User.User", on_delete=models.CASCADE, related_name="watched_jobs"
    )
    job = models.ForeignKey(
        "Job.Job", on_delete=models.CASCADE, related_name="watched_by"
    )
    started_watching = models.DateTimeField(default=timezone.now)
    notify = models.BooleanField(default=True)
    notification_preferences = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "provider_watched_job"
        managed = True
        unique_together = ["job", "provider"]
        verbose_name = "Watched Job"
        verbose_name_plural = "Watched Jobs"

    def __str__(self):
        return f"{self.provider} watching job #{self.job.id}"


# def VATNumberValidator(value):
#     if not value:
#         return
#     try:
#         VATNumber(value)
#     except InvalidVATNumber:
#         raise ValidationError("Invalid VAT Number")
