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
    VEHICLE_TYPES = [
        ('small_van', 'Small Van (up to 2.5t)'),
        ('medium_van', 'Medium Van (2.5-3.5t)'),
        ('large_van', 'Large Van (3.5t)'),
        ('luton', 'Luton Van'),
        ('7.5t', '7.5 Tonne Truck'),
        ('18t', '18 Tonne Truck'),
        ('refrigerated', 'Refrigerated Vehicle'),
        ('flatbed', 'Flatbed Truck'),
        ('tipper', 'Tipper Truck'),
        ('curtain_sider', 'Curtain Sider'),
        ('dropside', 'Dropside Truck'),
        ('tail_lift', 'Tail Lift Van'),
        ('pickup', 'Pickup Truck'),
        ('cargo_bike', 'Cargo Bike'),
        ('other', 'Other Specialized Vehicle'),
    ]
    
    FUEL_TYPES = [
        ('diesel', 'Diesel'),
        ('petrol', 'Petrol'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('plugin_hybrid', 'Plug-in Hybrid'),
        ('hydrogen', 'Hydrogen'),
        ('lpg', 'LPG'),
        ('cng', 'CNG'),
    ]
    
    TRANSMISSION_TYPES = [
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
    ]
    
    COMPLIANCE_STATUSES = [
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('exempt', 'Exempt'),
    ]
    
    # Core vehicle identity
    registration = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9 ]{1,10}$', 'Valid UK vehicle registration required')],
        help_text=_("UK Vehicle Registration Number (e.g., AB12 CDE)")
    )
    vin = models.CharField(
        max_length=17,
        unique=True,
        validators=[RegexValidator(r'^[A-HJ-NPR-Z0-9]{17}$', 'Valid VIN required')],
        verbose_name=_("VIN Number"),
        help_text=_("Vehicle Identification Number (17 characters)")
    )
    
    # Vehicle details
    make = models.CharField(max_length=50, help_text=_("Vehicle manufacturer"))
    model = models.CharField(max_length=100, help_text=_("Vehicle model"))
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1980), MaxValueValidator(2030)],
        help_text=_("Year of manufacture")
    )
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    fuel_type = models.CharField(max_length=15, choices=FUEL_TYPES)
    transmission = models.CharField(max_length=10, choices=TRANSMISSION_TYPES, default='manual')
    color = models.CharField(max_length=50, blank=True)
    
    # Capacity details
    payload_capacity_kg = models.PositiveIntegerField(help_text=_("Maximum payload in kg"))
    gross_vehicle_weight_kg = models.PositiveIntegerField(help_text=_("Gross vehicle weight in kg (GVW)"))
    load_length_mm = models.PositiveIntegerField(help_text=_("Load length in mm"))
    load_width_mm = models.PositiveIntegerField(help_text=_("Load width in mm"))
    load_height_mm = models.PositiveIntegerField(help_text=_("Load height in mm"))
    load_volume_m3 = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text=_("Load volume in cubic meters")
    )
    
    # UK regulatory compliance
    mot_expiry_date = models.DateField(help_text=_("MOT test certificate expiry date"))
    road_tax_expiry_date = models.DateField(help_text=_("Vehicle tax expiry date"))
    has_tachograph = models.BooleanField(default=False, help_text=_("Vehicle has a tachograph"))
    ulez_compliant = models.BooleanField(
        default=False,
        help_text=_("Compliant with Ultra Low Emission Zone standards")
    )
    clean_air_zone_status = models.CharField(
        max_length=15, 
        choices=COMPLIANCE_STATUSES, 
        default='non_compliant',
        help_text=_("Clean Air Zone compliance status")
    )
    
    # Insurance and fleet management
    insurance_policy_number = models.CharField(max_length=50, blank=True)
    insurance_expiry_date = models.DateField(null=True, blank=True)
    fleet_number = models.CharField(max_length=20, blank=True, help_text=_("Internal fleet ID"))
    
    # Maintenance tracking
    last_service_date = models.DateField(null=True, blank=True)
    next_service_date = models.DateField(null=True, blank=True)
    last_service_mileage = models.PositiveIntegerField(null=True, blank=True)
    current_mileage = models.PositiveIntegerField(default=0)
    service_interval_months = models.PositiveIntegerField(default=12)
    service_interval_miles = models.PositiveIntegerField(default=12000)
    
    # Equipment and features
    has_tail_lift = models.BooleanField(default=False)
    has_refrigeration = models.BooleanField(default=False)
    has_tracking_device = models.BooleanField(default=False)
    has_dash_cam = models.BooleanField(default=False)
    additional_features = models.JSONField(null=True, blank=True, help_text=_("Additional vehicle features"))
    
    # Ownership and assignment
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='provider_vehicles',
        help_text=_("Service provider that owns this vehicle")
    )
    primary_driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_vehicles',
        help_text=_("Driver primarily assigned to this vehicle")
    )
    is_active = models.BooleanField(default=True, help_text=_("Vehicle is currently active in the fleet"))
    
    # Tracking and utilization
    location = models.JSONField(null=True, blank=True, help_text=_("Last known location"))
    last_location_update = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True, help_text=_("Vehicle is available for jobs"))
    
    class Meta:
        db_table = 'vehicle'
        managed = True
        verbose_name = _("Vehicle")
        verbose_name_plural = _("Vehicles")
        ordering = ['provider', 'fleet_number', 'registration']
        indexes = [
            models.Index(fields=['registration']),
            models.Index(fields=['provider']),
            models.Index(fields=['vehicle_type']),
            models.Index(fields=['is_active', 'is_available']),
        ]
    
    def __str__(self):
        return f"{self.registration} - {self.make} {self.model} ({self.get_vehicle_type_display()})"
    
    @property
    def is_mot_valid(self):
        """Check if MOT is currently valid"""
        from django.utils import timezone
        return self.mot_expiry_date >= timezone.now().date()
    
    @property
    def is_road_tax_valid(self):
        """Check if road tax is currently valid"""
        from django.utils import timezone
        return self.road_tax_expiry_date >= timezone.now().date()
    
    @property
    def is_service_due(self):
        """Check if service is due based on date or mileage"""
        from django.utils import timezone
        if not self.next_service_date:
            return False
        
        is_date_due = self.next_service_date <= timezone.now().date()
        is_mileage_due = False
        
        if self.last_service_mileage and self.service_interval_miles:
            is_mileage_due = (self.current_mileage - self.last_service_mileage) >= self.service_interval_miles
            
        return is_date_due or is_mileage_due
    
    @property
    def load_dimensions(self):
        """Return formatted load dimensions"""
        return f"{self.load_length_mm/1000:.2f}m × {self.load_width_mm/1000:.2f}m × {self.load_height_mm/1000:.2f}m"


class VehicleDocument(Basemodel):
    """
    Model for storing vehicle-related documents such as MOT certificates, 
    insurance documents, and maintenance records.
    """
    DOCUMENT_TYPES = [
        ('mot', 'MOT Certificate'),
        ('insurance', 'Insurance Certificate'),
        ('v5c', 'V5C Registration Document'),
        ('service', 'Service Record'),
        ('repair', 'Repair Invoice'),
        ('inspection', 'Vehicle Inspection Report'),
        ('other', 'Other Document'),
    ]
    
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='vehicle_documents/%Y/%m/')
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'vehicle_document'
        managed = True
        verbose_name = _("Vehicle Document")
        verbose_name_plural = _("Vehicle Documents")
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.vehicle.registration}"


class VehicleInspection(Basemodel):
    """
    Model for tracking regular vehicle inspections and condition reports.
    """
    INSPECTION_TYPES = [
        ('daily', 'Daily Check'),
        ('weekly', 'Weekly Check'),
        ('periodic', 'Periodic Safety Inspection'),
        ('pre_mot', 'Pre-MOT Inspection'),
        ('accident', 'Post-Accident Inspection'),
    ]
    
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('unroadworthy', 'Unroadworthy'),
    ]
    
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.CASCADE,
        related_name='inspections'
    )
    inspection_type = models.CharField(max_length=20, choices=INSPECTION_TYPES)
    inspection_date = models.DateField()
    inspector_name = models.CharField(max_length=100)
    mileage_at_inspection = models.PositiveIntegerField()
    overall_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    
    # Detailed inspection points
    inspection_items = models.JSONField(help_text=_("Detailed inspection checklist items"))
    defects_found = models.TextField(blank=True, help_text=_("Description of any defects found"))
    actions_required = models.TextField(blank=True, help_text=_("Actions required to fix defects"))
    
    is_roadworthy = models.BooleanField(default=True, help_text=_("Vehicle is considered roadworthy"))
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'vehicle_inspection'
        managed = True
        verbose_name = _("Vehicle Inspection")
        verbose_name_plural = _("Vehicle Inspections")
        ordering = ['-inspection_date']
    
    def __str__(self):
        return f"{self.get_inspection_type_display()} - {self.vehicle.registration} - {self.inspection_date}"


class MaintenanceRecord(Basemodel):
    """
    Model for tracking vehicle maintenance history.
    """
    MAINTENANCE_TYPES = [
        ('regular_service', 'Regular Service'),
        ('interim_service', 'Interim Service'),
        ('major_service', 'Major Service'),
        ('repair', 'Repair Work'),
        ('breakdown', 'Breakdown Repair'),
        ('recall', 'Manufacturer Recall'),
        ('tire_change', 'Tire Change'),
        ('battery', 'Battery Replacement'),
        ('other', 'Other Maintenance'),
    ]
    
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.CASCADE,
        related_name='maintenance_records'
    )
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    maintenance_date = models.DateField()
    mileage = models.PositiveIntegerField(help_text=_("Vehicle mileage at time of maintenance"))
    work_performed = models.TextField(help_text=_("Description of work performed"))
    parts_replaced = models.TextField(blank=True, help_text=_("Parts that were replaced"))
    
    performed_by = models.CharField(max_length=100, help_text=_("Person or garage that performed the work"))
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    invoice_reference = models.CharField(max_length=100, blank=True)
    
    next_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_mileage = models.PositiveIntegerField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'maintenance_record'
        managed = True
        verbose_name = _("Maintenance Record")
        verbose_name_plural = _("Maintenance Records")
        ordering = ['-maintenance_date']
    
    def __str__(self):
        return f"{self.get_maintenance_type_display()} - {self.vehicle.registration} - {self.maintenance_date}"