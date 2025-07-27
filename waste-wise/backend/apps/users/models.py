from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom User model with additional fields for waste management system."""
    
    class UserRole(models.TextChoices):
        ADMIN = 'admin', _('Administrator')
        OPERATOR = 'operator', _('Operator')
        DRIVER = 'driver', _('Driver')
        CITIZEN = 'citizen', _('Citizen')
        
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CITIZEN
    )
    
    # Profile fields
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, default='Accra')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_location = models.JSONField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def is_admin(self):
        return self.role == self.UserRole.ADMIN
    
    @property
    def is_operator(self):
        return self.role == self.UserRole.OPERATOR
    
    @property
    def is_driver(self):
        return self.role == self.UserRole.DRIVER
    
    @property
    def is_citizen(self):
        return self.role == self.UserRole.CITIZEN
    
    def get_role_display_name(self):
        return self.get_role_display()


class UserActivity(models.Model):
    """Track user activities in the system."""
    
    class ActivityType(models.TextChoices):
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        BIN_REPORT = 'bin_report', _('Bin Report')
        ROUTE_COMPLETED = 'route_completed', _('Route Completed')
        ALERT_RESOLVED = 'alert_resolved', _('Alert Resolved')
        
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(
        max_length=50,
        choices=ActivityType.choices
    )
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        verbose_name = _('User Activity')
        verbose_name_plural = _('User Activities')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} - {self.created_at}"