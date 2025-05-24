from datetime import date, datetime, timedelta
import holidays
from rest_framework.response import Response
from rest_framework import status
import logging
from django.core.cache import cache
from django.db.models import Q
from .models import (
    PricingConfiguration,
    DistancePricing,
    WeightPricing,
    TimePricing,
    WeatherPricing,
    VehicleTypePricing,
    SpecialRequirementsPricing,
    ServiceLevelPricing,
    StaffRequiredPricing,
    PropertyTypePricing,
    InsurancePricing,
    LoadingTimePricing,
)
import uuid
from .defaults import (
    DEFAULT_PRICING_CONFIG,
    DEFAULT_DISTANCE_PRICING,
    DEFAULT_WEIGHT_PRICING,
    DEFAULT_TIME_PRICING,
    DEFAULT_WEATHER_PRICING,
    DEFAULT_VEHICLE_PRICING,
    DEFAULT_SPECIAL_REQUIREMENTS_PRICING,
    DEFAULT_SERVICE_LEVEL_PRICING,
    DEFAULT_STAFF_REQUIRED_PRICING,
    DEFAULT_PROPERTY_TYPE_PRICING,
    DEFAULT_INSURANCE_PRICING,
    DEFAULT_LOADING_TIME_PRICING,
)
from decimal import Decimal
import random
from types import SimpleNamespace
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PricingService:
    """Service class to handle pricing logic separated from the views"""

    CACHE_TIMEOUT = 3600  # 1 hour cache timeout
    CACHE_KEY_PREFIX = "pricing_"

    @staticmethod
    def get_cache_key(key):
        """Generate a cache key with prefix"""
        return f"{PricingService.CACHE_KEY_PREFIX}{key}"

    @staticmethod
    def calculate_price_forecast(forecast_request):
        """
        Calculate prices for different dates and staff requirements.
        Returns a calendar-friendly format with staff prices for each day.
        """
        try:
            # Ensure default configuration exists
            PricingService.ensure_default_config_exists()

            # Get request data
            data = (
                forecast_request.data
                if hasattr(forecast_request, "data")
                else forecast_request
            )

            # Get active configuration
            active_config = PricingService.get_active_configuration()
            if not active_config:
                raise ValueError("No active pricing configuration found")

            # Use default base_price if missing
            base_price = float(
                active_config.base_price
                if active_config.base_price is not None
                else DEFAULT_PRICING_CONFIG["base_price"]
            )

            # Get date range
            start_date = data.get("start_date", date.today())
            end_date = data.get("end_date", start_date + timedelta(days=90))

            # Get basic pricing parameters with validation
            distance = float(data.get("distance", random.uniform(5, 50)))
            weight = float(data.get("weight", 0))
            service_level = data.get("service_level", "standard")
            property_type = data.get("property_type", "house")
            vehicle_type = data.get("vehicle_type", "van")
            priority_type = data.get("priority_type", "standard")

            # Validate parameters
            if distance < 0:
                raise ValueError("Distance cannot be negative")
            if weight < 0:
                raise ValueError("Weight cannot be negative")

            # Get configuration factors with caching
            factors = PricingService._get_pricing_factors(
                active_config, service_level, property_type, vehicle_type
            )

            # Initialize result structure
            monthly_calendar = {}
            uk_holidays = holidays.GB()

            # Generate pricing for each day in the range
            current_date = start_date
            while current_date <= end_date:
                month_key = current_date.strftime("%Y-%m")
                if month_key not in monthly_calendar:
                    monthly_calendar[month_key] = []

                # Calculate day's prices
                day_data = PricingService._calculate_day_prices(
                    current_date,
                    distance,
                    weight,
                    data,
                    factors,
                    active_config,
                    uk_holidays,
                    forecast_request,
                )
                monthly_calendar[month_key].append(day_data)
                current_date += timedelta(days=1)

            return Response(
                {
                    "pricing_configuration": active_config.name,
                    "base_parameters": {
                        "distance": distance,
                        "weight": weight,
                        "service_level": service_level,
                        "property_type": property_type,
                        "vehicle_type": vehicle_type,
                        "priority_type": priority_type,
                    },
                    "monthly_calendar": monthly_calendar,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error calculating prices: {str(e)}")
            return Response(
                {"error": "An error occurred while calculating prices"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @staticmethod
    def _calculate_day_prices(
        current_date,
        distance,
        weight,
        data,
        factors,
        active_config,
        uk_holidays,
        forecast_request,
    ):
        """Calculate prices for a specific day"""
        # Check if it's a weekend or holiday using the day name
        day_name = current_date.strftime('%A').lower()  # Get full day name in lowercase
        is_weekend = day_name in ['saturday', 'sunday']
        is_holiday = current_date in uk_holidays

        # Calculate base components
        base_price = float(active_config.base_price)
        distance_cost = PricingService._calculate_distance_cost(
            distance, factors["distance"]
        )
        weight_cost = PricingService._calculate_weight_cost(weight, factors["weight"])
        property_cost = PricingService._calculate_property_cost(
            data, factors["property"]
        )

        # Calculate vehicle cost with dimensions
        vehicle_cost, vehicle_multiplier = PricingService._calculate_vehicle_cost(
            factors["vehicle"],
            data.get('total_dimensions')
        )

        # Calculate insurance cost if applicable
        insurance_cost = PricingService._calculate_insurance_cost(
            data, factors["insurance"]
        )

        # Calculate multipliers
        service_multiplier = PricingService._calculate_service_multiplier(
            factors["service_level"]
        )
        time_multiplier = PricingService._calculate_time_multiplier(
            is_weekend, is_holiday, factors["time"]
        )
        weather_multiplier, weather_type = (
            PricingService._calculate_weather_multiplier(data.get('city'), current_date.strftime('%Y-%m-%d'))
        )

        # Get priority type from data
        priority_type = data.get('priority_type', 'normal')

        # Calculate staff prices
        staff_prices = PricingService._calculate_staff_prices(
            factors["staff"],
            is_weekend,
            is_holiday,
            base_price,
            distance_cost,
            weight_cost,
            property_cost,
            vehicle_cost,
            insurance_cost,
            service_multiplier,
            time_multiplier,
            weather_multiplier,
            vehicle_multiplier,
            active_config,
            priority_type
        )

        # Find the best price and its staff count
        best_price = float('inf')
        best_staff_count = None
        best_value_score = float('inf')  # Lower score is better

        for staff_price in staff_prices:
            price = staff_price['price']
            staff_count = staff_price['staff_count']
            
            # Calculate value score (price per staff member)
            value_score = price / staff_count
            
            # If this is a better value proposition (lower price per staff member)
            # or if it's the same value but lower total price
            if value_score < best_value_score or (value_score == best_value_score and price < best_price):
                best_value_score = value_score
                best_price = price
                best_staff_count = staff_count

        # Prepare day data
        day_data = {
            "date": current_date.strftime("%Y-%m-%d"),
            "day": current_date.day,
            "day_name": current_date.strftime('%A'),  # Add full day name
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "holiday_name": uk_holidays.get(current_date) if is_holiday else None,
            "weather_type": weather_type,
            "staff_prices": staff_prices,
            "status": "available",
            "request_type": data.get('request_type', 'standard'),
            "priority_type": priority_type,
            "best_price": best_price if best_price != float('inf') else None,
            "best_staff_count": best_staff_count
        }

        if hasattr(forecast_request, "request_id"):
            day_data["request_id"] = forecast_request.request_id

        return day_data

    @staticmethod
    def get_active_configuration():
        """Return the DB config or fallback to an in-memory default."""
        config = PricingConfiguration.objects.filter(is_default=True).first()
        if not config:
            config = PricingConfiguration.objects.filter(is_active=True).first()

        if config:
            return config

        # build a fake config from our DEFAULT_… dict
        fake = SimpleNamespace(**DEFAULT_PRICING_CONFIG)
        # attach in-memory lists of mock factors
        fake.distance_factors = [DistancePricing(**DEFAULT_DISTANCE_PRICING)]
        fake.weight_factors = [WeightPricing(**DEFAULT_WEIGHT_PRICING)]
        fake.time_factors = [TimePricing(**DEFAULT_TIME_PRICING)]
        fake.weather_factors = [WeatherPricing(**DEFAULT_WEATHER_PRICING)]
        fake.vehicle_factors = [VehicleTypePricing(**DEFAULT_VEHICLE_PRICING)]
        fake.special_requirement_factors = [
            SpecialRequirementsPricing(**DEFAULT_SPECIAL_REQUIREMENTS_PRICING)
        ]
        fake.service_level_factors = [
            ServiceLevelPricing(**DEFAULT_SERVICE_LEVEL_PRICING)
        ]
        fake.staff_factors = [StaffRequiredPricing(**DEFAULT_STAFF_REQUIRED_PRICING)]
        fake.property_type_factors = [
            PropertyTypePricing(**DEFAULT_PROPERTY_TYPE_PRICING)
        ]
        fake.insurance_factors = [InsurancePricing(**DEFAULT_INSURANCE_PRICING)]
        fake.loading_time_factors = [LoadingTimePricing(**DEFAULT_LOADING_TIME_PRICING)]
        return fake

    @staticmethod
    def ensure_default_config_exists():
        """
        Ensures that at least one default pricing configuration exists in the database.
        If no configuration exists, creates a default one with standard pricing factors.
        """
        # Check if any pricing configuration exists
        if PricingConfiguration.objects.count() == 0:
            logger.info(
                "No pricing configuration found. Creating default configuration..."
            )

            try:
                # Create default configuration
                config = PricingConfiguration.objects.create(**DEFAULT_PRICING_CONFIG)
                logger.info(
                    f"Created default pricing configuration: {config.name} (ID: {config.id})"
                )

                # Create all default factors
                factors = {
                    "distance": DistancePricing.objects.create(
                        **DEFAULT_DISTANCE_PRICING
                    ),
                    "weight": WeightPricing.objects.create(**DEFAULT_WEIGHT_PRICING),
                    "time": TimePricing.objects.create(**DEFAULT_TIME_PRICING),
                    "weather": WeatherPricing.objects.create(**DEFAULT_WEATHER_PRICING),
                    "vehicle": VehicleTypePricing.objects.create(
                        **DEFAULT_VEHICLE_PRICING
                    ),
                    "special_req": SpecialRequirementsPricing.objects.create(
                        **DEFAULT_SPECIAL_REQUIREMENTS_PRICING
                    ),
                    "service": ServiceLevelPricing.objects.create(
                        **DEFAULT_SERVICE_LEVEL_PRICING
                    ),
                    "staff": StaffRequiredPricing.objects.create(
                        **DEFAULT_STAFF_REQUIRED_PRICING
                    ),
                    "property_type": PropertyTypePricing.objects.create(
                        **DEFAULT_PROPERTY_TYPE_PRICING
                    ),
                    "insurance": InsurancePricing.objects.create(
                        **DEFAULT_INSURANCE_PRICING
                    ),
                    "loading_time": LoadingTimePricing.objects.create(
                        **DEFAULT_LOADING_TIME_PRICING
                    ),
                }

                # Associate factors with configuration
                config.distance_factors.add(factors["distance"])
                config.weight_factors.add(factors["weight"])
                config.time_factors.add(factors["time"])
                config.weather_factors.add(factors["weather"])
                config.vehicle_factors.add(factors["vehicle"])
                config.special_requirement_factors.add(factors["special_req"])
                config.service_level_factors.add(factors["service"])
                config.staff_factors.add(factors["staff"])
                config.property_type_factors.add(factors["property_type"])
                config.insurance_factors.add(factors["insurance"])
                config.loading_time_factors.add(factors["loading_time"])

                # For backward compatibility with active_factors
                config.active_factors = {
                    "distance": [str(factors["distance"].id)],
                    "weight": [str(factors["weight"].id)],
                    "time": [str(factors["time"].id)],
                    "weather": [str(factors["weather"].id)],
                    "vehicle_type": [str(factors["vehicle"].id)],
                    "special_requirements": [str(factors["special_req"].id)],
                    "service_level": [str(factors["service"].id)],
                    "staff_required": [str(factors["staff"].id)],
                    "property_type": [str(factors["property_type"].id)],
                    "insurance": [str(factors["insurance"].id)],
                    "loading_time": [str(factors["loading_time"].id)],
                }
                config.save()

                # Clear cache
                cache.delete(PricingService.get_cache_key("active_config"))

                logger.info(
                    f"Associated {len(factors)} default pricing factors with the configuration"
                )
                return config
            except Exception as e:
                logger.error(f"Error creating default configuration: {str(e)}")
                raise

        return None

    @staticmethod
    def _get_pricing_factors(active_config, service_level, property_type, vehicle_type):
        """Get all pricing factors with caching"""
        cache_key = PricingService.get_cache_key(f"factors_{active_config.id}")
        factors = cache.get(cache_key)

        if not factors:
            factors = {
                "distance": active_config.distance_factors.filter(is_active=True),
                "weight": active_config.weight_factors.filter(is_active=True),
                "property": active_config.property_type_factors.filter(
                    is_active=True, property_type=property_type
                ),
                "service_level": active_config.service_level_factors.filter(
                    is_active=True, service_level=service_level
                ),
                "vehicle": active_config.vehicle_factors.filter(
                    is_active=True, vehicle_type=vehicle_type
                ),
                "time": active_config.time_factors.filter(is_active=True),
                "weather": active_config.weather_factors.filter(is_active=True),
                "insurance": active_config.insurance_factors.filter(is_active=True),
                "staff": active_config.staff_factors.filter(is_active=True),
            }
            cache.set(cache_key, factors, PricingService.CACHE_TIMEOUT)

        return factors

    @staticmethod
    def _calculate_distance_cost(distance, factors):
        """Calculate distance-based cost"""
        total_cost = 0
        for factor in factors:
            if distance <= factor.additional_distance_threshold:
                total_cost += factor.calculate_price(distance)
            else:
                base_distance_cost = factor.calculate_price(
                    factor.additional_distance_threshold
                )
                additional_distance = distance - factor.additional_distance_threshold
                additional_cost = (
                    additional_distance
                    * float(factor.base_rate_per_km)
                    * float(factor.additional_distance_multiplier)
                )
                total_cost += base_distance_cost + additional_cost
        return total_cost

    @staticmethod
    def _calculate_weight_cost(weight, factors):
        """Calculate weight-based cost"""
        total_cost = 0
        for factor in factors:
            base_cost = factor.calculate_price(weight)
            if weight > factor.heavy_item_threshold:
                total_cost += float(factor.heavy_item_surcharge)
            total_cost += base_cost
        return total_cost

    @staticmethod
    def _calculate_property_cost(data, factors):
        """Calculate property type cost"""
        total_cost = 0
        for factor in factors:
            total_cost += float(factor.base_rate)
            if data.get("number_of_rooms"):
                total_cost += float(factor.rate_per_room) * data["number_of_rooms"]
            if data.get("floor_number"):
                floor_cost = float(factor.floor_rate) * data["floor_number"]
                if data.get("has_elevator", False):
                    floor_cost *= float(factor.elevator_discount)
                total_cost += floor_cost
        return total_cost

    @staticmethod
    def _calculate_vehicle_cost(factors, total_dimensions=None):
        """Calculate vehicle cost and multiplier based on dimensions and vehicle type"""
        for factor in factors:
            base_rate = float(factor.base_rate)
            capacity_multiplier = float(factor.capacity_multiplier)
            
            # If we have dimensions, adjust multiplier based on volume
            if total_dimensions and 'volume' in total_dimensions:
                volume = total_dimensions['volume']
                # Adjust multiplier based on volume utilization
                if volume > 0:
                    # Example: If volume is more than 80% of max capacity, increase multiplier
                    volume_utilization = min(volume / float(factor.max_volume), 1.0)
                    if volume_utilization > 0.8:
                        capacity_multiplier *= 1.2
                    elif volume_utilization > 0.6:
                        capacity_multiplier *= 1.1
                        
            return base_rate, capacity_multiplier
        return 0, 1.0

    @staticmethod
    def _calculate_insurance_cost(data, factors):
        """Calculate insurance cost"""
        if not data.get("insurance_required", False):
            return 0

        total_cost = 0
        for factor in factors:
            declared_value = float(data.get("declared_value", 0))
            value_based_cost = declared_value * (float(factor.value_percentage) / 100)
            base_cost = max(value_based_cost, float(factor.min_premium))

            if data.get("premium_coverage", False):
                base_cost *= float(factor.premium_coverage_multiplier)

            if data.get("high_value_items", False):
                high_value_surcharge = declared_value * (
                    float(factor.high_value_item_rate) / 100
                )
                base_cost += high_value_surcharge

            total_cost += base_cost
        return total_cost

    @staticmethod
    def _calculate_service_multiplier(factors):
        """Calculate service level multiplier"""
        for factor in factors:
            # Return the multiplier for the matching service level
            if factor.service_level == 'standard':
                return 1.0
            elif factor.service_level == 'express':
                return 1.5
            elif factor.service_level == 'same_day':
                return 2.0
            elif factor.service_level == 'scheduled':
                return 0.9
        return 1.0

    @staticmethod
    def _calculate_time_multiplier(is_weekend, is_holiday, factors):
        """Calculate time-based multiplier"""
        for factor in factors:
            if is_holiday:
                return float(factor.holiday_multiplier)
            elif is_weekend:
                return float(factor.weekend_multiplier)
        return 1.0

    @staticmethod
    def _calculate_weather_multiplier(city: str = None, date: str = None):
        """Calculate weather multiplier based on real weather data"""
        if not city or not date:
            return 1.0, "normal"
        
        weather_data = WeatherService.get_weather_data(city, date)
        weather_type = weather_data["weather_type"]
        
        # Map weather types to multipliers
        multipliers = {
            "normal": 1.0,
            "rain": 1.2,
            "snow": 1.5,
            "extreme": 2.0
        }
        
        return multipliers.get(weather_type, 1.0), weather_type

    @staticmethod
    def _calculate_priority_multiplier(priority_type):
        """Calculate priority-based multiplier"""
        PRIORITY_MULTIPLIERS = {
            'standard': 1.0,    # Base price
            'express': 1.5,     # 50% markup for express
            'same_day': 2.0,    # 100% markup for same day
            'scheduled': 0.9,   # 10% discount for scheduled/flexible
        }
        return PRIORITY_MULTIPLIERS.get(priority_type, 1.0)

    @staticmethod
    def _calculate_staff_prices(
        staff_factors,
        is_weekend,
        is_holiday,
        base_price,
        distance_cost,
        weight_cost,
        property_cost,
        vehicle_cost,
        insurance_cost,
        service_multiplier,
        time_multiplier,
        weather_multiplier,
        vehicle_multiplier,
        active_config,
        priority_type='normal'  # Keep for backward compatibility
    ):
        """Calculate prices for different staff counts"""
        staff_prices = []
        
        # Base rates for different staff counts (in GBP)
        STAFF_BASE_RATES = {
            1: 25.00,  # Single staff member
            2: 45.00,  # Two staff members
            3: 65.00,  # Three staff members
            4: 85.00   # Four staff members
        }
        
        # Minimum hours per job
        MIN_HOURS = 2.0
        
        for staff_count in range(1, 5):
            # Get base rate for this staff count
            base_rate = STAFF_BASE_RATES.get(staff_count, 25.00)
            
            # Calculate staff cost based on minimum hours
            staff_cost = base_rate * MIN_HOURS
            
            # Apply overtime multiplier for weekends/holidays
            if is_weekend or is_holiday:
                staff_cost *= 1.5  # 50% premium for weekends/holidays
            
            # Calculate total price components
            total_price = (
                base_price
                + distance_cost
                + weight_cost
                + property_cost
                + vehicle_cost
                + insurance_cost
                + staff_cost
            )
            
            # Apply multipliers
            total_price *= service_multiplier  # This includes the service level multiplier
            total_price *= time_multiplier
            total_price *= weather_multiplier
            total_price *= vehicle_multiplier
            
            # Apply priority multiplier
            priority_multiplier = PricingService._calculate_priority_multiplier(priority_type)
            total_price *= priority_multiplier
            
            # Add fuel surcharge
            fuel_surcharge = total_price * (float(active_config.fuel_surcharge_percentage) / 100)
            total_price += fuel_surcharge
            
            # Add carbon offset
            carbon_offset = total_price * (float(active_config.carbon_offset_rate) / 100)
            total_price += carbon_offset
            
            # Apply minimum and maximum price constraints
            total_price = max(total_price, float(active_config.min_price))
            max_price = base_price * float(active_config.max_price_multiplier)
            total_price = min(total_price, max_price)
            
            # Round to 2 decimal places
            total_price = round(total_price, 2)
            
            staff_prices.append({
                "staff_count": staff_count,
                "price": total_price,
                "components": {
                    "base_price": round(base_price, 2),
                    "distance_cost": round(distance_cost, 2),
                    "weight_cost": round(weight_cost, 2),
                    "property_cost": round(property_cost, 2),
                    "staff_cost": round(staff_cost, 2),
                    "vehicle_cost": round(vehicle_cost, 2),
                    "insurance_cost": round(insurance_cost, 2),
                    "fuel_surcharge": round(fuel_surcharge, 2),
                    "carbon_offset": round(carbon_offset, 2)
                },
                "multipliers": {
                    "service_multiplier": service_multiplier,
                    "time_multiplier": time_multiplier,
                    "weather_multiplier": weather_multiplier,
                    "vehicle_multiplier": vehicle_multiplier,
                    "priority_multiplier": priority_multiplier
                }
            })
        
        return staff_prices


class WeatherService:
    """Service class to handle weather API integration"""
    
    CACHE_TIMEOUT = 3600  # Cache weather data for 1 hour
    CACHE_KEY_PREFIX = "weather_"
    
    @staticmethod
    def get_cache_key(city: str, date: str) -> str:
        """Generate a cache key for weather data"""
        return f"{WeatherService.CACHE_KEY_PREFIX}{city}_{date}"
    
    @staticmethod
    def get_weather_condition(weather_code: int) -> str:
        """
        Map OpenWeatherMap weather codes to our weather conditions
        https://openweathermap.org/weather-conditions
        """
        if weather_code >= 200 and weather_code < 300:  # Thunderstorm
            return "extreme"
        elif weather_code >= 300 and weather_code < 400:  # Drizzle
            return "rain"
        elif weather_code >= 500 and weather_code < 600:  # Rain
            return "rain"
        elif weather_code >= 600 and weather_code < 700:  # Snow
            return "snow"
        elif weather_code >= 700 and weather_code < 800:  # Atmosphere (fog, mist, etc.)
            return "extreme"
        elif weather_code >= 800 and weather_code < 900:  # Clear/Clouds
            return "normal"
        else:
            return "normal"
    
    @staticmethod
    def get_weather_data(city: str, date: str) -> dict:
        """
        Get weather data for a specific city and date
        Returns cached data if available, otherwise fetches from API
        """
        cache_key = WeatherService.get_cache_key(city, date)
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Get API key from settings
            api_key = settings.OPENWEATHERMAP_API_KEY
            if not api_key:
                logger.warning("OpenWeatherMap API key not configured")
                return {"weather_type": "normal"}
            
            # Convert date string to datetime
            target_date = datetime.strptime(date, "%Y-%m-%d")
            
            # Get coordinates for the city
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city},GB&limit=1&appid={api_key}"
            geo_response = requests.get(geo_url)
            geo_data = geo_response.json()
            
            if not geo_data:
                logger.warning(f"No coordinates found for city: {city}")
                return {"weather_type": "normal"}
            
            lat = geo_data[0]["lat"]
            lon = geo_data[0]["lon"]
            
            # Get 5-day forecast
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            forecast_response = requests.get(forecast_url)
            forecast_data = forecast_response.json()
            
            # Find the forecast for the target date
            target_forecast = None
            for forecast in forecast_data["list"]:
                forecast_date = datetime.fromtimestamp(forecast["dt"])
                if forecast_date.date() == target_date.date():
                    target_forecast = forecast
                    break
            
            if not target_forecast:
                logger.warning(f"No forecast found for date: {date}")
                return {"weather_type": "normal"}
            
            # Get weather condition from the forecast
            weather_code = target_forecast["weather"][0]["id"]
            weather_type = WeatherService.get_weather_condition(weather_code)
            
            weather_data = {
                "weather_type": weather_type,
                "temperature": target_forecast["main"]["temp"],
                "humidity": target_forecast["main"]["humidity"],
                "wind_speed": target_forecast["wind"]["speed"],
                "description": target_forecast["weather"][0]["description"]
            }
            
            # Cache the weather data
            cache.set(cache_key, weather_data, WeatherService.CACHE_TIMEOUT)
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            return {"weather_type": "normal"}
