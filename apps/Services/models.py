from django.db import models
from apps.Basemodel.models import Basemodel


class ServiceCategory(Basemodel):
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=30, null=True)
    color = models.CharField(max_length=50, blank=True, help_text="CSS color classes")
    tab_color = models.CharField(
        max_length=50, blank=True, help_text="CSS color classes for tabs"
    )
    objects: models.Manager = models.Manager()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "service_category"
        managed = True
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"


class Services(Basemodel):
    """Model representing a service offered by the platform"""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    service_category = models.ForeignKey(
        ServiceCategory, on_delete=models.CASCADE, related_name="services"
    )
    icon = models.CharField(max_length=30, null=True)
    color = models.CharField(max_length=50, blank=True, help_text="CSS color classes")
    estimated_duration = models.PositiveIntegerField(
        null=True, blank=True, help_text="Estimated duration in hours"
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Base price for the service",
    )
    providers = models.ManyToManyField(
        "Provider.ServiceProvider", through="Provider.ServiceProviderThrough"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "services"
        managed = True
        verbose_name = "Service"
        verbose_name_plural = "Services"
