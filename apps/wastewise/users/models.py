"""
User Models for WasteWise Smart Waste Management System

Custom user model with role-based access control for different types of users:
- Municipal Administrators
- Zone Supervisors  
- Collection Operators
- Citizens
- Maintenance Technicians
"""

from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid


class WasteWiseUser(AbstractUser):
    """Extended user model for WasteWise system"""
    
    USER_ROLES = [
        ('admin', 'Municipal Administrator'),
        ('supervisor', 'Zone Supervisor'),
        ('operator', 'Collection Operator'),
        ('citizen', 'Citizen'),
        ('technician', 'Maintenance Technician'),
        ('analyst', 'Data Analyst'),
        ('customer_support', 'Customer Support'),
    ]
    
    VERIFICATION_STATUS = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Extended profile fields
    phone_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be valid")],
        null=True,
        blank=True
    )
    role = models.CharField(max_length=20, choices=USER_ROLES, default='citizen')
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    # Personal information
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    national_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    # Contact and location
    address = models.TextField(blank=True)
    location = models.PointField(null=True, blank=True, help_text="User's location")
    zone = models.ForeignKey(
        'bins.Zone', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='users'
    )
    
    # Account status
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    is_verified = models.BooleanField(default=False)
    verification_documents = models.JSONField(default=list, blank=True)
    
    # Preferences
    language_preference = models.CharField(
        max_length=5,
        choices=[('en', 'English'), ('tw', 'Twi'), ('ga', 'Ga')],
        default='en'
    )
    notification_preferences = models.JSONField(default=dict, blank=True)
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Work-related fields (for staff)
    department = models.CharField(max_length=100, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    supervisor = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='subordinates'
    )
    
    # Metadata
    last_activity = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wastewise_users'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    @property
    def is_staff_member(self):
        """Check if user is a staff member (not citizen)"""
        return self.role != 'citizen'

    @property
    def can_manage_bins(self):
        """Check if user can manage waste bins"""
        return self.role in ['admin', 'supervisor']

    @property
    def can_view_analytics(self):
        """Check if user can view analytics"""
        return self.role in ['admin', 'supervisor', 'analyst']

    @property
    def can_manage_routes(self):
        """Check if user can manage collection routes"""
        return self.role in ['admin', 'supervisor', 'operator']

    def update_last_activity(self):
        """Update last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


class UserSession(models.Model):
    """Track user sessions for security and analytics"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(WasteWiseUser, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    
    # Session details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('mobile', 'Mobile'),
            ('tablet', 'Tablet'),
            ('desktop', 'Desktop'),
            ('unknown', 'Unknown'),
        ],
        default='unknown'
    )
    
    # Location information
    location = models.PointField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Security flags
    is_suspicious = models.BooleanField(default=False)
    suspicious_reasons = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'user_sessions'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.username} session from {self.ip_address}"

    @property
    def duration(self):
        """Calculate session duration"""
        end_time = self.ended_at or timezone.now()
        return end_time - self.started_at

    def end_session(self):
        """End the session"""
        self.ended_at = timezone.now()
        self.save(update_fields=['ended_at'])


class UserPreferences(models.Model):
    """User preferences and settings"""

    user = models.OneToOneField(WasteWiseUser, on_delete=models.CASCADE, related_name='preferences')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    
    # Specific notification types
    bin_full_alerts = models.BooleanField(default=True)
    collection_reminders = models.BooleanField(default=True)
    maintenance_updates = models.BooleanField(default=False)
    system_announcements = models.BooleanField(default=True)
    
    # Dashboard preferences
    dashboard_layout = models.JSONField(default=dict, blank=True)
    default_map_view = models.PointField(null=True, blank=True)
    default_zoom_level = models.IntegerField(default=12)
    
    # Data and privacy
    share_location = models.BooleanField(default=True)
    share_usage_data = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    
    # Mobile app preferences
    app_theme = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark'), ('auto', 'Auto')],
        default='auto'
    )
    offline_mode = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_preferences'

    def __str__(self):
        return f"Preferences for {self.user.username}"


class UserActivity(models.Model):
    """Log user activities for analytics and auditing"""
    
    ACTIVITY_TYPES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('bin_view', 'Viewed Bin Details'),
        ('bin_create', 'Created Bin'),
        ('bin_update', 'Updated Bin'),
        ('route_create', 'Created Route'),
        ('route_update', 'Updated Route'),
        ('alert_acknowledge', 'Acknowledged Alert'),
        ('alert_resolve', 'Resolved Alert'),
        ('report_generate', 'Generated Report'),
        ('report_view', 'Viewed Report'),
        ('maintenance_schedule', 'Scheduled Maintenance'),
        ('collection_record', 'Recorded Collection'),
        ('profile_update', 'Updated Profile'),
        ('settings_change', 'Changed Settings'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(WasteWiseUser, on_delete=models.CASCADE, related_name='activities')
    
    # Activity details
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.TextField()
    
    # Context information
    object_type = models.CharField(max_length=50, blank=True)  # e.g., 'WasteBin', 'Route'
    object_id = models.CharField(max_length=100, blank=True)  # UUID or ID of the object
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Location if available
    location = models.PointField(null=True, blank=True)
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_activities'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['activity_type', '-timestamp']),
            models.Index(fields=['object_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()}"


class UserNotificationSettings(models.Model):
    """Detailed notification settings for users"""

    user = models.OneToOneField(WasteWiseUser, on_delete=models.CASCADE, related_name='notification_settings')
    
    # Email settings
    email_enabled = models.BooleanField(default=True)
    email_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('hourly', 'Hourly Digest'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Digest'),
        ],
        default='immediate'
    )
    
    # SMS settings
    sms_enabled = models.BooleanField(default=False)
    sms_for_emergencies_only = models.BooleanField(default=True)
    
    # Push notification settings
    push_enabled = models.BooleanField(default=True)
    push_sound_enabled = models.BooleanField(default=True)
    push_vibration_enabled = models.BooleanField(default=True)
    
    # WhatsApp settings (if integrated)
    whatsapp_enabled = models.BooleanField(default=False)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    
    # Specific alert types
    bin_overflow_alerts = models.BooleanField(default=True)
    sensor_offline_alerts = models.BooleanField(default=True)
    route_updates = models.BooleanField(default=True)
    maintenance_notifications = models.BooleanField(default=False)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_start_time = models.TimeField(null=True, blank=True)
    quiet_end_time = models.TimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_notification_settings'

    def __str__(self):
        return f"Notification settings for {self.user.username}"

    def is_quiet_time(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled or not self.quiet_start_time or not self.quiet_end_time:
            return False
        
        now = timezone.now().time()
        
        if self.quiet_start_time <= self.quiet_end_time:
            # Same day quiet hours (e.g., 22:00 to 06:00)
            return self.quiet_start_time <= now <= self.quiet_end_time
        else:
            # Quiet hours span midnight (e.g., 22:00 to 06:00)
            return now >= self.quiet_start_time or now <= self.quiet_end_time