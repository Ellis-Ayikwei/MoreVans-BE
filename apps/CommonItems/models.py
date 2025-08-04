from django.db import models
from apps.Basemodel.models import Basemodel


class ItemCategory(Basemodel):
    """Categories of items that can be transported"""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    requires_special_handling = models.BooleanField(default=False, null=True)
    restricted = models.BooleanField(default=False, null=True)
    insurance_required = models.BooleanField(default=False, null=True)
    price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    special_instructions = models.TextField(blank=True)
    # Visual properties for frontend
    icon = models.CharField(
        max_length=100, blank=True, help_text="FontAwesome icon name"
    )
    image = models.URLField(blank=True, help_text="URL to category image")
    color = models.CharField(max_length=255, blank=True, help_text="Hex color code")
    tab_color = models.CharField(max_length=255, blank=True, help_text="Hex color code")

    def __str__(self):
        return self.name

    class Meta:
        db_table = "item_category"
        managed = True
        verbose_name = "Item Category"
        verbose_name_plural = "Item Categories"
        ordering = ["name"]


class ItemType(Basemodel):
    """Types of items within categories (e.g., cars, motorcycles, boats under automotive)"""

    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.CASCADE,
        related_name="types",
        help_text="Category this type belongs to",
    )
    description = models.TextField(blank=True)
    # Visual properties for frontend
    icon = models.CharField(
        max_length=100, blank=True, help_text="FontAwesome icon name"
    )
    image = models.URLField(blank=True, help_text="URL to type image")
    color = models.CharField(max_length=255, blank=True, help_text="Hex color code")
    tab_color = models.CharField(max_length=255, blank=True, help_text="Hex color code")
    priority = models.IntegerField(default=0, help_text="Display priority order")
    is_active = models.BooleanField(
        default=True, help_text="Type is active and available"
    )

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    class Meta:
        db_table = "item_type"
        managed = True
        verbose_name = "Item Type"
        verbose_name_plural = "Item Types"
        ordering = ["category__name", "priority", "name"]
        unique_together = ["name", "category"]


class ItemBrand(Basemodel):
    """Brands of items that can be transported"""

    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.CASCADE,
        related_name="brands",
        help_text="Category this brand belongs to",
    )
    type = models.ForeignKey(
        ItemType,
        on_delete=models.CASCADE,
        related_name="brands",
        help_text="Type this brand belongs to",
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True)
    # Visual properties for frontend
    icon = models.CharField(
        max_length=100, blank=True, help_text="FontAwesome icon name"
    )
    image = models.URLField(blank=True, help_text="URL to brand image")
    color = models.CharField(max_length=255, blank=True, help_text="Hex color code")
    tab_color = models.CharField(max_length=255, blank=True, help_text="Hex color code")

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    class Meta:
        db_table = "item_brand"
        managed = True
        verbose_name = "Item Brand"
        verbose_name_plural = "Item Brands"
        ordering = ["category__name", "type__name", "name"]
        unique_together = ["name", "category", "type"]


class ItemModel(Basemodel):
    """Models of items that can be transported"""

    name = models.CharField(max_length=100)
    brand = models.ForeignKey(
        ItemBrand,
        on_delete=models.CASCADE,
        related_name="models",
        help_text="Brand this model belongs to",
    )
    description = models.TextField(blank=True)
    # Visual properties for frontend
    icon = models.CharField(
        max_length=100, blank=True, help_text="FontAwesome icon name"
    )
    image = models.URLField(blank=True, help_text="URL to model image")
    color = models.CharField(max_length=255, blank=True, help_text="Hex color code")
    tab_color = models.CharField(max_length=255, blank=True, help_text="Hex color code")

    def __str__(self):
        return f"{self.name} ({self.brand.name})"

    class Meta:
        db_table = "item_model"
        managed = True
        verbose_name = "Item Model"
        verbose_name_plural = "Item Models"
        ordering = ["brand__category__name", "brand__name", "name"]
        unique_together = ["name", "brand"]


class CommonItem(Basemodel):
    """Common items that can be selected for pickup points"""

    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Category this item belongs to",
    )
    type = models.ForeignKey(
        ItemType,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Type this item belongs to",
        null=True,
        blank=True,
    )
    brand = models.ForeignKey(
        ItemBrand,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Brand this item belongs to",
        null=True,
        blank=True,
    )
    model = models.ForeignKey(
        ItemModel,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Model this item belongs to",
        null=True,
        blank=True,
    )

    # Basic information
    description = models.TextField(blank=True)

    # Physical properties
    weight = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, help_text="Weight in kg"
    )
    dimensions = models.JSONField(
        null=True, blank=True, help_text="Dimensions as JSON object"
    )

    # Special handling flags
    fragile = models.BooleanField(
        default=False, help_text="Item is fragile and needs special handling"
    )
    needs_disassembly = models.BooleanField(
        default=False, help_text="Item needs to be disassembled for transport"
    )

    # Additional identification fields
    model_number = models.CharField(
        max_length=100, blank=True, help_text="Model number"
    )
    serial_number = models.CharField(
        max_length=100, blank=True, help_text="Serial number"
    )
    year = models.IntegerField(null=True, blank=True, help_text="Year of manufacture")
    model_year = models.IntegerField(null=True, blank=True, help_text="Model year")

    # Visual properties for frontend
    icon = models.CharField(
        max_length=100, blank=True, help_text="FontAwesome icon name"
    )
    image = models.URLField(blank=True, help_text="URL to item image")
    color = models.CharField(max_length=255, blank=True, help_text="Hex color code")
    tab_color = models.CharField(max_length=255, blank=True, help_text="Hex color code")

    # Service relationship
    service_category = models.ForeignKey(
        "Services.ServiceCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Service category for this category of items",
    )

    def __str__(self):
        brand_name = self.brand.name if self.brand else ""
        model_name = self.model.name if self.model else ""
        return f"{self.name} ({brand_name} {model_name})"

    class Meta:
        db_table = "common_item"
        managed = True
        verbose_name = "Common Item"
        verbose_name_plural = "Common Items"
        ordering = [
            "category__name",
            "type__name",
            "brand__name",
            "model__name",
            "name",
        ]
        unique_together = ["name", "category", "type", "brand", "model"]

    @property
    def full_name(self):
        """Returns the full name including type, brand and model"""
        type_name = self.type.name if self.type else ""
        brand_name = self.brand.name if self.brand else ""
        model_name = self.model.name if self.model else ""
        return f"{self.name} ({type_name} {brand_name} {model_name})"

    @property
    def category_name(self):
        """Returns the category name"""
        return self.category.name if self.category else ""

    @property
    def type_name(self):
        """Returns the type name"""
        return self.type.name if self.type else ""

    @property
    def brand_name(self):
        """Returns the brand name"""
        return self.brand.name if self.brand else ""

    @property
    def model_name(self):
        """Returns the model name"""
        return self.model.name if self.model else ""

    def get_dimensions_display(self):
        """Returns formatted dimensions string"""
        if not self.dimensions:
            return ""
        try:
            dims = self.dimensions
            if isinstance(dims, dict):
                parts = []
                if dims.get("length"):
                    parts.append(f"L: {dims['length']}")
                if dims.get("width"):
                    parts.append(f"W: {dims['width']}")
                if dims.get("height"):
                    parts.append(f"H: {dims['height']}")
                return " × ".join(parts) if parts else ""
            return str(dims)
        except:
            return str(self.dimensions)

    def get_weight_display(self):
        """Returns formatted weight string"""
        if self.weight:
            return f"{self.weight} kg"
        return ""

    def get_fragile_display(self):
        """Returns formatted fragile status"""
        return "Yes" if self.fragile else "No"

    def get_disassembly_display(self):
        """Returns formatted disassembly status"""
        return "Yes" if self.needs_disassembly else "No"


class VehicleSize(Basemodel):
    """Class for Vehicle sizes SWB up to 2.4M"""

    name = models.CharField(max_length=200, null=False, blank=False)
    description = models.CharField(max_length=200, null=True, blank=False)
    max_length = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum length in meters",
    )

    # Visual properties for frontend
    icon = models.CharField(
        max_length=100, blank=True, help_text="FontAwesome icon name"
    )
    color = models.CharField(max_length=255, blank=True, help_text="Hex color code")
    tab_color = models.CharField(
        max_length=255, blank=True, help_text="Hex color code for tabs"
    )
    priority = models.IntegerField(default=0, help_text="Display priority order")

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "vehicle_size"
        managed = True
        verbose_name = "Vehicle Size"
        verbose_name_plural = "Vehicle Sizes"
        ordering = ["name"]


class VehicleType(Basemodel):
    """The model for vehicle type eg, goods vehicle and vehicle transporter"""

    name = models.CharField(max_length=200, help_text="Name of the vehicle type")
    description = models.CharField(
        max_length=250, help_text="The description for the vehicle type"
    )

    # Visual properties for frontend
    icon = models.CharField(
        max_length=100, blank=True, help_text="FontAwesome icon name"
    )
    color = models.CharField(max_length=255, blank=True, help_text="Hex color code")
    tab_color = models.CharField(
        max_length=255, blank=True, help_text="Hex color code for tabs"
    )
    priority = models.IntegerField(default=0, help_text="Display priority order")

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "vehicle_type"
        managed = True
        verbose_name = "Vehicle Type"
        verbose_name_plural = "Vehicle Types"
        ordering = ["name"]


class VehicleCategory(Basemodel):
    """Categories of vehicles that can be used for transportation"""

    name = models.CharField(max_length=100, help_text="Name of the vehicle category")
    description = models.TextField(
        blank=True, help_text="Description of the vehicle category"
    )

    # Visual properties for frontend
    icon = models.CharField(
        max_length=100, blank=True, help_text="FontAwesome icon name"
    )
    image = models.URLField(blank=True, help_text="URL to category image")
    color = models.CharField(max_length=255, blank=True, help_text="Hex color code")
    tab_color = models.CharField(
        max_length=255, blank=True, help_text="Hex color code for tabs"
    )
    type = models.ForeignKey(
        VehicleType, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Operational settings
    priority = models.IntegerField(default=0, help_text="Display priority order")
    is_active = models.BooleanField(
        default=True,
        blank=False,
        null=False,
        help_text="Category is active and available",
    )

    vehicle_size = models.ForeignKey(
        VehicleSize, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "vehicle_category"
        managed = True
        verbose_name = "Vehicle Category"
        verbose_name_plural = "Vehicle Categories"
        ordering = ["name"]
