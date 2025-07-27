"""
IoT Sensor Models for WasteWise Smart Waste Management System

These models handle sensor data from ESP32 devices monitoring waste bins.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.gis.db import models as gis_models
import uuid
import json


class SensorDevice(models.Model):
    """IoT sensor device information and configuration"""
    
    SENSOR_TYPES = [
        ('ultrasonic', 'Ultrasonic Distance Sensor'),
        ('weight', 'Weight Sensor'),
        ('temperature', 'Temperature Sensor'),
        ('humidity', 'Humidity Sensor'),
        ('gas', 'Gas Sensor'),
        ('motion', 'Motion Sensor'),
    ]
    
    DEVICE_STATUS = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance'),
        ('low_battery', 'Low Battery'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_id = models.CharField(max_length=50, unique=True, help_text="Unique device identifier")
    bin = models.OneToOneField(
        'bins.WasteBin', 
        on_delete=models.CASCADE, 
        related_name='sensor_device'
    )
    
    # Device specifications
    manufacturer = models.CharField(max_length=100, default='ESP32')
    model = models.CharField(max_length=100)
    firmware_version = models.CharField(max_length=20)
    hardware_version = models.CharField(max_length=20)
    
    # Sensor configuration
    sensor_types = models.JSONField(default=list, help_text="List of sensor types on this device")
    calibration_data = models.JSONField(default=dict, help_text="Sensor calibration parameters")
    
    # Communication settings
    wifi_ssid = models.CharField(max_length=100, blank=True)
    mqtt_topic = models.CharField(max_length=200)
    transmission_interval_minutes = models.IntegerField(
        default=15,
        validators=[MinValueValidator(1), MaxValueValidator(1440)]
    )
    
    # Status and monitoring
    status = models.CharField(max_length=20, choices=DEVICE_STATUS, default='offline')
    last_seen = models.DateTimeField(null=True, blank=True)
    last_data_received = models.DateTimeField(null=True, blank=True)
    battery_level = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    signal_strength = models.IntegerField(null=True, blank=True, help_text="RSSI value")
    
    # Installation details
    installation_date = models.DateField()
    last_maintenance = models.DateTimeField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    
    # Configuration
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sensor_devices'
        ordering = ['device_id']

    def __str__(self):
        return f"Sensor {self.device_id} - {self.bin.bin_id}"

    @property
    def is_online(self):
        """Check if device is currently online based on last seen time"""
        if not self.last_seen:
            return False
        threshold = timezone.now() - timezone.timedelta(minutes=self.transmission_interval_minutes * 2)
        return self.last_seen > threshold

    @property
    def uptime_percentage(self):
        """Calculate uptime percentage over the last 30 days"""
        from django.db.models import Count, Q
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        total_expected_readings = (30 * 24 * 60) // self.transmission_interval_minutes
        actual_readings = self.sensor_readings.filter(
            timestamp__gte=thirty_days_ago
        ).count()
        
        return (actual_readings / total_expected_readings * 100) if total_expected_readings > 0 else 0

    def update_status(self):
        """Update device status based on recent activity and battery level"""
        if self.battery_level < 10:
            self.status = 'low_battery'
        elif not self.is_online:
            self.status = 'offline'
        else:
            self.status = 'online'
        self.save(update_fields=['status'])


class SensorReading(models.Model):
    """Individual sensor readings from IoT devices"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(SensorDevice, on_delete=models.CASCADE, related_name='sensor_readings')
    bin = models.ForeignKey('bins.WasteBin', on_delete=models.CASCADE, related_name='sensor_readings')
    
    # Primary sensor data
    fill_level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Fill level percentage (0-100%)"
    )
    distance_cm = models.FloatField(
        null=True, 
        blank=True,
        help_text="Distance from sensor to waste surface in cm"
    )
    
    # Environmental data
    temperature = models.FloatField(
        null=True, 
        blank=True,
        help_text="Temperature in Celsius"
    )
    humidity = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Humidity percentage"
    )
    
    # Device health data
    battery_level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Battery level percentage"
    )
    signal_strength = models.IntegerField(
        null=True, 
        blank=True,
        help_text="WiFi signal strength (RSSI)"
    )
    
    # Additional sensor data (JSON for flexibility)
    additional_data = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Additional sensor data (weight, gas levels, etc.)"
    )
    
    # Quality indicators
    data_quality = models.CharField(
        max_length=20,
        choices=[
            ('good', 'Good'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('calibration_needed', 'Calibration Needed'),
        ],
        default='good'
    )
    
    # Timestamp and metadata
    timestamp = models.DateTimeField(help_text="When the reading was taken")
    received_at = models.DateTimeField(auto_now_add=True, help_text="When data was received by server")
    
    # Processing flags
    is_processed = models.BooleanField(default=False)
    is_anomaly = models.BooleanField(default=False)
    anomaly_reason = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'sensor_readings'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['bin', '-timestamp']),
            models.Index(fields=['device', '-timestamp']),
            models.Index(fields=['fill_level', 'timestamp']),
            models.Index(fields=['is_processed']),
        ]

    def __str__(self):
        return f"{self.bin.bin_id} - {self.fill_level}% at {self.timestamp}"

    def save(self, *args, **kwargs):
        """Override save to perform data validation and processing"""
        # Detect anomalies
        self.detect_anomalies()
        
        # Update bin status if fill level is high
        if self.fill_level >= 85 and self.bin.status == 'active':
            self.bin.status = 'full'
            self.bin.save(update_fields=['status'])
        
        super().save(*args, **kwargs)
        
        # Update device status
        self.device.last_data_received = self.received_at
        self.device.battery_level = self.battery_level
        if self.signal_strength:
            self.device.signal_strength = self.signal_strength
        self.device.update_status()

    def detect_anomalies(self):
        """Detect anomalous readings based on historical data"""
        # Get recent readings for comparison
        recent_readings = SensorReading.objects.filter(
            bin=self.bin,
            timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
        ).exclude(pk=self.pk).values_list('fill_level', flat=True)
        
        if recent_readings:
            avg_fill = sum(recent_readings) / len(recent_readings)
            
            # Check for sudden large changes
            if abs(self.fill_level - avg_fill) > 50:
                self.is_anomaly = True
                self.anomaly_reason = "Sudden large change in fill level"
                self.data_quality = 'error'
            
            # Check for impossible readings
            if self.fill_level > 100 or self.fill_level < 0:
                self.is_anomaly = True
                self.anomaly_reason = "Impossible fill level value"
                self.data_quality = 'error'


class SensorAlert(models.Model):
    """Alerts generated based on sensor data"""
    
    ALERT_TYPES = [
        ('bin_full', 'Bin Full'),
        ('bin_overflow', 'Bin Overflow'),
        ('sensor_offline', 'Sensor Offline'),
        ('low_battery', 'Low Battery'),
        ('sensor_error', 'Sensor Error'),
        ('data_anomaly', 'Data Anomaly'),
        ('maintenance_due', 'Maintenance Due'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(SensorDevice, on_delete=models.CASCADE, related_name='alerts')
    bin = models.ForeignKey('bins.WasteBin', on_delete=models.CASCADE, related_name='sensor_alerts')
    reading = models.ForeignKey(
        SensorReading, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='generated_alerts'
    )
    
    # Alert details
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Resolution tracking
    is_active = models.BooleanField(default=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        'users.WasteWiseUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_sensor_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        'users.WasteWiseUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_sensor_alerts'
    )
    resolution_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sensor_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['bin', 'is_active']),
            models.Index(fields=['alert_type', 'severity']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.bin.bin_id}"

    def acknowledge(self, user):
        """Acknowledge the alert"""
        self.acknowledged_at = timezone.now()
        self.acknowledged_by = user
        self.save(update_fields=['acknowledged_at', 'acknowledged_by'])

    def resolve(self, user, notes=""):
        """Resolve the alert"""
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.resolution_notes = notes
        self.is_active = False
        self.save(update_fields=['resolved_at', 'resolved_by', 'resolution_notes', 'is_active'])


class SensorCalibration(models.Model):
    """Sensor calibration records"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(SensorDevice, on_delete=models.CASCADE, related_name='calibrations')
    
    # Calibration details
    calibration_type = models.CharField(
        max_length=20,
        choices=[
            ('initial', 'Initial Setup'),
            ('routine', 'Routine Calibration'),
            ('corrective', 'Corrective Calibration'),
            ('factory_reset', 'Factory Reset'),
        ]
    )
    
    # Calibration parameters
    empty_distance_cm = models.FloatField(help_text="Distance when bin is empty")
    full_distance_cm = models.FloatField(help_text="Distance when bin is full")
    temperature_offset = models.FloatField(default=0.0)
    
    # Quality metrics
    accuracy_test_results = models.JSONField(default=dict)
    calibration_quality = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('acceptable', 'Acceptable'),
            ('poor', 'Poor'),
        ],
        default='good'
    )
    
    # Personnel and timing
    performed_by = models.ForeignKey(
        'users.WasteWiseUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='calibrations_performed'
    )
    performed_at = models.DateTimeField()
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sensor_calibrations'
        ordering = ['-performed_at']

    def __str__(self):
        return f"Calibration for {self.device.device_id} on {self.performed_at.date()}"