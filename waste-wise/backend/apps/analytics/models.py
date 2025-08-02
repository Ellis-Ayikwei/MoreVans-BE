from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
import uuid


class AnalyticsReport(models.Model):
    """Generated analytics reports."""
    
    class ReportType(models.TextChoices):
        DAILY = 'daily', _('Daily Report')
        WEEKLY = 'weekly', _('Weekly Report')
        MONTHLY = 'monthly', _('Monthly Report')
        QUARTERLY = 'quarterly', _('Quarterly Report')
        ANNUAL = 'annual', _('Annual Report')
        CUSTOM = 'custom', _('Custom Report')
    
    class ReportStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
    
    report_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=200)
    report_type = models.CharField(
        max_length=20,
        choices=ReportType.choices
    )
    status = models.CharField(
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.PENDING
    )
    
    # Report period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Scope
    zones = models.ManyToManyField(
        'bins.Zone',
        blank=True,
        related_name='analytics_reports'
    )
    include_all_zones = models.BooleanField(default=True)
    
    # Report data
    data = models.JSONField(default=dict)
    summary = models.JSONField(default=dict)
    
    # Files
    pdf_file = models.FileField(
        upload_to='reports/pdf/',
        null=True,
        blank=True
    )
    excel_file = models.FileField(
        upload_to='reports/excel/',
        null=True,
        blank=True
    )
    
    # Generation details
    generated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports'
    )
    generation_time = models.DurationField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_reports'
        verbose_name = _('Analytics Report')
        verbose_name_plural = _('Analytics Reports')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} - {self.report_type} ({self.start_date} to {self.end_date})"


class KPI(models.Model):
    """Key Performance Indicators tracking."""
    
    class KPIType(models.TextChoices):
        COLLECTION_EFFICIENCY = 'collection_efficiency', _('Collection Efficiency')
        ROUTE_OPTIMIZATION = 'route_optimization', _('Route Optimization')
        BIN_UTILIZATION = 'bin_utilization', _('Bin Utilization')
        RESPONSE_TIME = 'response_time', _('Response Time')
        FUEL_EFFICIENCY = 'fuel_efficiency', _('Fuel Efficiency')
        RECYCLING_RATE = 'recycling_rate', _('Recycling Rate')
        CITIZEN_SATISFACTION = 'citizen_satisfaction', _('Citizen Satisfaction')
        COST_PER_TON = 'cost_per_ton', _('Cost per Ton')
    
    kpi_type = models.CharField(
        max_length=30,
        choices=KPIType.choices
    )
    zone = models.ForeignKey(
        'bins.Zone',
        on_delete=models.CASCADE,
        related_name='kpis',
        null=True,
        blank=True
    )
    
    # KPI values
    value = models.FloatField()
    target = models.FloatField()
    unit = models.CharField(max_length=20)
    
    # Period
    date = models.DateField()
    period_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly')
        ]
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'kpis'
        verbose_name = _('KPI')
        verbose_name_plural = _('KPIs')
        ordering = ['-date']
        unique_together = [['kpi_type', 'zone', 'date', 'period_type']]
        
    def __str__(self):
        return f"{self.get_kpi_type_display()} - {self.date} - {self.value}{self.unit}"
    
    @property
    def performance_percentage(self):
        """Calculate performance against target."""
        if self.target > 0:
            return (self.value / self.target) * 100
        return 0


class Prediction(models.Model):
    """ML-based predictions for waste management."""
    
    class PredictionType(models.TextChoices):
        FILL_LEVEL = 'fill_level', _('Fill Level Prediction')
        COLLECTION_TIME = 'collection_time', _('Collection Time Prediction')
        WASTE_GENERATION = 'waste_generation', _('Waste Generation Prediction')
        ROUTE_DURATION = 'route_duration', _('Route Duration Prediction')
    
    prediction_type = models.CharField(
        max_length=30,
        choices=PredictionType.choices
    )
    
    # Target
    bin = models.ForeignKey(
        'bins.WasteBin',
        on_delete=models.CASCADE,
        related_name='predictions',
        null=True,
        blank=True
    )
    zone = models.ForeignKey(
        'bins.Zone',
        on_delete=models.CASCADE,
        related_name='predictions',
        null=True,
        blank=True
    )
    
    # Prediction details
    prediction_date = models.DateField()
    prediction_time = models.TimeField(null=True, blank=True)
    predicted_value = models.FloatField()
    confidence_score = models.FloatField(
        help_text=_('Confidence score 0-1')
    )
    
    # Model information
    model_name = models.CharField(max_length=50)
    model_version = models.CharField(max_length=20)
    features_used = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list
    )
    
    # Validation
    actual_value = models.FloatField(null=True, blank=True)
    error_margin = models.FloatField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'predictions'
        verbose_name = _('Prediction')
        verbose_name_plural = _('Predictions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['prediction_type', 'prediction_date']),
            models.Index(fields=['bin', 'prediction_date']),
        ]
        
    def __str__(self):
        return f"{self.get_prediction_type_display()} - {self.prediction_date} - {self.predicted_value}"
    
    def calculate_accuracy(self):
        """Calculate prediction accuracy if actual value is available."""
        if self.actual_value is not None:
            error = abs(self.predicted_value - self.actual_value)
            if self.actual_value > 0:
                return 100 - (error / self.actual_value * 100)
        return None


class Dashboard(models.Model):
    """Customizable dashboards for different user roles."""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='dashboards',
        null=True,
        blank=True
    )
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    
    # Dashboard configuration
    layout = models.JSONField(
        default=dict,
        help_text=_('Dashboard layout configuration')
    )
    widgets = models.JSONField(
        default=list,
        help_text=_('List of widgets and their configurations')
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboards'
        verbose_name = _('Dashboard')
        verbose_name_plural = _('Dashboards')
        ordering = ['name']
        
    def __str__(self):
        return self.name


class DataExport(models.Model):
    """Track data export requests."""
    
    class ExportFormat(models.TextChoices):
        CSV = 'csv', _('CSV')
        EXCEL = 'excel', _('Excel')
        JSON = 'json', _('JSON')
        PDF = 'pdf', _('PDF')
    
    class ExportStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        EXPIRED = 'expired', _('Expired')
    
    export_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Export configuration
    data_type = models.CharField(max_length=50)
    filters = models.JSONField(default=dict)
    format = models.CharField(
        max_length=10,
        choices=ExportFormat.choices
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=ExportStatus.choices,
        default=ExportStatus.PENDING
    )
    
    # Files
    file = models.FileField(
        upload_to='exports/',
        null=True,
        blank=True
    )
    file_size = models.BigIntegerField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    
    # User
    requested_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='data_exports'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'data_exports'
        verbose_name = _('Data Export')
        verbose_name_plural = _('Data Exports')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} - {self.format} - {self.status}"