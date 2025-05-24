from rest_framework import serializers
from datetime import datetime, timedelta
from .models import (
    DistancePricing,
    WeightPricing,
    TimePricing,
    WeatherPricing,
    VehicleTypePricing,
    SpecialRequirementsPricing,
    LocationPricing,
    PricingConfiguration,
    ServiceLevelPricing,
    StaffRequiredPricing,
    PropertyTypePricing,
    InsurancePricing,
    LoadingTimePricing,
)


class DistancePricingSerializer(serializers.ModelSerializer):
    # Explicitly define fields that should be numeric
    base_rate_per_km = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False
    )
    base_rate_per_mile = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False
    )
    additional_distance_multiplier = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False
    )

    class Meta:
        model = DistancePricing
        fields = "__all__"


class WeightPricingSerializer(serializers.ModelSerializer):
    # Convert numeric fields to proper format
    base_rate_per_kg = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False
    )
    base_rate_per_lb = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False, required=False
    )
    volume_to_weight_ratio = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False, required=False
    )
    heavy_item_threshold = serializers.IntegerField(required=False)
    heavy_item_surcharge = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False, required=False
    )
    min_weight = serializers.IntegerField()
    max_weight = serializers.IntegerField()

    class Meta:
        model = WeightPricing
        fields = "__all__"


class TimePricingSerializer(serializers.ModelSerializer):
    # Convert numeric fields to proper format
    peak_hour_multiplier = serializers.DecimalField(
        max_digits=5, decimal_places=2, coerce_to_string=False
    )
    weekend_multiplier = serializers.DecimalField(
        max_digits=5, decimal_places=2, coerce_to_string=False
    )
    holiday_multiplier = serializers.DecimalField(
        max_digits=5, decimal_places=2, coerce_to_string=False
    )

    class Meta:
        model = TimePricing
        fields = "__all__"


class WeatherPricingSerializer(serializers.ModelSerializer):
    # Convert numeric fields to proper format
    rain_multiplier = serializers.DecimalField(
        max_digits=5, decimal_places=2, coerce_to_string=False
    )
    snow_multiplier = serializers.DecimalField(
        max_digits=5, decimal_places=2, coerce_to_string=False
    )
    extreme_weather_multiplier = serializers.DecimalField(
        max_digits=5, decimal_places=2, coerce_to_string=False
    )

    class Meta:
        model = WeatherPricing
        fields = "__all__"


class VehicleTypePricingSerializer(serializers.ModelSerializer):
    # Convert numeric fields to proper format
    base_rate = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False
    )
    capacity_multiplier = serializers.DecimalField(
        max_digits=5, decimal_places=2, coerce_to_string=False
    )
    capacity_cubic_meters = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False, required=False
    )
    capacity_weight_kg = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False, required=False
    )
    fuel_efficiency_km_per_liter = serializers.DecimalField(
        max_digits=5, decimal_places=2, coerce_to_string=False, required=False
    )
    hourly_rate = serializers.DecimalField(
        max_digits=8, decimal_places=2, coerce_to_string=False, required=False
    )
    daily_rate = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False, required=False
    )

    class Meta:
        model = VehicleTypePricing
        fields = "__all__"


class SpecialRequirementsPricingSerializer(serializers.ModelSerializer):
    # Convert numeric fields to proper format
    fragile_items_multiplier = serializers.DecimalField(
        max_digits=5, decimal_places=2, coerce_to_string=False
    )
    assembly_required_rate = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False
    )
    special_equipment_rate = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False
    )

    class Meta:
        model = SpecialRequirementsPricing
        fields = "__all__"


class LocationPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationPricing
        fields = "__all__"


class PricingConfigurationSerializer(serializers.ModelSerializer):
    active_factors = serializers.JSONField(required=False)

    class Meta:
        model = PricingConfiguration
        fields = "__all__"

    def create(self, validated_data):
        # Extract active factors data
        active_factors_data = validated_data.pop("active_factors", {})

        # Create the main configuration object
        config = PricingConfiguration.objects.create(**validated_data)

        # Process the active factors and create relationships
        self._process_active_factors(config, active_factors_data)

        return config

    def update(self, instance, validated_data):
        # Extract active factors data
        active_factors_data = validated_data.pop("active_factors", None)

        # Update the main configuration fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Process the active factors if provided
        if active_factors_data is not None:
            self._process_active_factors(instance, active_factors_data)

        return instance

    def _process_active_factors(self, config, active_factors_data):
        """Process active factors and create relationships"""
        factor_models = {
            "distance": (DistancePricing, ConfigDistanceFactor),
            "weight": (WeightPricing, ConfigWeightFactor),
            "time": (TimePricing, ConfigTimeFactor),
            "weather": (WeatherPricing, ConfigWeatherFactor),
            "vehicle_type": (VehicleTypePricing, ConfigVehicleFactor),
            "special_requirements": (
                SpecialRequirementsPricing,
                ConfigSpecialRequirementsFactor,
            ),
            "location": (LocationPricing, ConfigLocationFactor),
            "service_level": (ServiceLevelPricing, ConfigServiceLevelFactor),
            "staff_required": (StaffRequiredPricing, ConfigStaffFactor),
            "property_type": (PropertyTypePricing, ConfigPropertyTypeFactor),
            "insurance": (InsurancePricing, ConfigInsuranceFactor),
            "loading_time": (LoadingTimePricing, ConfigLoadingTimeFactor),
        }

        for factor_type, factor_ids in active_factors_data.items():
            if factor_type in factor_models and factor_ids:
                model_class, through_class = factor_models[factor_type]

                # Clear existing relationships for this factor type
                through_class.objects.filter(configuration=config).delete()

                # Create new relationships with priority based on order
                for priority, factor_id in enumerate(factor_ids):
                    try:
                        factor = model_class.objects.get(id=factor_id)
                        through_class.objects.create(
                            configuration=config,
                            factor=factor,
                            priority=priority + 1,  # Start from 1
                            weight=1.0,  # Default weight
                        )
                    except model_class.DoesNotExist:
                        # Log error or handle invalid factor ID
                        pass


class ServiceLevelPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceLevelPricing
        fields = "__all__"


class StaffRequiredPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffRequiredPricing
        fields = "__all__"


class PropertyTypePricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyTypePricing
        fields = "__all__"


class InsurancePricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsurancePricing
        fields = "__all__"


class LoadingTimePricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoadingTimePricing
        fields = "__all__"


class PriceCalculationSerializer(serializers.Serializer):
    distance = serializers.FloatField(required=False, default=0)
    weight = serializers.FloatField(required=False, default=0)
    service_level = serializers.ChoiceField(
        choices=["standard", "express", "premium"], required=False, default="standard"
    )
    staff_required = serializers.IntegerField(required=False, min_value=1, default=1)
    property_type = serializers.ChoiceField(
        choices=["house", "apartment", "office", "storage", "other"], required=False
    )
    number_of_rooms = serializers.IntegerField(required=False, min_value=1)
    floor_number = serializers.IntegerField(required=False, min_value=0)
    has_elevator = serializers.BooleanField(required=False, default=True)
    has_fragile_items = serializers.BooleanField(required=False, default=False)
    requires_assembly = serializers.BooleanField(required=False, default=False)
    requires_special_equipment = serializers.BooleanField(required=False, default=False)
    insurance_required = serializers.BooleanField(required=False, default=False)
    insurance_value = serializers.DecimalField(
        required=False, max_digits=10, decimal_places=2, min_value=0
    )
    pickup_city = serializers.CharField(required=False, allow_null=True)
    dropoff_city = serializers.CharField(required=False, allow_null=True)
    carbon_offset = serializers.BooleanField(required=False, default=False)
    is_peak_hour = serializers.BooleanField(required=False, default=False)
    is_weekend = serializers.BooleanField(required=False, default=False)
    is_holiday = serializers.BooleanField(required=False, default=False)
    loading_time = serializers.DurationField(required=False, allow_null=True)
    unloading_time = serializers.DurationField(required=False, allow_null=True)
    weather_condition = serializers.ChoiceField(
        choices=["normal", "rain", "snow", "extreme"], required=False, default="normal"
    )


class DateBasedPriceCalculationSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    distance = serializers.FloatField(required=False, default=0)
    weight = serializers.FloatField(required=False, default=0)
    service_level = serializers.ChoiceField(
        choices=["standard", "express", "premium"], required=False, default="standard"
    )
    loading_time = serializers.DurationField(required=False, allow_null=True)
    unloading_time = serializers.DurationField(required=False, allow_null=True)
    vehicle_type = serializers.CharField(required=False)
    property_type = serializers.ChoiceField(
        choices=["house", "apartment", "office", "storage", "other"], required=False
    )
    number_of_rooms = serializers.IntegerField(required=False, min_value=1)
    floor_number = serializers.IntegerField(required=False, min_value=0)
    has_elevator = serializers.BooleanField(required=False, default=True)
    has_fragile_items = serializers.BooleanField(required=False, default=False)
    requires_assembly = serializers.BooleanField(required=False, default=False)
    requires_special_equipment = serializers.BooleanField(required=False, default=False)
    insurance_required = serializers.BooleanField(required=False, default=False)
    insurance_value = serializers.DecimalField(
        required=False, max_digits=10, decimal_places=2, min_value=0
    )
    pickup_city = serializers.CharField(required=False, allow_null=True)
    dropoff_city = serializers.CharField(required=False, allow_null=True)
    carbon_offset = serializers.BooleanField(required=False, default=False)
    request_id = serializers.UUIDField(required=True)

    def validate(self, data):
        # Check if both dates are present before comparing
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date is None:
            raise serializers.ValidationError("Start date is required")

        if end_date is None:
            raise serializers.ValidationError("End date is required")

        if start_date > end_date:
            raise serializers.ValidationError("End date must be after start date")

        if (end_date - start_date).days > 90:
            raise serializers.ValidationError("Date range cannot exceed 90 days")

        return data
