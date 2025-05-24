from django.db import models
from apps.Basemodel.models import Basemodel
from apps.CommonItems.models import ItemCategory
from apps.Request.models import Request


class RequestItem(Basemodel):
    """Individual items within a request"""

    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="items")
    category = models.ForeignKey(ItemCategory, on_delete=models.PROTECT)
    name = models.CharField(max_length=100, default="Unnamed Item")
    description = models.TextField(blank=True)
    quantity = models.IntegerField(default=1)
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    dimensions = models.JSONField(null=True, blank=True)
    fragile = models.BooleanField(default=False)
    needs_disassembly = models.BooleanField(default=False)
    special_instructions = models.TextField(blank=True)
    photos = models.JSONField(null=True, blank=True)
    declared_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    pickup_stop = models.ForeignKey(
        "JourneyStop.JourneyStop",
        related_name="pickup_items",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    dropoff_stop = models.ForeignKey(
        "JourneyStop.JourneyStop",
        related_name="dropoff_items",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.name} ({self.quantity}) - Request: {self.request.tracking_number}"
        )

    class Meta:
        db_table = "request_item"
        managed = True
        verbose_name = "Request Item"
        verbose_name_plural = "Request Items"
