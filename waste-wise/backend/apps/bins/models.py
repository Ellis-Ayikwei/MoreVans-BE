from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Zone(models.Model):
    """Geographic zones for organizing waste collection."""
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    boundary = models.PolygonField()
    description = models.TextField(blank=True)
    
    # Zone statistics
    population = models.IntegerField(default=0)
    area_sq_km = models.FloatField(default=0.0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'zones'
        verbose_name = _('Zone')
        verbose_name_plural = _('Zones')
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def bin_count(self):
        return self.bins.count()
    
    @property
    def active_bin_count(self):
        return self.bins.filter(is_active=True).count()


class WasteBin(models.Model):
    """Smart waste bin with IoT sensors."""
    
    class BinType(models.TextChoices):
        GENERAL = 'general', _('General Waste')
        RECYCLABLE = 'recyclable', _('Recyclable')
        ORGANIC = 'organic', _('Organic')
        HAZARDOUS = 'hazardous', _('Hazardous')
        
    class BinStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        MAINTENANCE = 'maintenance', _('Under Maintenance')
        DAMAGED = 'damaged', _('Damaged')
        INACTIVE = 'inactive', _('Inactive')
    
    # Unique identifier
    bin_id = models.CharField(
        max_length=20,
        unique=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Location
    location = models.PointField(srid=4326)
    address = models.CharField(max_length=255)
    zone = models.ForeignKey(
        Zone,
        on_delete=models.CASCADE,
        related_name='bins'
    )
    
    # Bin specifications
    bin_type = models.CharField(
        max_length=20,
        choices=BinType.choices,
        default=BinType.GENERAL
    )
    capacity = models.IntegerField(
        help_text=_('Capacity in liters'),
        validators=[MinValueValidator(50), MaxValueValidator(5000)]
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=BinStatus.choices,
        default=BinStatus.ACTIVE
    )
    is_active = models.BooleanField(default=True)
    
    # Current state
    current_fill_level = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Current fill level in percentage')
    )
    last_emptied = models.DateTimeField(null=True, blank=True)
    last_sensor_reading = models.DateTimeField(null=True, blank=True)
    
    # Hardware info
    sensor_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    firmware_version = models.CharField(max_length=20, blank=True)
    battery_level = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Installation details
    installation_date = models.DateField()
    installed_by = models.CharField(max_length=100, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    # Images
    image = models.ImageField(
        upload_to='bin_images/',
        blank=True,
        null=True
    )
    qr_code = models.ImageField(
        upload_to='bin_qrcodes/',
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'waste_bins'
        verbose_name = _('Waste Bin')
        verbose_name_plural = _('Waste Bins')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['zone', 'bin_type']),
            models.Index(fields=['current_fill_level']),
            models.Index(fields=['status']),
        ]
        
    def __str__(self):
        return f"Bin {self.bin_id} - {self.address}"
    
    @property
    def is_full(self):
        return self.current_fill_level >= 80
    
    @property
    def needs_emptying(self):
        return self.current_fill_level >= 70
    
    @property
    def coordinates(self):
        return {
            'lat': self.location.y,
            'lng': self.location.x
        }
    
    def get_fill_status(self):
        """Get human-readable fill status."""
        if self.current_fill_level >= 80:
            return 'Full'
        elif self.current_fill_level >= 60:
            return 'Nearly Full'
        elif self.current_fill_level >= 40:
            return 'Half Full'
        elif self.current_fill_level >= 20:
            return 'Partially Full'
        else:
            return 'Empty'
    
    def get_status_color(self):
        """Get color code for visualization."""
        if not self.is_active or self.status != self.BinStatus.ACTIVE:
            return '#808080'  # Gray for inactive
        elif self.current_fill_level >= 80:
            return '#FF0000'  # Red for full
        elif self.current_fill_level >= 60:
            return '#FFA500'  # Orange for nearly full
        elif self.current_fill_level >= 40:
            return '#FFFF00'  # Yellow for half full
        else:
            return '#00FF00'  # Green for empty


class BinMaintenance(models.Model):
    """Maintenance records for waste bins."""
    
    class MaintenanceType(models.TextChoices):
        ROUTINE = 'routine', _('Routine Check')
        REPAIR = 'repair', _('Repair')
        CLEANING = 'cleaning', _('Cleaning')
        SENSOR_REPLACEMENT = 'sensor', _('Sensor Replacement')
        OTHER = 'other', _('Other')
    
    bin = models.ForeignKey(
        WasteBin,
        on_delete=models.CASCADE,
        related_name='maintenance_records'
    )
    maintenance_type = models.CharField(
        max_length=20,
        choices=MaintenanceType.choices
    )
    description = models.TextField()
    performed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='maintenance_performed'
    )
    scheduled_date = models.DateTimeField()
    completed_date = models.DateTimeField(null=True, blank=True)
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bin_maintenance'
        verbose_name = _('Bin Maintenance')
        verbose_name_plural = _('Bin Maintenance Records')
        ordering = ['-scheduled_date']
        
    def __str__(self):
        return f"{self.bin.bin_id} - {self.maintenance_type} - {self.scheduled_date}"
    
    @property
    def is_completed(self):
        return self.completed_date is not None
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        return not self.is_completed and self.scheduled_date < timezone.now()