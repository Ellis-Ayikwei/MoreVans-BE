from django.db import models
from apps.Basemodel.models import Basemodel


class ServiceCategory(Basemodel):
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=30, null=True)
    objects: models.Manager = models.Manager()

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
    providers = models.ManyToManyField(
        "Provider.Provider", through="Provider.ServiceProvider"
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "services"
        managed = True
        verbose_name = "Service"
        verbose_name_plural = "Services"
