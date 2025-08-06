from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone
import uuid
from django.contrib.gis.db import models as gis_models
from django.db.models import JSONField
from django.contrib.auth.models import AbstractUser, Group, Permission

from datetime import datetime, time
from http import client
from math import prod
from operator import add
import random
from django.db import models
from django.forms import model_to_dict
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid

from apps.Basemodel.models import Basemodel


# accounts/managers.py or accounts/models.py
from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email, password=None, **extra_fields
    ):  # Remove username parameter
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("user_type", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email, password, **extra_fields
        )  # Pass only email, not username


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ("customer", "Customer"),
        ("provider", "Service Provider"),
        ("admin", "Admin"),
    )

    ACCOUNT_STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("pending", "Pending"),
        ("suspended", "Suspended"),
        ("deleted", "Deleted"),
        ("banned", "Banned"),
        ("expired", "Expired"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    user_addresses = models.OneToOneField(
        "Address", on_delete=models.SET_NULL, null=True, blank=True, related_name="user"
    )
    profile_picture = models.ImageField(
        upload_to="profile_pics/", null=True, blank=True
    )
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    stripe_customer_id = models.CharField(max_length=100, null=True, blank=True)
    notification_preferences = models.JSONField(default=dict)
    last_active = models.DateTimeField(null=True)
    device_tokens = models.JSONField(default=list)
    user_type = models.CharField(
        max_length=20, choices=USER_TYPE_CHOICES, default="customer"
    )
    account_status = models.CharField(
        max_length=20, choices=ACCOUNT_STATUS_CHOICES, default="active"
    )

    username = None

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    groups = models.ManyToManyField(
        Group,
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to.",
        related_name="custom_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="custom_user_set",
        related_query_name="user",
    )

    def calculate_rating(self):
        reviews = self.reviews_received.all()
        if reviews:
            return sum(review.rating for review in reviews) / reviews.count()
        return 0.0

    def get_active_trips(self):
        """Get all active trips (in progress, not completed)"""
        from Request.models import Request

        return Request.objects.filter(user=self, status__in=["accepted", "in_transit"])

    def get_bidding_requests(self):
        """Get all requests in bidding state"""
        from Request.models import Request

        return Request.objects.filter(user=self, status="bidding")

    def get_completed_trips(self):
        """Get all completed trips"""
        from Request.models import Request

        return Request.objects.filter(user=self, status="completed")

    def get_watched_requests(self):
        """Get all requests user is watching"""
        return self.watched_requests.all()

    def get_request_history(self):
        """Get full request history"""
        from Request.models import Request

        return Request.objects.filter(user=self)

    class Meta:
        managed = True
        db_table = "users"
        swappable = "AUTH_USER_MODEL"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def requires_verification(self):
        """
        Check if user requires email verification.
        Returns True if user is not active or email is not verified.
        """
        # Check if user has verification record
        if hasattr(self, "verification"):
            return not self.verification.email_verified
        # If no verification record exists, assume verification is required
        return True


class Address(Basemodel):
    ADDRESS_TYPES = [("billing", "Billing"), ("shipping", "Shipping"), ("both", "Both")]

    address_user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, related_name="addresses"
    )
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    address_type = models.CharField(
        max_length=10, choices=ADDRESS_TYPES, default="both"
    )

    class Meta:
        managed = True
        db_table = "addresses"

    def __str__(self):
        return self.address


class UserActivity(Basemodel):
    """Track user activity history"""

    ACTIVITY_TYPES = [
        ("view_request", "Viewed Request"),
        ("place_bid", "Placed Bid"),
        ("create_request", "Created Request"),
        ("watch_request", "Watched Request"),
        ("update_request", "Updated Request"),
        ("cancel_request", "Cancelled Request"),
        ("payment", "Made Payment"),
        ("review", "Left Review"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    request = models.ForeignKey("Request.Request", on_delete=models.CASCADE, null=True)
    details = models.JSONField(null=True)  # Store additional activity details

    class Meta:
        ordering = ["-created_at"]  # Updated to use created_at from Basemodel
        managed = True
        db_table = "user_activity"

    def __str__(self):
        return f"{self.user.email} - {self.activity_type}"
