# File: backend/pricing/defaults.py

import uuid
from decimal import Decimal

DEFAULT_PRICING_CONFIG = {
    "name": "Default Pricing Configuration",
    "is_active": True,
    "is_default": True,
    "base_price": Decimal("50.00"),
    "min_price": Decimal("30.00"),
    "max_price_multiplier": Decimal("5.0"),
    "fuel_surcharge_percentage": Decimal("3.0"),
    "carbon_offset_rate": Decimal("1.0"),
}

DEFAULT_DISTANCE_PRICING = {
    "name": "Default Distance Pricing",
    "description": "Standard pricing per kilometer",
    "is_active": True,
    "base_rate_per_km": Decimal("1.20"),
    "base_rate_per_mile": Decimal("1.93"),
    "min_distance": 0,
    "max_distance": 1000,
    "additional_distance_threshold": 50,
    "additional_distance_multiplier": Decimal("1.2"),
}

DEFAULT_WEIGHT_PRICING = {
    "name": "Default Weight Pricing",
    "description": "Standard pricing per kilogram",
    "is_active": True,
    "base_rate_per_kg": Decimal("0.50"),
    "min_weight": 0,
    "max_weight": 10000,
    "heavy_item_threshold": 50,
    "heavy_item_surcharge": Decimal("25.00"),
}

DEFAULT_TIME_PRICING = {
    "name": "Default Time Pricing",
    "description": "Time-based multipliers for peak hours, weekends, and holidays",
    "is_active": True,
    "peak_hour_multiplier": Decimal("1.25"),
    "weekend_multiplier": Decimal("1.50"),
    "holiday_multiplier": Decimal("2.00"),
}

DEFAULT_WEATHER_PRICING = {
    "name": "Default Weather Pricing",
    "description": "Weather condition multipliers",
    "is_active": True,
    "rain_multiplier": Decimal("1.20"),
    "snow_multiplier": Decimal("1.50"),
    "extreme_weather_multiplier": Decimal("2.00"),
}

DEFAULT_VEHICLE_PRICING = {
    "name": "Standard Van",
    "description": "Default van pricing",
    "is_active": True,
    "vehicle_type": "van",
    "base_rate": Decimal("50.00"),
    "capacity_multiplier": Decimal("1.00"),
    "capacity_cubic_meters": Decimal("10.00"),
    "capacity_weight_kg": Decimal("1000.00"),
}

DEFAULT_SPECIAL_REQUIREMENTS_PRICING = {
    "name": "Default Special Requirements Pricing",
    "description": "Pricing for special item handling",
    "is_active": True,
    "fragile_items_multiplier": Decimal("1.30"),
    "assembly_required_rate": Decimal("25.00"),
    "special_equipment_rate": Decimal("35.00"),
}

DEFAULT_SERVICE_LEVEL_PRICING = {
    "name": "Standard Service",
    "description": "Standard service level",
    "is_active": True,
    "service_level": "standard",
    "price_multiplier": Decimal("1.00"),
}

DEFAULT_STAFF_REQUIRED_PRICING = {
    "name": "Standard Staff Pricing",
    "description": "Standard pricing per staff member",
    "is_active": True,
    "base_rate_per_staff": Decimal("25.00"),
    "min_staff": 1,
    "max_staff": 4,
    "hourly_rate": Decimal("25.00"),
    "overtime_rate_multiplier": Decimal("1.50"),
    "specialist_staff_multiplier": Decimal("1.50"),
    "id": uuid.uuid4()
}

DEFAULT_PROPERTY_TYPE_PRICING = {
    "name": "Standard House",
    "description": "Standard house pricing",
    "is_active": True,
    "property_type": "house",
    "base_rate": Decimal("50.00"),
    "rate_per_room": Decimal("10.00"),
    "elevator_discount": Decimal("0.90"),
    "floor_rate": Decimal("15.00"),
}

DEFAULT_INSURANCE_PRICING = {
    "name": "Standard Insurance",
    "description": "Standard insurance coverage",
    "is_active": True,
    "base_rate": Decimal("20.00"),
    "value_percentage": Decimal("0.50"),
    "min_premium": Decimal("20.00"),
}

DEFAULT_LOADING_TIME_PRICING = {
    "name": "Standard Loading Time",
    "description": "Standard pricing for loading/unloading time",
    "is_active": True,
    "base_rate_per_hour": Decimal("30.00"),
    "min_hours": Decimal("1.0"),
    "overtime_multiplier": Decimal("1.50"),
}
