"""
Waste Bin Models for WasteWise Smart Waste Management System

These models define the physical waste bins, their locations, and status.
"""

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
import uuid


class Zone(models.Model):
    """Geographic zones for organizing waste collection areas"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    boundary = models.PolygonField(help_text="Geographic boundary of the zone")
    population = models.IntegerField(default=0, help_text="Estimated population in zone")
    area_sq_km = models.FloatField(help_text="Area in square kilometers")
    supervisor = models.ForeignKey(
        'users.WasteWiseUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='supervised_zones'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'zones'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def bin_count(self):
        return self.bins.filter(is_active=True).count()

    @property
    def average_fill_level(self):
        from apps.wastewise.sensors.models import SensorReading
        recent_readings = SensorReading.objects.filter(
            bin__zone=self,
            timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
        ).values_list('fill_level', flat=True)
        return sum(recent_readings) / len(recent_readings) if recent_readings else 0


class WasteBin(models.Model):
    """Physical waste bin with IoT sensors"""
    
    BIN_TYPES = [
        ('general', 'General Waste'),
        ('recyclable', 'Recyclable'),
        ('organic', 'Organic Waste'),
        ('hazardous', 'Hazardous Waste'),
        ('electronics', 'E-Waste'),
    ]
    
    BIN_SIZES = [
        ('small', 'Small (50L)'),
        ('medium', 'Medium (120L)'),
        ('large', 'Large (240L)'),
        ('industrial', 'Industrial (1000L+)'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('damaged', 'Damaged'),
        ('full', 'Full'),
        ('offline', 'Offline'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bin_id = models.CharField(max_length=20, unique=True, help_text="Unique identifier for the bin")
    location = models.PointField(help_text="GPS coordinates of the bin")
    address = models.CharField(max_length=255, help_text="Street address")
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='bins')
    
    # Bin specifications
    bin_type = models.CharField(max_length=20, choices=BIN_TYPES, default='general')
    bin_size = models.CharField(max_length=20, choices=BIN_SIZES, default='medium')
    capacity_liters = models.IntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(10000)],
        help_text="Total capacity in liters"
    )
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    installation_date = models.DateField()
    last_emptied = models.DateTimeField(null=True, blank=True)
    last_maintenance = models.DateTimeField(null=True, blank=True)
    
    # IoT sensor information
    sensor_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    is_smart_bin = models.BooleanField(default=True, help_text="Has IoT sensors")
    
    # Collection metadata
    collection_frequency_days = models.IntegerField(
        default=3, 
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="How often bin should be collected (in days)"
    )
    priority_level = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Collection priority (1=lowest, 5=highest)"
    )
    
    # Administrative fields
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'waste_bins'
        ordering = ['bin_id']
        indexes = [
            models.Index(fields=['zone', 'status']),
            models.Index(fields=['bin_type', 'is_active']),
            models.Index(fields=['last_emptied']),
        ]

    def __str__(self):
        return f"Bin {self.bin_id} - {self.get_bin_type_display()}"

    def get_absolute_url(self):
        return reverse('bins:detail', kwargs={'pk': self.pk})

    @property
    def current_fill_level(self):
        """Get the most recent fill level reading"""
        from apps.wastewise.sensors.models import SensorReading
        latest_reading = self.sensor_readings.first()
        return latest_reading.fill_level if latest_reading else 0

    @property
    def is_full(self):
        """Check if bin is considered full (>85% capacity)"""
        return self.current_fill_level >= 85

    @property
    def is_overflowing(self):
        """Check if bin is overflowing (>95% capacity)"""
        return self.current_fill_level >= 95

    @property
    def days_since_emptied(self):
        """Calculate days since last emptied"""
        if not self.last_emptied:
            return None
        return (timezone.now() - self.last_emptied).days

    @property
    def needs_collection(self):
        """Determine if bin needs immediate collection"""
        return (
            self.is_full or 
            (self.days_since_emptied and self.days_since_emptied >= self.collection_frequency_days)
        )

    @property
    def latitude(self):
        return self.location.y if self.location else None

    @property
    def longitude(self):
        return self.location.x if self.location else None

    def mark_as_emptied(self):
        """Mark bin as emptied and update timestamp"""
        self.last_emptied = timezone.now()
        self.save(update_fields=['last_emptied'])

    def mark_as_maintained(self):
        """Mark bin as maintained and update timestamp"""
        self.last_maintenance = timezone.now()
        self.status = 'active'
        self.save(update_fields=['last_maintenance', 'status'])


class BinMaintenanceLog(models.Model):
    """Log of maintenance activities for waste bins"""
    
    MAINTENANCE_TYPES = [
        ('cleaning', 'Cleaning'),
        ('repair', 'Repair'),
        ('sensor_replacement', 'Sensor Replacement'),
        ('battery_replacement', 'Battery Replacement'),
        ('general_inspection', 'General Inspection'),
        ('damage_assessment', 'Damage Assessment'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bin = models.ForeignKey(WasteBin, on_delete=models.CASCADE, related_name='maintenance_logs')
    maintenance_type = models.CharField(max_length=30, choices=MAINTENANCE_TYPES)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    technician = models.ForeignKey(
        'users.WasteWiseUser', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='maintenance_performed'
    )
    
    # Timing
    scheduled_date = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    is_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    photos = models.JSONField(default=list, blank=True)  # Store photo URLs
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bin_maintenance_logs'
        ordering = ['-scheduled_date']

    def __str__(self):
        return f"{self.bin.bin_id} - {self.get_maintenance_type_display()} ({self.scheduled_date.date()})"

    @property
    def duration_hours(self):
        """Calculate maintenance duration in hours"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() / 3600
        return None


class BinCollectionHistory(models.Model):
    """History of waste bin collections"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bin = models.ForeignKey(WasteBin, on_delete=models.CASCADE, related_name='collection_history')
    collected_at = models.DateTimeField()
    collected_by = models.ForeignKey(
        'users.WasteWiseUser', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='collections_performed'
    )
    vehicle = models.ForeignKey(
        'vehicles.CollectionVehicle', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    route = models.ForeignKey(
        'routes.CollectionRoute', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Collection details
    fill_level_before = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Fill level percentage before collection"
    )
    estimated_weight_kg = models.FloatField(null=True, blank=True)
    collection_duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Quality metrics
    bin_condition = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('damaged', 'Damaged'),
        ],
        default='good'
    )
    
    notes = models.TextField(blank=True)
    photos = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bin_collection_history'
        ordering = ['-collected_at']

    def __str__(self):
        return f"{self.bin.bin_id} collected on {self.collected_at.date()}"