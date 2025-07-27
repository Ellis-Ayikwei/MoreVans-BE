from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class SensorReading(models.Model):
    """IoT sensor readings from waste bins."""
    
    bin = models.ForeignKey(
        'bins.WasteBin',
        on_delete=models.CASCADE,
        related_name='sensor_readings'
    )
    
    # Sensor measurements
    fill_level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Fill level in percentage')
    )
    temperature = models.FloatField(
        help_text=_('Temperature in Celsius'),
        null=True,
        blank=True
    )
    humidity = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Humidity in percentage'),
        null=True,
        blank=True
    )
    
    # Device health
    battery_level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Battery level in percentage')
    )
    signal_strength = models.IntegerField(
        help_text=_('RSSI signal strength in dBm'),
        null=True,
        blank=True
    )
    
    # Additional sensor data
    weight = models.FloatField(
        help_text=_('Weight in kg'),
        null=True,
        blank=True
    )
    methane_level = models.FloatField(
        help_text=_('Methane level in ppm'),
        null=True,
        blank=True
    )
    
    # Raw data for debugging
    raw_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now)
    received_at = models.DateTimeField(auto_now_add=True)
    
    # Data quality
    is_valid = models.BooleanField(default=True)
    error_message = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'sensor_readings'
        verbose_name = _('Sensor Reading')
        verbose_name_plural = _('Sensor Readings')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['bin', '-timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['fill_level']),
        ]
        
    def __str__(self):
        return f"{self.bin.bin_id} - {self.fill_level}% - {self.timestamp}"
    
    def save(self, *args, **kwargs):
        """Update bin's current state when saving new reading."""
        super().save(*args, **kwargs)
        
        # Update bin's current state
        self.bin.current_fill_level = self.fill_level
        self.bin.battery_level = self.battery_level
        self.bin.last_sensor_reading = self.timestamp
        self.bin.save(update_fields=[
            'current_fill_level',
            'battery_level',
            'last_sensor_reading'
        ])


class SensorAlert(models.Model):
    """Alerts generated from sensor readings."""
    
    class AlertType(models.TextChoices):
        HIGH_FILL = 'high_fill', _('High Fill Level')
        RAPID_FILL = 'rapid_fill', _('Rapid Fill Rate')
        LOW_BATTERY = 'low_battery', _('Low Battery')
        SENSOR_OFFLINE = 'offline', _('Sensor Offline')
        TEMPERATURE_HIGH = 'temp_high', _('High Temperature')
        METHANE_HIGH = 'methane_high', _('High Methane Level')
        SENSOR_MALFUNCTION = 'malfunction', _('Sensor Malfunction')
    
    class Severity(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    sensor_reading = models.ForeignKey(
        SensorReading,
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True
    )
    bin = models.ForeignKey(
        'bins.WasteBin',
        on_delete=models.CASCADE,
        related_name='sensor_alerts'
    )
    
    alert_type = models.CharField(
        max_length=20,
        choices=AlertType.choices
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Alert handling
    is_active = models.BooleanField(default=True)
    acknowledged_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_sensor_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sensor_alerts'
        verbose_name = _('Sensor Alert')
        verbose_name_plural = _('Sensor Alerts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['bin', 'is_active']),
            models.Index(fields=['alert_type', 'severity']),
        ]
        
    def __str__(self):
        return f"{self.bin.bin_id} - {self.alert_type} - {self.severity}"


class SensorCalibration(models.Model):
    """Calibration records for sensors."""
    
    bin = models.ForeignKey(
        'bins.WasteBin',
        on_delete=models.CASCADE,
        related_name='calibrations'
    )
    
    # Calibration parameters
    empty_distance = models.FloatField(
        help_text=_('Distance reading when bin is empty (cm)')
    )
    full_distance = models.FloatField(
        help_text=_('Distance reading when bin is full (cm)')
    )
    offset = models.FloatField(
        default=0.0,
        help_text=_('Offset adjustment')
    )
    
    # Calibration metadata
    calibrated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sensor_calibrations'
    )
    calibration_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    
    # Validation
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'sensor_calibrations'
        verbose_name = _('Sensor Calibration')
        verbose_name_plural = _('Sensor Calibrations')
        ordering = ['-calibration_date']
        
    def __str__(self):
        return f"{self.bin.bin_id} - Calibration {self.calibration_date}"


class SensorDataAggregation(models.Model):
    """Aggregated sensor data for analytics."""
    
    class AggregationPeriod(models.TextChoices):
        HOURLY = 'hourly', _('Hourly')
        DAILY = 'daily', _('Daily')
        WEEKLY = 'weekly', _('Weekly')
        MONTHLY = 'monthly', _('Monthly')
    
    bin = models.ForeignKey(
        'bins.WasteBin',
        on_delete=models.CASCADE,
        related_name='aggregated_data'
    )
    
    period = models.CharField(
        max_length=20,
        choices=AggregationPeriod.choices
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Aggregated metrics
    avg_fill_level = models.FloatField()
    max_fill_level = models.IntegerField()
    min_fill_level = models.IntegerField()
    
    avg_temperature = models.FloatField(null=True, blank=True)
    max_temperature = models.FloatField(null=True, blank=True)
    min_temperature = models.FloatField(null=True, blank=True)
    
    reading_count = models.IntegerField()
    
    # Fill rate analysis
    fill_rate = models.FloatField(
        help_text=_('Average fill rate in percentage per hour'),
        null=True,
        blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sensor_data_aggregations'
        verbose_name = _('Sensor Data Aggregation')
        verbose_name_plural = _('Sensor Data Aggregations')
        ordering = ['-period_start']
        unique_together = [['bin', 'period', 'period_start']]
        indexes = [
            models.Index(fields=['bin', 'period', '-period_start']),
        ]
        
    def __str__(self):
        return f"{self.bin.bin_id} - {self.period} - {self.period_start}"