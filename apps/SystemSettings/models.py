from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.Basemodel.models import Basemodel
import json


class SystemSetting(Basemodel):
    """Store system-wide configuration settings"""

    SECTION_CHOICES = [
        ("general", "General Settings"),
        ("notifications", "Notification Settings"),
        ("payment", "Payment Settings"),
        ("appearance", "Appearance Settings"),
    ]

    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    key = models.CharField(max_length=100)
    value = models.TextField()
    data_type = models.CharField(
        max_length=20,
        choices=[
            ("string", "String"),
            ("integer", "Integer"),
            ("float", "Float"),
            ("boolean", "Boolean"),
            ("json", "JSON"),
        ],
        default="string",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "system_settings"
        unique_together = ("section", "key")
        indexes = [
            models.Index(fields=["section"]),
            models.Index(fields=["key"]),
        ]

    def __str__(self):
        return f"{self.section}.{self.key}"

    def get_value(self):
        """Convert stored value to appropriate Python type"""
        if self.data_type == "boolean":
            return self.value.lower() == "true"
        elif self.data_type == "integer":
            return int(self.value)
        elif self.data_type == "float":
            return float(self.value)
        elif self.data_type == "json":
            return json.loads(self.value)
        return self.value

    def set_value(self, value):
        """Convert Python value to stored string"""
        if self.data_type == "json":
            self.value = json.dumps(value)
        else:
            self.value = str(value)


class PaymentGateway(Basemodel):
    """Store payment gateway configurations"""

    GATEWAY_CHOICES = [
        ("stripe", "Stripe"),
        ("paypal", "PayPal"),
        ("square", "Square"),
        ("razorpay", "Razorpay"),
        ("authorize_net", "Authorize.net"),
    ]

    gateway_id = models.CharField(max_length=50, choices=GATEWAY_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    test_mode = models.BooleanField(default=True)
    api_key = models.TextField(blank=True)
    secret_key = models.TextField(blank=True)
    merchant_id = models.CharField(max_length=100, blank=True)
    webhook_secret = models.TextField(blank=True)
    configuration = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "payment_gateways"

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
