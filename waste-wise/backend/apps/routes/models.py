from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField


class Vehicle(models.Model):
    """Waste collection vehicles."""
    
    class VehicleType(models.TextChoices):
        TRUCK = 'truck', _('Truck')
        VAN = 'van', _('Van')
        COMPACTOR = 'compactor', _('Compactor')
        TRICYCLE = 'tricycle', _('Tricycle')
    
    class VehicleStatus(models.TextChoices):
        AVAILABLE = 'available', _('Available')
        ON_ROUTE = 'on_route', _('On Route')
        MAINTENANCE = 'maintenance', _('Under Maintenance')
        OUT_OF_SERVICE = 'out_of_service', _('Out of Service')
    
    registration_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(
        max_length=20,
        choices=VehicleType.choices
    )
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    
    # Capacity
    capacity_kg = models.IntegerField(
        help_text=_('Maximum capacity in kilograms')
    )
    capacity_liters = models.IntegerField(
        help_text=_('Maximum capacity in liters')
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=VehicleStatus.choices,
        default=VehicleStatus.AVAILABLE
    )
    current_location = models.PointField(null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    
    # Fuel and maintenance
    fuel_type = models.CharField(max_length=20, default='diesel')
    fuel_efficiency = models.FloatField(
        help_text=_('Kilometers per liter'),
        default=5.0
    )
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    
    # Assignment
    assigned_driver = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_vehicles'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehicles'
        verbose_name = _('Vehicle')
        verbose_name_plural = _('Vehicles')
        ordering = ['registration_number']
        
    def __str__(self):
        return f"{self.registration_number} - {self.get_vehicle_type_display()}"


class CollectionRoute(models.Model):
    """Optimized collection routes for waste collection."""
    
    class RouteStatus(models.TextChoices):
        PLANNED = 'planned', _('Planned')
        ACTIVE = 'active', _('Active')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    
    # Schedule
    scheduled_date = models.DateField()
    scheduled_start_time = models.TimeField()
    estimated_duration = models.DurationField()
    
    # Assignment
    assigned_vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name='routes'
    )
    assigned_driver = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='assigned_routes'
    )
    assigned_collectors = models.ManyToManyField(
        'users.User',
        related_name='collector_routes',
        blank=True
    )
    
    # Route details
    zone = models.ForeignKey(
        'bins.Zone',
        on_delete=models.CASCADE,
        related_name='routes'
    )
    total_distance = models.FloatField(
        help_text=_('Total distance in kilometers'),
        default=0.0
    )
    estimated_fuel_consumption = models.FloatField(
        help_text=_('Estimated fuel consumption in liters'),
        default=0.0
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=RouteStatus.choices,
        default=RouteStatus.PLANNED
    )
    
    # Execution details
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    actual_distance = models.FloatField(null=True, blank=True)
    actual_fuel_consumption = models.FloatField(null=True, blank=True)
    
    # Route optimization
    optimization_score = models.FloatField(
        default=0.0,
        help_text=_('Route optimization score (0-100)')
    )
    route_geometry = models.LineStringField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_routes'
    )
    
    class Meta:
        db_table = 'collection_routes'
        verbose_name = _('Collection Route')
        verbose_name_plural = _('Collection Routes')
        ordering = ['-scheduled_date', 'scheduled_start_time']
        indexes = [
            models.Index(fields=['scheduled_date', 'status']),
            models.Index(fields=['zone', 'status']),
        ]
        
    def __str__(self):
        return f"{self.code} - {self.name} - {self.scheduled_date}"
    
    @property
    def is_active(self):
        return self.status == self.RouteStatus.ACTIVE
    
    @property
    def is_completed(self):
        return self.status == self.RouteStatus.COMPLETED
    
    @property
    def bin_count(self):
        return self.stops.count()
    
    def calculate_efficiency(self):
        """Calculate route efficiency based on various factors."""
        if not self.actual_end_time or not self.actual_start_time:
            return 0.0
            
        planned_duration = self.estimated_duration.total_seconds() / 3600
        actual_duration = (self.actual_end_time - self.actual_start_time).total_seconds() / 3600
        
        time_efficiency = min(planned_duration / actual_duration, 1.0) * 100
        
        if self.actual_distance and self.total_distance:
            distance_efficiency = min(self.total_distance / self.actual_distance, 1.0) * 100
        else:
            distance_efficiency = 0.0
            
        return (time_efficiency + distance_efficiency) / 2


class RouteStop(models.Model):
    """Individual stops in a collection route."""
    
    route = models.ForeignKey(
        CollectionRoute,
        on_delete=models.CASCADE,
        related_name='stops'
    )
    bin = models.ForeignKey(
        'bins.WasteBin',
        on_delete=models.CASCADE,
        related_name='route_stops'
    )
    
    # Order in route
    stop_order = models.IntegerField()
    
    # Estimated timing
    estimated_arrival_time = models.DateTimeField()
    estimated_duration = models.DurationField(
        help_text=_('Estimated time to empty bin')
    )
    
    # Actual timing
    actual_arrival_time = models.DateTimeField(null=True, blank=True)
    actual_departure_time = models.DateTimeField(null=True, blank=True)
    
    # Collection details
    fill_level_before = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Fill level before collection')
    )
    fill_level_after = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Fill level after collection')
    )
    collected_weight = models.FloatField(
        null=True,
        blank=True,
        help_text=_('Weight collected in kg')
    )
    
    # Status
    is_completed = models.BooleanField(default=False)
    skipped = models.BooleanField(default=False)
    skip_reason = models.CharField(max_length=255, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'route_stops'
        verbose_name = _('Route Stop')
        verbose_name_plural = _('Route Stops')
        ordering = ['route', 'stop_order']
        unique_together = [['route', 'stop_order']]
        
    def __str__(self):
        return f"{self.route.code} - Stop {self.stop_order} - {self.bin.bin_id}"
    
    @property
    def collection_duration(self):
        if self.actual_arrival_time and self.actual_departure_time:
            return self.actual_departure_time - self.actual_arrival_time
        return None


class RouteOptimization(models.Model):
    """Route optimization history and parameters."""
    
    class OptimizationType(models.TextChoices):
        DISTANCE = 'distance', _('Minimize Distance')
        TIME = 'time', _('Minimize Time')
        FUEL = 'fuel', _('Minimize Fuel')
        BALANCED = 'balanced', _('Balanced Optimization')
    
    route = models.ForeignKey(
        CollectionRoute,
        on_delete=models.CASCADE,
        related_name='optimizations'
    )
    
    optimization_type = models.CharField(
        max_length=20,
        choices=OptimizationType.choices,
        default=OptimizationType.BALANCED
    )
    
    # Parameters
    parameters = models.JSONField(default=dict)
    
    # Results
    original_distance = models.FloatField()
    optimized_distance = models.FloatField()
    distance_saved = models.FloatField()
    
    original_duration = models.DurationField()
    optimized_duration = models.DurationField()
    time_saved = models.DurationField()
    
    fuel_saved = models.FloatField(
        help_text=_('Estimated fuel saved in liters')
    )
    
    # Metadata
    optimized_at = models.DateTimeField(auto_now_add=True)
    optimized_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        db_table = 'route_optimizations'
        verbose_name = _('Route Optimization')
        verbose_name_plural = _('Route Optimizations')
        ordering = ['-optimized_at']
        
    def __str__(self):
        return f"{self.route.code} - {self.optimization_type} - {self.optimized_at}"


class CollectionReport(models.Model):
    """Daily collection reports."""
    
    date = models.DateField()
    zone = models.ForeignKey(
        'bins.Zone',
        on_delete=models.CASCADE,
        related_name='collection_reports'
    )
    
    # Statistics
    total_routes = models.IntegerField(default=0)
    completed_routes = models.IntegerField(default=0)
    total_bins_scheduled = models.IntegerField(default=0)
    total_bins_collected = models.IntegerField(default=0)
    
    total_weight_collected = models.FloatField(
        default=0.0,
        help_text=_('Total weight collected in kg')
    )
    total_distance_covered = models.FloatField(
        default=0.0,
        help_text=_('Total distance covered in km')
    )
    total_fuel_consumed = models.FloatField(
        default=0.0,
        help_text=_('Total fuel consumed in liters')
    )
    
    # Efficiency metrics
    collection_efficiency = models.FloatField(
        default=0.0,
        help_text=_('Collection efficiency percentage')
    )
    route_efficiency = models.FloatField(
        default=0.0,
        help_text=_('Route efficiency percentage')
    )
    
    # Issues
    total_issues = models.IntegerField(default=0)
    issues_resolved = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'collection_reports'
        verbose_name = _('Collection Report')
        verbose_name_plural = _('Collection Reports')
        ordering = ['-date']
        unique_together = [['date', 'zone']]
        
    def __str__(self):
        return f"{self.zone.name} - {self.date}"