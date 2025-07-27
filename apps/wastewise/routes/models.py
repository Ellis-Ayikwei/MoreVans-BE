"""
Route Models for WasteWise Smart Waste Management System

These models handle collection route planning, optimization, and tracking.
"""

from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString, Point
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
import json


class CollectionRoute(models.Model):
    """Collection routes for waste pickup"""
    
    ROUTE_STATUS = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    ROUTE_TYPES = [
        ('scheduled', 'Scheduled Route'),
        ('emergency', 'Emergency Route'),
        ('optimization', 'Optimized Route'),
        ('manual', 'Manual Route'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    route_code = models.CharField(max_length=50, unique=True)
    
    # Route classification
    route_type = models.CharField(max_length=20, choices=ROUTE_TYPES, default='scheduled')
    status = models.CharField(max_length=20, choices=ROUTE_STATUS, default='planned')
    priority = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Route priority (1=lowest, 5=highest)"
    )
    
    # Geographic data
    zones = models.ManyToManyField('bins.Zone', related_name='routes')
    route_path = models.LineStringField(null=True, blank=True, help_text="Optimized route path")
    total_distance_km = models.FloatField(null=True, blank=True)
    
    # Scheduling
    scheduled_date = models.DateField()
    scheduled_start_time = models.TimeField()
    estimated_duration_hours = models.FloatField(
        validators=[MinValueValidator(0.5), MaxValueValidator(24)]
    )
    
    # Assignment
    assigned_vehicle = models.ForeignKey(
        'vehicles.CollectionVehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_routes'
    )
    assigned_driver = models.ForeignKey(
        'users.WasteWiseUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_routes',
        limit_choices_to={'role__in': ['operator', 'driver']}
    )
    assigned_team = models.ManyToManyField(
        'users.WasteWiseUser',
        related_name='team_routes',
        blank=True
    )
    
    # Execution tracking
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    actual_duration_hours = models.FloatField(null=True, blank=True)
    actual_distance_km = models.FloatField(null=True, blank=True)
    
    # Performance metrics
    bins_collected = models.IntegerField(default=0)
    total_bins_planned = models.IntegerField(default=0)
    completion_percentage = models.FloatField(default=0.0)
    fuel_consumed_liters = models.FloatField(null=True, blank=True)
    
    # Weather and conditions
    weather_conditions = models.JSONField(default=dict, blank=True)
    road_conditions = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('blocked', 'Blocked'),
        ],
        default='good'
    )
    
    # Optimization data
    optimization_algorithm = models.CharField(max_length=50, blank=True)
    optimization_parameters = models.JSONField(default=dict, blank=True)
    optimization_score = models.FloatField(null=True, blank=True)
    
    # Administrative
    created_by = models.ForeignKey(
        'users.WasteWiseUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_routes'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'collection_routes'
        ordering = ['-scheduled_date', '-scheduled_start_time']
        indexes = [
            models.Index(fields=['status', 'scheduled_date']),
            models.Index(fields=['assigned_vehicle', 'status']),
            models.Index(fields=['assigned_driver', 'scheduled_date']),
        ]

    def __str__(self):
        return f"{self.name} - {self.scheduled_date}"

    @property
    def is_active(self):
        """Check if route is currently active"""
        return self.status == 'active'

    @property
    def is_completed(self):
        """Check if route is completed"""
        return self.status == 'completed'

    @property
    def efficiency_score(self):
        """Calculate route efficiency based on time and distance"""
        if not self.actual_duration_hours or not self.estimated_duration_hours:
            return None
        
        time_efficiency = min(self.estimated_duration_hours / self.actual_duration_hours, 1.0)
        completion_efficiency = self.completion_percentage / 100.0
        
        return (time_efficiency + completion_efficiency) / 2 * 100

    def start_route(self):
        """Start the collection route"""
        self.status = 'active'
        self.actual_start_time = timezone.now()
        self.save(update_fields=['status', 'actual_start_time'])

    def complete_route(self):
        """Complete the collection route"""
        self.status = 'completed'
        self.actual_end_time = timezone.now()
        if self.actual_start_time:
            duration = self.actual_end_time - self.actual_start_time
            self.actual_duration_hours = duration.total_seconds() / 3600
        self.save(update_fields=['status', 'actual_end_time', 'actual_duration_hours'])

    def calculate_completion_percentage(self):
        """Calculate and update completion percentage"""
        total_stops = self.route_stops.count()
        completed_stops = self.route_stops.filter(status='completed').count()
        
        if total_stops > 0:
            self.completion_percentage = (completed_stops / total_stops) * 100
            self.bins_collected = completed_stops
            self.total_bins_planned = total_stops
            self.save(update_fields=['completion_percentage', 'bins_collected', 'total_bins_planned'])


class RouteStop(models.Model):
    """Individual stops along a collection route"""
    
    STOP_STATUS = [
        ('pending', 'Pending'),
        ('skipped', 'Skipped'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(CollectionRoute, on_delete=models.CASCADE, related_name='route_stops')
    bin = models.ForeignKey('bins.WasteBin', on_delete=models.CASCADE, related_name='route_stops')
    
    # Stop details
    stop_order = models.PositiveIntegerField(help_text="Order of this stop in the route")
    estimated_arrival_time = models.TimeField()
    estimated_collection_duration_minutes = models.IntegerField(default=5)
    
    # Execution data
    actual_arrival_time = models.DateTimeField(null=True, blank=True)
    actual_departure_time = models.DateTimeField(null=True, blank=True)
    actual_duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Collection data
    status = models.CharField(max_length=20, choices=STOP_STATUS, default='pending')
    fill_level_before = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    estimated_weight_kg = models.FloatField(null=True, blank=True)
    
    # Issues and notes
    issues_encountered = models.JSONField(default=list, blank=True)
    skip_reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    photos = models.JSONField(default=list, blank=True)
    
    # Location verification
    gps_coordinates = models.PointField(null=True, blank=True)
    location_accuracy = models.FloatField(null=True, blank=True, help_text="GPS accuracy in meters")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'route_stops'
        ordering = ['route', 'stop_order']
        unique_together = ['route', 'stop_order']
        indexes = [
            models.Index(fields=['route', 'stop_order']),
            models.Index(fields=['bin', 'status']),
            models.Index(fields=['status', 'actual_arrival_time']),
        ]

    def __str__(self):
        return f"Stop {self.stop_order}: {self.bin.bin_id} on {self.route.name}"

    def mark_as_arrived(self, gps_location=None):
        """Mark stop as arrived"""
        self.actual_arrival_time = timezone.now()
        if gps_location:
            self.gps_coordinates = gps_location
        self.save(update_fields=['actual_arrival_time', 'gps_coordinates'])

    def mark_as_completed(self, fill_level=None, weight=None):
        """Mark stop as completed"""
        self.status = 'completed'
        self.actual_departure_time = timezone.now()
        
        if self.actual_arrival_time:
            duration = self.actual_departure_time - self.actual_arrival_time
            self.actual_duration_minutes = int(duration.total_seconds() / 60)
        
        if fill_level is not None:
            self.fill_level_before = fill_level
        if weight is not None:
            self.estimated_weight_kg = weight
            
        self.save(update_fields=[
            'status', 'actual_departure_time', 'actual_duration_minutes',
            'fill_level_before', 'estimated_weight_kg'
        ])
        
        # Update bin status
        self.bin.mark_as_emptied()
        
        # Update route completion percentage
        self.route.calculate_completion_percentage()

    def skip_stop(self, reason):
        """Skip this stop with reason"""
        self.status = 'skipped'
        self.skip_reason = reason
        self.save(update_fields=['status', 'skip_reason'])
        
        # Update route completion percentage
        self.route.calculate_completion_percentage()


class RouteOptimization(models.Model):
    """Route optimization sessions and results"""
    
    OPTIMIZATION_STATUS = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    ALGORITHMS = [
        ('nearest_neighbor', 'Nearest Neighbor'),
        ('genetic_algorithm', 'Genetic Algorithm'),
        ('simulated_annealing', 'Simulated Annealing'),
        ('ant_colony', 'Ant Colony Optimization'),
        ('tsp_solver', 'TSP Solver'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Input parameters
    zones = models.ManyToManyField('bins.Zone', related_name='optimizations')
    target_date = models.DateField()
    algorithm = models.CharField(max_length=30, choices=ALGORITHMS, default='genetic_algorithm')
    
    # Optimization constraints
    max_route_duration_hours = models.FloatField(default=8.0)
    max_vehicle_capacity_liters = models.IntegerField(default=5000)
    start_location = models.PointField(help_text="Depot or starting location")
    end_location = models.PointField(null=True, blank=True, help_text="End location (if different from start)")
    
    # Parameters
    optimization_parameters = models.JSONField(default=dict, blank=True)
    bin_priorities = models.JSONField(default=dict, blank=True)
    
    # Execution
    status = models.CharField(max_length=20, choices=OPTIMIZATION_STATUS, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time_seconds = models.FloatField(null=True, blank=True)
    
    # Results
    optimized_route = models.ForeignKey(
        CollectionRoute,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='optimization_results'
    )
    total_distance_km = models.FloatField(null=True, blank=True)
    estimated_duration_hours = models.FloatField(null=True, blank=True)
    number_of_stops = models.IntegerField(null=True, blank=True)
    
    # Quality metrics
    optimization_score = models.FloatField(null=True, blank=True)
    improvement_percentage = models.FloatField(null=True, blank=True)
    
    # Administrative
    requested_by = models.ForeignKey(
        'users.WasteWiseUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_optimizations'
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'route_optimizations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Optimization for {self.target_date} using {self.get_algorithm_display()}"

    def start_optimization(self):
        """Start the optimization process"""
        self.status = 'running'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])

    def complete_optimization(self, route=None, metrics=None):
        """Complete the optimization process"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.processing_time_seconds = duration.total_seconds()
        
        if route:
            self.optimized_route = route
            
        if metrics:
            self.total_distance_km = metrics.get('distance_km')
            self.estimated_duration_hours = metrics.get('duration_hours')
            self.number_of_stops = metrics.get('stops')
            self.optimization_score = metrics.get('score')
            self.improvement_percentage = metrics.get('improvement')
        
        self.save()

    def fail_optimization(self, error_message):
        """Mark optimization as failed"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message'])


class RouteTemplate(models.Model):
    """Reusable route templates for common collection patterns"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Template configuration
    zones = models.ManyToManyField('bins.Zone', related_name='route_templates')
    template_path = models.LineStringField(null=True, blank=True)
    frequency_days = models.IntegerField(
        default=7,
        help_text="How often this route should be executed (in days)"
    )
    
    # Default settings
    default_start_time = models.TimeField()
    estimated_duration_hours = models.FloatField()
    vehicle_type_required = models.CharField(
        max_length=50,
        choices=[
            ('small', 'Small Vehicle'),
            ('medium', 'Medium Vehicle'),
            ('large', 'Large Vehicle'),
            ('specialized', 'Specialized Vehicle'),
        ],
        default='medium'
    )
    
    # Performance history
    times_used = models.IntegerField(default=0)
    average_completion_time_hours = models.FloatField(null=True, blank=True)
    average_efficiency_score = models.FloatField(null=True, blank=True)
    
    # Administrative
    created_by = models.ForeignKey(
        'users.WasteWiseUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'route_templates'
        ordering = ['name']

    def __str__(self):
        return f"Template: {self.name}"

    def create_route_from_template(self, scheduled_date, assigned_vehicle=None, assigned_driver=None):
        """Create a new route based on this template"""
        route = CollectionRoute.objects.create(
            name=f"{self.name} - {scheduled_date}",
            route_code=f"TMPL_{self.id.hex[:8]}_{scheduled_date.strftime('%Y%m%d')}",
            route_type='scheduled',
            scheduled_date=scheduled_date,
            scheduled_start_time=self.default_start_time,
            estimated_duration_hours=self.estimated_duration_hours,
            assigned_vehicle=assigned_vehicle,
            assigned_driver=assigned_driver,
            route_path=self.template_path,
        )
        
        # Add zones
        route.zones.set(self.zones.all())
        
        # Increment usage counter
        self.times_used += 1
        self.save(update_fields=['times_used'])
        
        return route


class RoutePerformanceMetrics(models.Model):
    """Aggregate performance metrics for routes"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.OneToOneField(CollectionRoute, on_delete=models.CASCADE, related_name='performance_metrics')
    
    # Efficiency metrics
    time_efficiency = models.FloatField(null=True, blank=True, help_text="Actual vs planned time")
    distance_efficiency = models.FloatField(null=True, blank=True, help_text="Actual vs planned distance")
    fuel_efficiency = models.FloatField(null=True, blank=True, help_text="Fuel consumption per km")
    
    # Collection metrics
    collection_rate = models.FloatField(null=True, blank=True, help_text="Percentage of bins collected")
    average_fill_level = models.FloatField(null=True, blank=True, help_text="Average fill level of collected bins")
    total_waste_collected_kg = models.FloatField(null=True, blank=True)
    
    # Quality metrics
    route_adherence = models.FloatField(null=True, blank=True, help_text="How closely route was followed")
    customer_satisfaction = models.FloatField(null=True, blank=True, help_text="Citizen feedback score")
    
    # Environmental impact
    co2_emissions_kg = models.FloatField(null=True, blank=True)
    noise_level_average = models.FloatField(null=True, blank=True)
    
    # Cost metrics
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_per_bin = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    cost_per_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'route_performance_metrics'

    def __str__(self):
        return f"Metrics for {self.route.name}"

    def calculate_metrics(self):
        """Calculate all performance metrics for the route"""
        route = self.route
        
        # Time efficiency
        if route.estimated_duration_hours and route.actual_duration_hours:
            self.time_efficiency = min(route.estimated_duration_hours / route.actual_duration_hours, 1.0) * 100
        
        # Distance efficiency
        if route.total_distance_km and route.actual_distance_km:
            self.distance_efficiency = min(route.total_distance_km / route.actual_distance_km, 1.0) * 100
        
        # Fuel efficiency
        if route.fuel_consumed_liters and route.actual_distance_km:
            self.fuel_efficiency = route.fuel_consumed_liters / route.actual_distance_km
        
        # Collection rate
        if route.total_bins_planned > 0:
            self.collection_rate = (route.bins_collected / route.total_bins_planned) * 100
        
        # Average fill level
        completed_stops = route.route_stops.filter(status='completed', fill_level_before__isnull=False)
        if completed_stops.exists():
            fill_levels = completed_stops.values_list('fill_level_before', flat=True)
            self.average_fill_level = sum(fill_levels) / len(fill_levels)
            
            # Total waste collected
            weights = completed_stops.filter(estimated_weight_kg__isnull=False).values_list('estimated_weight_kg', flat=True)
            if weights:
                self.total_waste_collected_kg = sum(weights)
        
        self.save()