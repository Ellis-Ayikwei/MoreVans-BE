from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField


class Alert(models.Model):
    """System-wide alerts for various events."""
    
    class AlertType(models.TextChoices):
        BIN_FULL = 'bin_full', _('Bin Full')
        BIN_OVERFLOW = 'bin_overflow', _('Bin Overflow')
        MAINTENANCE_REQUIRED = 'maintenance', _('Maintenance Required')
        SENSOR_OFFLINE = 'sensor_offline', _('Sensor Offline')
        ROUTE_DELAYED = 'route_delayed', _('Route Delayed')
        VEHICLE_BREAKDOWN = 'vehicle_breakdown', _('Vehicle Breakdown')
        ILLEGAL_DUMPING = 'illegal_dumping', _('Illegal Dumping')
        CITIZEN_REPORT = 'citizen_report', _('Citizen Report')
        SYSTEM_ERROR = 'system_error', _('System Error')
    
    class Severity(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    class AlertStatus(models.TextChoices):
        NEW = 'new', _('New')
        ACKNOWLEDGED = 'acknowledged', _('Acknowledged')
        IN_PROGRESS = 'in_progress', _('In Progress')
        RESOLVED = 'resolved', _('Resolved')
        CLOSED = 'closed', _('Closed')
    
    # Alert details
    alert_type = models.CharField(
        max_length=30,
        choices=AlertType.choices
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=AlertStatus.choices,
        default=AlertStatus.NEW
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related objects
    bin = models.ForeignKey(
        'bins.WasteBin',
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True
    )
    route = models.ForeignKey(
        'routes.CollectionRoute',
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True
    )
    vehicle = models.ForeignKey(
        'routes.Vehicle',
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True
    )
    reported_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_alerts'
    )
    
    # Location
    location = models.PointField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    
    # Alert handling
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_alerts'
    )
    acknowledged_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    resolved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    attachments = ArrayField(
        models.URLField(),
        blank=True,
        default=list
    )
    
    # Notification tracking
    notifications_sent = models.BooleanField(default=False)
    notification_channels = ArrayField(
        models.CharField(max_length=20),
        blank=True,
        default=list
    )
    
    class Meta:
        db_table = 'alerts'
        verbose_name = _('Alert')
        verbose_name_plural = _('Alerts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['alert_type', 'status']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.title}"
    
    @property
    def is_active(self):
        return self.status not in [self.AlertStatus.RESOLVED, self.AlertStatus.CLOSED]
    
    @property
    def response_time(self):
        if self.acknowledged_at:
            return self.acknowledged_at - self.created_at
        return None
    
    @property
    def resolution_time(self):
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return None
    
    def acknowledge(self, user):
        """Acknowledge the alert."""
        self.status = self.AlertStatus.ACKNOWLEDGED
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self, user, resolution_notes=''):
        """Resolve the alert."""
        self.status = self.AlertStatus.RESOLVED
        self.resolved_by = user
        self.resolved_at = timezone.now()
        if resolution_notes:
            self.metadata['resolution_notes'] = resolution_notes
        self.save()


class AlertRule(models.Model):
    """Configurable rules for automatic alert generation."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    
    # Rule conditions
    alert_type = models.CharField(
        max_length=30,
        choices=Alert.AlertType.choices
    )
    
    # Thresholds
    bin_fill_threshold = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Fill level percentage to trigger alert')
    )
    battery_threshold = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Battery level percentage to trigger alert')
    )
    temperature_threshold = models.FloatField(
        null=True,
        blank=True,
        help_text=_('Temperature in Celsius to trigger alert')
    )
    offline_duration = models.DurationField(
        null=True,
        blank=True,
        help_text=_('Duration of offline status to trigger alert')
    )
    
    # Alert configuration
    severity = models.CharField(
        max_length=20,
        choices=Alert.Severity.choices,
        default=Alert.Severity.MEDIUM
    )
    auto_assign = models.BooleanField(default=False)
    notification_channels = ArrayField(
        models.CharField(max_length=20),
        blank=True,
        default=list,
        help_text=_('Channels: email, sms, push, webhook')
    )
    
    # Scope
    zones = models.ManyToManyField(
        'bins.Zone',
        blank=True,
        related_name='alert_rules'
    )
    bin_types = ArrayField(
        models.CharField(max_length=20),
        blank=True,
        default=list
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        db_table = 'alert_rules'
        verbose_name = _('Alert Rule')
        verbose_name_plural = _('Alert Rules')
        ordering = ['name']
        
    def __str__(self):
        return self.name


class AlertComment(models.Model):
    """Comments on alerts for tracking resolution progress."""
    
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE
    )
    
    comment = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text=_('Internal comments are not visible to citizens')
    )
    
    attachments = ArrayField(
        models.URLField(),
        blank=True,
        default=list
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'alert_comments'
        verbose_name = _('Alert Comment')
        verbose_name_plural = _('Alert Comments')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Comment on {self.alert} by {self.user}"


class AlertNotification(models.Model):
    """Track notifications sent for alerts."""
    
    class NotificationChannel(models.TextChoices):
        EMAIL = 'email', _('Email')
        SMS = 'sms', _('SMS')
        PUSH = 'push', _('Push Notification')
        WEBHOOK = 'webhook', _('Webhook')
        IN_APP = 'in_app', _('In-App Notification')
    
    class NotificationStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SENT = 'sent', _('Sent')
        DELIVERED = 'delivered', _('Delivered')
        FAILED = 'failed', _('Failed')
        READ = 'read', _('Read')
    
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    recipient = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='alert_notifications'
    )
    
    channel = models.CharField(
        max_length=20,
        choices=NotificationChannel.choices
    )
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING
    )
    
    # Notification content
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Delivery details
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'alert_notifications'
        verbose_name = _('Alert Notification')
        verbose_name_plural = _('Alert Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['alert', 'channel']),
        ]
        
    def __str__(self):
        return f"{self.channel} notification for {self.alert} to {self.recipient}"
    
    def mark_as_sent(self):
        """Mark notification as sent."""
        self.status = self.NotificationStatus.SENT
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_delivered(self):
        """Mark notification as delivered."""
        self.status = self.NotificationStatus.DELIVERED
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_as_read(self):
        """Mark notification as read."""
        self.status = self.NotificationStatus.READ
        self.read_at = timezone.now()
        self.save()