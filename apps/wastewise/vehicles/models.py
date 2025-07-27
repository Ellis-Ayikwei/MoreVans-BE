"""
Vehicle Models for WasteWise Smart Waste Management System

These models manage the collection vehicle fleet and tracking.
"""

from django.contrib.gis.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class CollectionVehicle(models.Model):
    """Collection vehicles in the fleet"""
    
    VEHICLE_TYPES = [
        ('compact', 'Compact Truck'),
        ('medium', 'Medium Truck'),
        ('large', 'Large Truck'),
        ('specialized', 'Specialized Vehicle'),
    ]
    
    FUEL_TYPES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('cng', 'CNG'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('out_of_service', 'Out of Service'),
        ('retired', 'Retired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle_id = models.CharField(max_length=50, unique=True)
    license_plate = models.CharField(max_length=20, unique=True)
    
    # Vehicle specifications
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    
    # Capacity and specifications
    capacity_liters = models.IntegerField(
        validators=[MinValueValidator(100), MaxValueValidator(50000)]
    )
    max_weight_kg = models.IntegerField()
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES)
    fuel_capacity_liters = models.FloatField()
    
    # GPS and tracking
    gps_device_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    current_location = models.PointField(null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    
    # Status and maintenance
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    odometer_km = models.IntegerField(default=0)
    last_service_date = models.DateField(null=True, blank=True)
    next_service_due_km = models.IntegerField(null=True, blank=True)
    
    # Insurance and registration
    insurance_expiry = models.DateField()
    registration_expiry = models.DateField()
    inspection_expiry = models.DateField(null=True, blank=True)
    
    # Performance metrics
    average_fuel_consumption = models.FloatField(null=True, blank=True)  # L/100km
    total_collections = models.IntegerField(default=0)
    total_distance_km = models.FloatField(default=0)
    
    # Administrative
    purchase_date = models.DateField()
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'collection_vehicles'
        ordering = ['vehicle_id']

    def __str__(self):
        return f"{self.vehicle_id} - {self.make} {self.model}"

    @property
    def is_available(self):
        """Check if vehicle is available for assignment"""
        return self.status == 'active'

    @property
    def needs_service(self):
        """Check if vehicle needs service based on odometer"""
        if self.next_service_due_km:
            return self.odometer_km >= self.next_service_due_km
        return False

    def update_location(self, latitude, longitude):
        """Update vehicle's current location"""
        from django.contrib.gis.geos import Point
        self.current_location = Point(longitude, latitude)
        self.last_location_update = timezone.now()
        self.save(update_fields=['current_location', 'last_location_update'])


class VehicleMaintenanceLog(models.Model):
    """Maintenance records for vehicles"""
    
    MAINTENANCE_TYPES = [
        ('routine', 'Routine Maintenance'),
        ('repair', 'Repair'),
        ('inspection', 'Inspection'),
        ('tire_change', 'Tire Change'),
        ('oil_change', 'Oil Change'),
        ('brake_service', 'Brake Service'),
        ('engine_repair', 'Engine Repair'),
        ('body_repair', 'Body Repair'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(CollectionVehicle, on_delete=models.CASCADE, related_name='maintenance_logs')
    
    # Maintenance details
    maintenance_type = models.CharField(max_length=30, choices=MAINTENANCE_TYPES)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Service provider
    service_provider = models.CharField(max_length=200)
    technician = models.CharField(max_length=100, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    
    # Timing
    scheduled_date = models.DateField()
    actual_date = models.DateField()
    started_at = models.TimeField(null=True, blank=True)
    completed_at = models.TimeField(null=True, blank=True)
    
    # Vehicle condition
    odometer_reading = models.IntegerField()
    parts_replaced = models.JSONField(default=list, blank=True)
    
    # Quality and follow-up
    quality_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    warranty_period_days = models.IntegerField(null=True, blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vehicle_maintenance_logs'
        ordering = ['-actual_date']

    def __str__(self):
        return f"{self.vehicle.vehicle_id} - {self.get_maintenance_type_display()} ({self.actual_date})"


class VehicleTracking(models.Model):
    """Real-time vehicle location tracking"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(CollectionVehicle, on_delete=models.CASCADE, related_name='tracking_history')
    
    # Location data
    location = models.PointField()
    accuracy_meters = models.FloatField(null=True, blank=True)
    altitude_meters = models.FloatField(null=True, blank=True)
    heading_degrees = models.FloatField(null=True, blank=True)
    speed_kmh = models.FloatField(null=True, blank=True)
    
    # Context
    route = models.ForeignKey(
        'routes.CollectionRoute',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicle_tracking'
    )
    driver = models.ForeignKey(
        'users.WasteWiseUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Vehicle status
    engine_on = models.BooleanField(default=True)
    fuel_level_percentage = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    odometer_reading = models.IntegerField(null=True, blank=True)
    
    # Additional data
    temperature = models.FloatField(null=True, blank=True)
    battery_voltage = models.FloatField(null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vehicle_tracking'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['vehicle', '-timestamp']),
            models.Index(fields=['route', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.vehicle.vehicle_id} at {self.timestamp}"


class FuelLog(models.Model):
    """Fuel consumption tracking for vehicles"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(CollectionVehicle, on_delete=models.CASCADE, related_name='fuel_logs')
    
    # Fuel data
    fuel_amount_liters = models.FloatField()
    cost_per_liter = models.DecimalField(max_digits=8, decimal_places=3)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Context
    odometer_reading = models.IntegerField()
    fuel_station = models.CharField(max_length=200)
    driver = models.ForeignKey(
        'users.WasteWiseUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Receipt and verification
    receipt_number = models.CharField(max_length=100, blank=True)
    receipt_photo = models.ImageField(upload_to='fuel_receipts/', null=True, blank=True)
    
    # Calculated metrics
    distance_since_last_fuel = models.FloatField(null=True, blank=True)
    consumption_per_100km = models.FloatField(null=True, blank=True)
    
    fueled_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fuel_logs'
        ordering = ['-fueled_at']

    def __str__(self):
        return f"{self.vehicle.vehicle_id} - {self.fuel_amount_liters}L on {self.fueled_at.date()}"

    def save(self, *args, **kwargs):
        # Calculate total cost
        self.total_cost = self.fuel_amount_liters * self.cost_per_liter
        
        # Calculate consumption metrics
        last_fuel = FuelLog.objects.filter(
            vehicle=self.vehicle,
            fueled_at__lt=self.fueled_at
        ).first()
        
        if last_fuel:
            self.distance_since_last_fuel = self.odometer_reading - last_fuel.odometer_reading
            if self.distance_since_last_fuel > 0:
                self.consumption_per_100km = (self.fuel_amount_liters / self.distance_since_last_fuel) * 100
        
        super().save(*args, **kwargs)