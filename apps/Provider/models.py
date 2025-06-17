from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from apps.Basemodel.models import Basemodel
from apps.Services.models import ServiceCategory
from django.contrib.postgres.indexes import GistIndex
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from datetime import datetime
import uuid


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
    )
    business_description = models.TextField(max_length=2000, blank=True)
    website = models.URLField(max_length=200, blank=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    operating_areas = models.JSONField(default=list, blank=True)

    # --- Contact Information ---
    contact_person_name = models.CharField(max_length=100, blank=True)
    contact_person_position = models.CharField(max_length=100, blank=True)
    contact_person_email = models.EmailField(blank=True)
    contact_person_phone = models.CharField(max_length=20, blank=True)

    # --- Banking Information ---
    bank_account_holder = models.CharField(max_length=200, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_routing_number = models.CharField(max_length=50, blank=True)

    # --- Service Offerings ---
    service_categories = models.ManyToManyField(
        ServiceCategory, related_name="providers", verbose_name=_("Service Categories")
    )

    specializations = models.ManyToManyField(
        ServiceCategory,
        related_name="specializing_providers",
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
        related_name="service_providers",
    )

    # --- Financial Details ---
    payment_methods = models.ManyToManyField(
        "Payment.PaymentMethod",
        blank=True,
        related_name="providers",
    )

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
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    completed_bookings = models.PositiveIntegerField(default=0)
    vehicle_count = models.PositiveIntegerField(default=0)
    last_active = models.DateTimeField(null=True, blank=True)

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


class ServiceArea(Basemodel):
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
    objects: models.Manager = models.Manager()

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


class InsurancePolicy(Basemodel):
    """Insurance policy details"""

    POLICY_TYPES = [
        ("transit", _("Goods in Transit")),
        ("cmr", _("CMR Insurance")),
        ("liability", _("Public Liability")),
    ]

    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name="provider_insurance_policies",
    )
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES)
    coverage_amount = models.DecimalField(max_digits=10, decimal_places=2)
    policy_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    objects: models.Manager = models.Manager()

    class Meta:
        db_table = "insurance_policy"
        managed = True
        verbose_name = _("Insurance Policy")
        verbose_name_plural = _("Insurance Policies")


def get_upload_path(instance, filename):
    """
    Generate the upload path for provider documents.
    Format: provider_documents/{provider_id}/{document_type}/{timestamp}_{filename}
    """
    # Get file extension
    ext = filename.split(".")[-1]
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Create filename
    filename = f"{timestamp}_{instance.document_type}.{ext}"
    # Return full path
    return (
        f"provider_documents/{instance.provider.id}/{instance.document_type}/{filename}"
    )


class ProviderDocument(models.Model):
    """Provider verification documents"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    DOCUMENT_TYPES = [
        # Driver & Operator Documents
        ("driving_license", "Driving License"),
        ("cpc_card", "CPC Qualification Card"),
        ("tacho_card", "Tachograph Card"),
        ("adr_certificate", "ADR Certificate (Dangerous Goods)"),
        ("medical_certificate", "Medical Certificate"),
        ("dbs_check", "DBS Check Certificate"),
        ("driver_training", "Driver Training Certificate"),
        ("passport", "Passport/ID Document"),
        ("right_to_work", "Right to Work Documentation"),
        ("proof_of_address", "Proof of Address"),
        # Vehicle Documents
        ("vehicle_registration", "Vehicle Registration (V5C)"),
        ("mot_certificate", "MOT Certificate"),
        ("vehicle_insurance", "Vehicle Insurance Certificate"),
        ("operators_license", "Operator's License (O-License)"),
        ("plating_certificate", "Plating Certificate (HGV)"),
        ("vehicle_inspection", "Vehicle Inspection Certificate"),
        ("annual_test", "Annual Test Certificate"),
        # Business Insurance
        ("public_liability", "Public Liability Insurance"),
        ("employers_liability", "Employer's Liability Insurance"),
        ("goods_in_transit", "Goods in Transit Insurance"),
        ("professional_indemnity", "Professional Indemnity Insurance"),
        ("motor_trade_insurance", "Motor Trade Insurance"),
        # Business Registration & Licenses
        ("company_registration", "Company Registration Certificate"),
        ("vat_registration", "VAT Registration Certificate"),
        ("trading_license", "Trading License"),
        ("waste_carrier_license", "Waste Carrier License"),
        ("scrap_metal_license", "Scrap Metal Dealer License"),
        ("waste_management_license", "Waste Management License"),
        # Compliance & Safety
        ("health_safety_policy", "Health & Safety Policy"),
        ("risk_assessment", "Risk Assessment Document"),
        ("coshh_assessment", "COSHH Assessment"),
        ("environmental_policy", "Environmental Policy"),
        ("quality_management", "Quality Management Certificate"),
        ("gdpr_policy", "GDPR Privacy Policy"),
        # Financial Documents
        ("bank_statement", "Bank Statement"),
        ("financial_standing", "Financial Standing Evidence"),
        ("credit_reference", "Credit Reference"),
        # Employment & Contracts
        ("employment_contract", "Employment Contract"),
        ("contractor_agreement", "Contractor Agreement"),
        ("terms_conditions", "Terms & Conditions"),
        # Specialized Certifications
        ("iso_certificate", "ISO Certification"),
        ("bifa_membership", "BIFA Membership Certificate"),
        ("fta_membership", "FTA Membership Certificate"),
        ("trade_association", "Trade Association Membership"),
        # International & Customs
        ("aea_certificate", "AEA Certificate (Customs)"),
        ("eori_number", "EORI Number Certificate"),
        ("customs_registration", "Customs Registration"),
        # Other Documents
        ("other", "Other Document"),
    ]

    DOCUMENT_CATEGORIES = [
        ("driver", "Driver & Operator"),
        ("personal", "Personal"),
        ("vehicle", "Vehicle"),
        ("insurance", "Business Insurance"),
        ("business", "Business Registration"),
        ("compliance", "Compliance & Safety"),
        ("financial", "Financial"),
        ("employment", "Employment & Contracts"),
        ("certification", "Specialized Certifications"),
        ("international", "International & Customs"),
        ("other", "Other"),
    ]

    DOCUMENT_STATUS = [
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
    ]

    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_front = models.ImageField(upload_to=get_upload_path, null=True, blank=True)
    document_back = models.ImageField(upload_to=get_upload_path, null=True, blank=True)
    has_two_sides = models.BooleanField(default=False)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=DOCUMENT_STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.provider.get_full_name()} - {self.get_document_type_display()}"

    class Meta:
        verbose_name = _("Provider Document")
        verbose_name_plural = _("Provider Documents")
        ordering = ["-created_at"]
        db_table = "provider_document"
        managed = True
        indexes = [
            models.Index(fields=["document_type"]),
            models.Index(fields=["status"]),
        ]


class ProviderReview(Basemodel):
    """Customer reviews for providers"""

    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="reviews"
    )
    customer = models.ForeignKey(
        "User.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="provider_reviews",
    )
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    objects: models.Manager = models.Manager()

    class Meta:
        db_table = "provider_review"
        managed = True
        verbose_name = _("Provider Review")
        verbose_name_plural = _("Provider Reviews")


class ProviderPayment(Basemodel):
    """Payment history for providers"""

    PAYMENT_TYPES = [
        ("payout", _("Payout")),
        ("refund", _("Refund")),
        ("fee", _("Fee")),
    ]

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("completed", _("Completed")),
        ("failed", _("Failed")),
    ]

    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="payments"
    )
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    objects: models.Manager = models.Manager()

    class Meta:
        db_table = "provider_payment"
        managed = True
        verbose_name = _("Provider Payment")
        verbose_name_plural = _("Provider Payments")


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
