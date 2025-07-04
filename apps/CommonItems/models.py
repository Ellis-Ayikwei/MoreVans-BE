from django.db import models
from apps.Basemodel.models import Basemodel


class ItemCategory(Basemodel):
    """Categories of items that can be transported"""

    name = models.CharField(max_length=100)
    requires_special_handling = models.BooleanField(default=False)
    restricted = models.BooleanField(default=False)
    insurance_required = models.BooleanField(default=False)
    price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    special_instructions = models.TextField(blank=True)
    description = models.TextField(blank=True)
    # Add icon/image for frontend display
    icon = models.CharField(
        max_length=100, blank=True, help_text="FontAwesome icon name"
    )
    image = models.URLField(blank=True, help_text="URL to category image")
    color = models.CharField(max_length=255, blank=True, help_text="Hex color code")
    tab_color = models.CharField(max_length=255, blank=True, help_text="Hex color code")

    class Meta:
        db_table = "item_category"
        managed = True
        verbose_name = "Item Category"
        verbose_name_plural = "Item Categories"


# Add this new model to handle common items for pickup points
class CommonItem(Basemodel):
    """Common items that can be selected for pickup points"""

    name = models.CharField(max_length=100)
    category = models.ForeignKey(ItemCategory, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    dimensions = models.JSONField(null=True, blank=True)
    fragile = models.BooleanField(default=False)
    needs_disassembly = models.BooleanField(default=False)
    icon = models.CharField(
        max_length=100, blank=True, help_text="FontAwesome icon name"
    )
    model = models.CharField(max_length=100, blank=True, help_text="Model name")
    brand = models.CharField(max_length=100, blank=True, help_text="Brand name")
    color = models.CharField(max_length=255, blank=True, help_text="Hex color code")
    tab_color = models.CharField(max_length=255, blank=True, help_text="Hex color code")
    image = models.URLField(blank=True, help_text="URL to item image")
    service_category = models.ForeignKey(
        "ServiceCategory",  # Replace with the actual model name
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Service category for this category of items",
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "common_item"
        managed = True
        verbose_name = "Common Item"
        verbose_name_plural = "Common Items"
