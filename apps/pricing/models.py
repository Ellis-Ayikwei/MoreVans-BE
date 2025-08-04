from django.db import models  # Importing models from Django
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)  # Importing validators for field constraints
from django.utils import timezone  # Importing timezone utilities from Django
from rest_framework.views import APIView  # Importing APIView from DRF
from rest_framework.response import Response  # Importing Response from DRF
from rest_framework import permissions  # Importing permissions from DRF
from rest_framework.decorators import action

from apps.Basemodel.models import Basemodel


class PricingFactor(Basemodel):  # Defining abstract base class for pricing factors
    """Base model for pricing factors that can be enabled/disabled by admin"""

    name = models.CharField(max_length=100)  # Name of the pricing factor
    description = models.TextField()  # Description of the pricing factor
    is_active = models.BooleanField(
        default=True
    )  # Whether the pricing factor is active

    class Meta:  # Meta class for additional options
        abstract = True  # Marks this model as abstract


class DistancePricing(PricingFactor):  # Model for distance-based pricing
    """Pricing based on distance"""

    base_rate_per_km = models.DecimalField(  # Base rate per kilometer
        max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    min_distance = models.IntegerField(default=0)  # Minimum distance for pricing
    max_distance = models.IntegerField(default=1000)  # Maximum distance for pricing
    base_rate_per_mile = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
        help_text="Optional: For regions using miles instead of km",
    )
    additional_distance_threshold = models.IntegerField(
        default=50, help_text="Distance threshold after which higher rates apply"
    )
    additional_distance_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.2,
        validators=[MinValueValidator(1.00)],
        help_text="Multiplier for distances beyond the threshold",
    )

    class Meta:
        db_table = "pricing_distance"

    def calculate_price(
        self, distance_km
    ):  # Method to calculate price based on distance
        if not self.is_active:  # If pricing factor is inactive
            return 0  # Return price as 0
        return float(self.base_rate_per_km) * max(  # Calculate price
            0, min(distance_km, self.max_distance)
        )


class WeightPricing(PricingFactor):  # Model for weight-based pricing
    """Pricing based on weight"""

    base_rate_per_kg = models.DecimalField(  # Base rate per kilogram
        max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    min_weight = models.IntegerField(default=0)  # Minimum weight for pricing
    max_weight = models.IntegerField(default=10000)  # Maximum weight for pricing
    base_rate_per_lb = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
        help_text="Optional: For regions using pounds instead of kg",
    )
    volume_to_weight_ratio = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=167.00,
        validators=[MinValueValidator(0.01)],
        help_text="Cubic cm to kg conversion ratio (volumetric weight)",
    )
    heavy_item_threshold = models.IntegerField(
        default=50, help_text="Weight threshold for items considered heavy"
    )
    heavy_item_surcharge = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=25.00,
        validators=[MinValueValidator(0.00)],
    )

    class Meta:
        db_table = "pricing_weight"

    def calculate_price(self, weight_kg):  # Method to calculate price based on weight
        if not self.is_active:  # If pricing factor is inactive
            return 0  # Return price as 0
        return float(self.base_rate_per_kg) * max(
            0, min(weight_kg, self.max_weight)
        )  # Calculate price


class TimePricing(PricingFactor):  # Model for time-based pricing
    """Pricing based on time factors (peak hours, weekends, etc.)"""

    peak_hour_multiplier = models.DecimalField(  # Multiplier for peak hours
        max_digits=3, decimal_places=2, default=1.5, validators=[MinValueValidator(1.0)]
    )
    weekend_multiplier = models.DecimalField(  # Multiplier for weekends
        max_digits=3, decimal_places=2, default=1.3, validators=[MinValueValidator(1.0)]
    )
    holiday_multiplier = models.DecimalField(  # Multiplier for holidays
        max_digits=3, decimal_places=2, default=2.0, validators=[MinValueValidator(1.0)]
    )

    class Meta:
        db_table = "pricing_time"


class WeatherPricing(PricingFactor):  # Model for weather-based pricing
    """Pricing adjustments based on weather conditions"""

    rain_multiplier = models.DecimalField(  # Multiplier for rain conditions
        max_digits=3, decimal_places=2, default=1.2, validators=[MinValueValidator(1.0)]
    )
    snow_multiplier = models.DecimalField(  # Multiplier for snow conditions
        max_digits=3, decimal_places=2, default=1.5, validators=[MinValueValidator(1.0)]
    )
    extreme_weather_multiplier = models.DecimalField(  # Multiplier for extreme weather
        max_digits=3, decimal_places=2, default=2.0, validators=[MinValueValidator(1.0)]
    )

    class Meta:
        db_table = "pricing_weather"


class VehicleTypePricing(PricingFactor):  # Model for vehicle type-based pricing
    """Pricing based on vehicle type"""

    vehicle_type = models.CharField(max_length=50)  # Type of vehicle
    base_rate = models.DecimalField(  # Base rate for vehicle type
        max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    capacity_multiplier = models.DecimalField(  # Multiplier based on vehicle capacity
        max_digits=3, decimal_places=2, default=1.0, validators=[MinValueValidator(1.0)]
    )
    capacity_cubic_meters = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
    )
    capacity_weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
    )
    fuel_efficiency_km_per_liter = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=8.00,
        validators=[MinValueValidator(0.01)],
    )
    hourly_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
    )
    daily_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
    )

    class Meta:
        db_table = "pricing_vehicle_type"


class SpecialRequirementsPricing(
    PricingFactor
):  # Model for special requirements pricing
    """Pricing for special handling requirements"""

    fragile_items_multiplier = models.DecimalField(  # Multiplier for fragile items
        max_digits=3, decimal_places=2, default=1.3, validators=[MinValueValidator(1.0)]
    )
    assembly_required_rate = models.DecimalField(  # Rate for assembly required
        max_digits=6,
        decimal_places=2,
        default=50.00,
        validators=[MinValueValidator(0.01)],
    )
    special_equipment_rate = models.DecimalField(  # Rate for special equipment
        max_digits=6,
        decimal_places=2,
        default=75.00,
        validators=[MinValueValidator(0.01)],
    )

    class Meta:
        db_table = "pricing_special_requirements"


class LocationPricing(PricingFactor):  # Model for location-based pricing
    """Pricing adjustments based on location characteristics"""

    city_name = models.CharField(max_length=100)  # Name of the city
    zone_multiplier = models.DecimalField(  # Multiplier based on zone
        max_digits=3,
        decimal_places=2,
        default=1.0,
        validators=[MinValueValidator(0.8), MaxValueValidator(3.0)],
    )
    congestion_charge = models.DecimalField(  # Charge for congestion
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
    )
    parking_fee = models.DecimalField(  # Fee for parking
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
    )

    class Meta:
        db_table = "pricing_location"


class ServiceLevelPricing(PricingFactor):  # Model for service level-based pricing
    """Pricing based on service level (standard, express, same_day, scheduled)"""

    SERVICE_LEVEL_CHOICES = [  # Choices for service levels
        ("standard", "Standard (2-3 business days)"),
        ("express", "Express (1-2 business days)"),
        ("same_day", "Same Day Delivery"),
        ("scheduled", "Scheduled (Flexible Date)"),
    ]
    service_level = models.CharField(
        max_length=20, choices=SERVICE_LEVEL_CHOICES
    )  # Service level choice
    price_multiplier = models.DecimalField(  # Multiplier for service level
        max_digits=3, decimal_places=2, default=1.0, validators=[MinValueValidator(0.5)]
    )

    class Meta:
        db_table = "pricing_service_level"


class StaffRequiredPricing(PricingFactor):  # Model for staff-based pricing
    """Pricing based on number of staff required"""

    base_rate_per_staff = models.DecimalField(  # Base rate per staff member
        max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    min_staff = models.IntegerField(default=1)  # Minimum number of staff
    max_staff = models.IntegerField(default=10)  # Maximum number of staff
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=25.00,
        validators=[MinValueValidator(0.01)],
    )
    overtime_rate_multiplier = models.DecimalField(
        max_digits=3, decimal_places=2, default=1.5, validators=[MinValueValidator(1.0)]
    )
    specialist_staff_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.5,
        validators=[MinValueValidator(1.0)],
        help_text="Multiplier for specialized staff (piano movers, art handlers, etc.)",
    )

    class Meta:
        db_table = "pricing_staff_required"


class PropertyTypePricing(PricingFactor):  # Model for property type-based pricing
    """Pricing based on property type and number of rooms"""

    PROPERTY_TYPE_CHOICES = [  # Choices for property types
        ("house", "House"),
        ("apartment", "Apartment"),
        ("office", "Office"),
        ("storage", "Storage"),
        ("other", "Other"),
    ]
    property_type = models.CharField(
        max_length=20, choices=PROPERTY_TYPE_CHOICES
    )  # Property type choice
    base_rate = models.DecimalField(  # Base rate for property type
        max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    rate_per_room = models.DecimalField(  # Rate per room
        max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    elevator_discount = models.DecimalField(  # Discount for elevator usage
        max_digits=3,
        decimal_places=2,
        default=0.90,
        validators=[MinValueValidator(0.50), MaxValueValidator(1.00)],
    )
    floor_rate = models.DecimalField(  # Rate per floor
        max_digits=6,
        decimal_places=2,
        default=10.00,
        validators=[MinValueValidator(0.01)],
    )
    narrow_access_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=25.00,
        validators=[MinValueValidator(0.00)],
    )
    stairs_per_flight_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=15.00,
        validators=[MinValueValidator(0.00)],
    )
    rate_per_sq_meter = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=2.00,
        validators=[MinValueValidator(0.01)],
    )
    long_carry_distance_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=30.00,
        validators=[MinValueValidator(0.00)],
        help_text="Fee for carrying items long distances from parking",
    )

    class Meta:
        db_table = "pricing_property_type"


class InsurancePricing(PricingFactor):  # Model for insurance-based pricing
    """Pricing for insurance coverage"""

    base_rate = models.DecimalField(  # Base rate for insurance
        max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    value_percentage = models.DecimalField(  # Percentage value for insurance
        max_digits=4,
        decimal_places=2,
        default=0.50,
        validators=[MinValueValidator(0.01), MaxValueValidator(5.00)],
    )
    min_premium = models.DecimalField(  # Minimum premium for insurance
        max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    premium_coverage_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=2.00,
        validators=[MinValueValidator(1.00)],
        help_text="Multiplier for premium coverage options",
    )
    high_value_item_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1000.00,
        validators=[MinValueValidator(0.00)],
        help_text="Value threshold for items considered high value",
    )
    high_value_item_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.00,
        validators=[MinValueValidator(0.01)],
        help_text="Percentage rate for high value items",
    )
    deductible_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=100.00,
        validators=[MinValueValidator(0.00)],
    )

    class Meta:
        db_table = "pricing_insurance"


class LoadingTimePricing(PricingFactor):  # Model for loading time-based pricing
    """Pricing based on loading/unloading time"""

    base_rate_per_hour = models.DecimalField(  # Base rate per hour
        max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    min_hours = models.DecimalField(  # Minimum hours for loading
        max_digits=4,
        decimal_places=2,
        default=1.00,
        validators=[MinValueValidator(0.50)],
    )
    overtime_multiplier = models.DecimalField(  # Multiplier for overtime
        max_digits=3,
        decimal_places=2,
        default=1.50,
        validators=[MinValueValidator(1.00)],
    )

    class Meta:
        db_table = "pricing_loading_time"


# Config Factors


class ConfigFactorBase(Basemodel):
    """Base model for configuration-factor relationships"""

    priority = models.PositiveIntegerField(default=1)
    weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects: models.Manager = models.Manager()

    class Meta:
        abstract = True
        ordering = ["priority"]


class ConfigDistanceFactor(ConfigFactorBase):
    """Relationship between configuration and distance factors"""

    configuration = models.ForeignKey("PricingConfiguration", on_delete=models.CASCADE)
    factor = models.ForeignKey(DistancePricing, on_delete=models.CASCADE)

    class Meta(ConfigFactorBase.Meta):
        unique_together = ["configuration", "factor"]
        db_table = "pricing_config_distance_factor"


class ConfigWeightFactor(ConfigFactorBase):
    """Relationship between configuration and weight factors"""

    configuration = models.ForeignKey("PricingConfiguration", on_delete=models.CASCADE)
    factor = models.ForeignKey(WeightPricing, on_delete=models.CASCADE)

    class Meta(ConfigFactorBase.Meta):
        unique_together = ["configuration", "factor"]
        db_table = "pricing_config_weight_factor"


class ConfigTimeFactor(ConfigFactorBase):
    """Relationship between configuration and time factors"""

    configuration = models.ForeignKey("PricingConfiguration", on_delete=models.CASCADE)
    factor = models.ForeignKey(TimePricing, on_delete=models.CASCADE)

    class Meta(ConfigFactorBase.Meta):
        unique_together = ["configuration", "factor"]
        db_table = "pricing_config_time_factor"


class ConfigWeatherFactor(ConfigFactorBase):
    """Relationship between configuration and weather factors"""

    configuration = models.ForeignKey("PricingConfiguration", on_delete=models.CASCADE)
    factor = models.ForeignKey(WeatherPricing, on_delete=models.CASCADE)

    class Meta(ConfigFactorBase.Meta):
        unique_together = ["configuration", "factor"]
        db_table = "pricing_config_weather_factor"


class ConfigVehicleFactor(ConfigFactorBase):
    """Relationship between configuration and vehicle factors"""

    configuration = models.ForeignKey("PricingConfiguration", on_delete=models.CASCADE)
    factor = models.ForeignKey(VehicleTypePricing, on_delete=models.CASCADE)

    class Meta(ConfigFactorBase.Meta):
        unique_together = ["configuration", "factor"]
        db_table = "pricing_config_vehicle_factor"


class ConfigSpecialRequirementsFactor(ConfigFactorBase):
    """Relationship between configuration and special requirements factors"""

    configuration = models.ForeignKey("PricingConfiguration", on_delete=models.CASCADE)
    factor = models.ForeignKey(SpecialRequirementsPricing, on_delete=models.CASCADE)

    class Meta(ConfigFactorBase.Meta):
        unique_together = ["configuration", "factor"]
        db_table = "pricing_config_special_requirements_factor"


class ConfigLocationFactor(ConfigFactorBase):
    """Relationship between configuration and location factors"""

    configuration = models.ForeignKey("PricingConfiguration", on_delete=models.CASCADE)
    factor = models.ForeignKey(LocationPricing, on_delete=models.CASCADE)

    class Meta(ConfigFactorBase.Meta):
        unique_together = ["configuration", "factor"]
        db_table = "pricing_config_location_factor"


class ConfigServiceLevelFactor(ConfigFactorBase):
    """Relationship between configuration and service level factors"""

    configuration = models.ForeignKey("PricingConfiguration", on_delete=models.CASCADE)
    factor = models.ForeignKey(ServiceLevelPricing, on_delete=models.CASCADE)

    class Meta(ConfigFactorBase.Meta):
        unique_together = ["configuration", "factor"]
        db_table = "pricing_config_service_level_factor"


class ConfigStaffFactor(ConfigFactorBase):
    """Relationship between configuration and staff factors"""

    configuration = models.ForeignKey("PricingConfiguration", on_delete=models.CASCADE)
    factor = models.ForeignKey(StaffRequiredPricing, on_delete=models.CASCADE)

    class Meta(ConfigFactorBase.Meta):
        unique_together = ["configuration", "factor"]
        db_table = "pricing_config_staff_factor"


class ConfigPropertyTypeFactor(ConfigFactorBase):
    """Relationship between configuration and property type factors"""

    configuration = models.ForeignKey("PricingConfiguration", on_delete=models.CASCADE)
    factor = models.ForeignKey(PropertyTypePricing, on_delete=models.CASCADE)

    class Meta(ConfigFactorBase.Meta):
        unique_together = ["configuration", "factor"]
        db_table = "pricing_config_property_type_factor"


class ConfigInsuranceFactor(ConfigFactorBase):
    """Relationship between configuration and insurance factors"""

    configuration = models.ForeignKey("PricingConfiguration", on_delete=models.CASCADE)
    factor = models.ForeignKey(InsurancePricing, on_delete=models.CASCADE)

    class Meta(ConfigFactorBase.Meta):
        unique_together = ["configuration", "factor"]
        db_table = "pricing_config_insurance_factor"


class ConfigLoadingTimeFactor(ConfigFactorBase):
    """Relationship between configuration and loading time factors"""

    configuration = models.ForeignKey("PricingConfiguration", on_delete=models.CASCADE)
    factor = models.ForeignKey(LoadingTimePricing, on_delete=models.CASCADE)

    class Meta(ConfigFactorBase.Meta):
        unique_together = ["configuration", "factor"]
        db_table = "pricing_config_loading_time_factor"


class PricingConfiguration(Basemodel):
    """Master configuration for the pricing system"""

    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    # Keep essential base rates
    base_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=50.00,
        validators=[MinValueValidator(0.01)],
    )
    min_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=30.00,
        validators=[MinValueValidator(0.01)],
    )
    max_price_multiplier = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Maximum multiplier for the base price",
    )
    fuel_surcharge_percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)],
        help_text="Fuel surcharge as percentage of total price",
    )
    carbon_offset_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
        help_text="Carbon offset rate as percentage of total price",
    )
    platform_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)],
        help_text="Platform fee as percentage of customer price",
    )

    # Add factor relationships
    distance_factors = models.ManyToManyField(
        DistancePricing,
        through=ConfigDistanceFactor,
        related_name="configurations",
        blank=True,
    )
    weight_factors = models.ManyToManyField(
        WeightPricing,
        through=ConfigWeightFactor,
        related_name="configurations",
        blank=True,
    )
    time_factors = models.ManyToManyField(
        TimePricing, through=ConfigTimeFactor, related_name="configurations", blank=True
    )
    weather_factors = models.ManyToManyField(
        WeatherPricing,
        through=ConfigWeatherFactor,
        related_name="configurations",
        blank=True,
    )
    vehicle_factors = models.ManyToManyField(
        VehicleTypePricing,
        through=ConfigVehicleFactor,
        related_name="configurations",
        blank=True,
    )
    special_requirement_factors = models.ManyToManyField(
        SpecialRequirementsPricing,
        through=ConfigSpecialRequirementsFactor,
        related_name="configurations",
        blank=True,
    )
    location_factors = models.ManyToManyField(
        LocationPricing,
        through=ConfigLocationFactor,
        related_name="configurations",
        blank=True,
    )
    service_level_factors = models.ManyToManyField(
        ServiceLevelPricing,
        through=ConfigServiceLevelFactor,
        related_name="configurations",
        blank=True,
    )
    staff_factors = models.ManyToManyField(
        StaffRequiredPricing,
        through=ConfigStaffFactor,
        related_name="configurations",
        blank=True,
    )
    property_type_factors = models.ManyToManyField(
        PropertyTypePricing,
        through=ConfigPropertyTypeFactor,
        related_name="configurations",
        blank=True,
    )
    insurance_factors = models.ManyToManyField(
        InsurancePricing,
        through=ConfigInsuranceFactor,
        related_name="configurations",
        blank=True,
    )
    loading_time_factors = models.ManyToManyField(
        LoadingTimePricing,
        through=ConfigLoadingTimeFactor,
        related_name="configurations",
        blank=True,
    )

    # For backward compatibility, keep the JSON field temporarily
    active_factors = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects: models.Manager = models.Manager()

    class Meta:
        ordering = ["-created_at"]
        managed = True
        db_table = "pricing_configuration"

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"

    def get_active_factors(self, factor_type):
        """Get all active factors of a specific type"""
        relation_name = f"{factor_type}_factors"
        if hasattr(self, relation_name):
            return getattr(self, relation_name).filter(is_active=True)
        return []
