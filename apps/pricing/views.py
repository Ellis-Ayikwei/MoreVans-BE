from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q
from datetime import timedelta, datetime, date
import holidays
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
from .serializers import (
    DistancePricingSerializer,
    WeightPricingSerializer,
    TimePricingSerializer,
    WeatherPricingSerializer,
    VehicleTypePricingSerializer,
    SpecialRequirementsPricingSerializer,
    LocationPricingSerializer,
    PricingConfigurationSerializer,
    ServiceLevelPricingSerializer,
    StaffRequiredPricingSerializer,
    PropertyTypePricingSerializer,
    InsurancePricingSerializer,
    LoadingTimePricingSerializer,
    PriceCalculationSerializer,
    DateBasedPriceCalculationSerializer,
)
from .services import PricingService


class PricingFactorViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]

    # def get_permissions(self):
    #     if self.action in ["create", "update", "partial_update", "destroy"]:
    #         return [IsAdminUser()]
    #     return super().get_permissions()


class DistancePricingViewSet(PricingFactorViewSet):
    queryset = DistancePricing.objects.all()
    serializer_class = DistancePricingSerializer


class WeightPricingViewSet(PricingFactorViewSet):
    queryset = WeightPricing.objects.all()
    serializer_class = WeightPricingSerializer


class TimePricingViewSet(PricingFactorViewSet):
    queryset = TimePricing.objects.all()
    serializer_class = TimePricingSerializer


class WeatherPricingViewSet(PricingFactorViewSet):
    queryset = WeatherPricing.objects.all()
    serializer_class = WeatherPricingSerializer


class VehicleTypePricingViewSet(PricingFactorViewSet):
    queryset = VehicleTypePricing.objects.all()
    serializer_class = VehicleTypePricingSerializer


class SpecialRequirementsPricingViewSet(PricingFactorViewSet):
    queryset = SpecialRequirementsPricing.objects.all()
    serializer_class = SpecialRequirementsPricingSerializer


class LocationPricingViewSet(PricingFactorViewSet):
    queryset = LocationPricing.objects.all()
    serializer_class = LocationPricingSerializer


class ServiceLevelPricingViewSet(PricingFactorViewSet):
    queryset = ServiceLevelPricing.objects.all()
    serializer_class = ServiceLevelPricingSerializer


class StaffRequiredPricingViewSet(PricingFactorViewSet):
    queryset = StaffRequiredPricing.objects.all()
    serializer_class = StaffRequiredPricingSerializer


class PropertyTypePricingViewSet(PricingFactorViewSet):
    queryset = PropertyTypePricing.objects.all()
    serializer_class = PropertyTypePricingSerializer


class InsurancePricingViewSet(PricingFactorViewSet):
    queryset = InsurancePricing.objects.all()
    serializer_class = InsurancePricingSerializer


class LoadingTimePricingViewSet(PricingFactorViewSet):
    queryset = LoadingTimePricing.objects.all()
    serializer_class = LoadingTimePricingSerializer


class PricingConfigurationViewSet(viewsets.ModelViewSet):
    queryset = PricingConfiguration.objects.all()
    serializer_class = PricingConfigurationSerializer
    # permission_classes = [permissions.IsAdminUser]
    permission_classes = [permissions.AllowAny]
    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "delete",
    ]  # Explicitly allow POST

    # def get_permissions(self):
    #     """
    #     Instantiates and returns the list of permissions that this view requires.
    #     """
    #     if self.action in [
    #         "create",
    #         "update",
    #         "partial_update",
    #         "destroy",
    #         "set_default",
    #     ]:
    #         return [permissions.IsAdminUser()]
    #     return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """Create a new pricing configuration"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=False, methods=["patch"])
    def set_default(self, request):
        """Set a configuration as the default one"""
        configuration_id = request.data.get("configuration_id")
        if not configuration_id:
            return Response(
                {"error": "configuration_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # First, unset any existing default
            PricingConfiguration.objects.filter(is_default=True).update(
                is_default=False
            )

            # Set the new default
            config = PricingConfiguration.objects.get(id=configuration_id)
            config.is_default = True
            config.save()

            return Response(
                {
                    "message": f"Configuration {config.name} set as default",
                    "configuration": self.get_serializer(config).data,
                }
            )
        except PricingConfiguration.DoesNotExist:
            return Response(
                {"error": "Configuration not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"])
    def calculate_price(self, request):
        """
        Calculate the final price based on all active pricing factors
        """
        serializer = PriceCalculationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        total_price = 0
        price_breakdown = {}

        # Get active configuration
        config = PricingConfiguration.objects.filter(is_active=True).first()
        if not config:
            return Response(
                {"error": "No active pricing configuration found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Base price
        total_price = float(config.base_price)
        price_breakdown["base_price"] = total_price

        # Distance pricing
        if data.get("distance"):
            distance_pricing = DistancePricing.objects.filter(is_active=True).first()
            if distance_pricing:
                distance_cost = distance_pricing.calculate_price(data["distance"])
                total_price += distance_cost
                price_breakdown["distance_cost"] = distance_cost

        # Weight pricing
        if data.get("weight"):
            weight_pricing = WeightPricing.objects.filter(is_active=True).first()
            if weight_pricing:
                weight_cost = weight_pricing.calculate_price(data["weight"])
                total_price += weight_cost
                price_breakdown["weight_cost"] = weight_cost

        # Service Level pricing
        if data.get("service_level"):
            service_pricing = ServiceLevelPricing.objects.filter(
                is_active=True, service_level=data["service_level"]
            ).first()
            if service_pricing:
                service_multiplier = float(service_pricing.price_multiplier)
                service_cost = total_price * (service_multiplier - 1)
                total_price *= service_multiplier
                price_breakdown["service_level_cost"] = service_cost

        # Staff Required pricing
        if data.get("staff_required"):
            staff_pricing = StaffRequiredPricing.objects.filter(is_active=True).first()
            if staff_pricing:
                staff_count = min(
                    max(data["staff_required"], staff_pricing.min_staff),
                    staff_pricing.max_staff,
                )
                staff_cost = float(staff_pricing.base_rate_per_staff) * staff_count
                total_price += staff_cost
                price_breakdown["staff_cost"] = staff_cost

        # Property Type pricing
        if data.get("property_type"):
            property_pricing = PropertyTypePricing.objects.filter(
                is_active=True, property_type=data["property_type"]
            ).first()
            if property_pricing:
                # Base property cost
                property_cost = float(property_pricing.base_rate)

                # Add room cost
                if data.get("number_of_rooms"):
                    property_cost += (
                        float(property_pricing.rate_per_room) * data["number_of_rooms"]
                    )

                # Add floor cost
                if data.get("floor_number"):
                    if not data.get("has_elevator", True):
                        property_cost += (
                            float(property_pricing.floor_rate) * data["floor_number"]
                        )
                    else:
                        property_cost *= float(property_pricing.elevator_discount)

                total_price += property_cost
                price_breakdown["property_cost"] = property_cost

        # Time factors
        time_pricing = TimePricing.objects.filter(is_active=True).first()
        if time_pricing:
            time_multiplier = 1.0
            if data.get("is_peak_hour"):
                time_multiplier *= float(time_pricing.peak_hour_multiplier)
            if data.get("is_weekend"):
                time_multiplier *= float(time_pricing.weekend_multiplier)
            if data.get("is_holiday"):
                time_multiplier *= float(time_pricing.holiday_multiplier)

            if time_multiplier > 1.0:
                time_cost = total_price * (time_multiplier - 1)
                total_price *= time_multiplier
                price_breakdown["time_factors_cost"] = time_cost

        # Loading/Unloading Time pricing
        loading_pricing = LoadingTimePricing.objects.filter(is_active=True).first()
        if loading_pricing:
            total_time = timedelta()
            if data.get("loading_time"):
                total_time += data["loading_time"]
            if data.get("unloading_time"):
                total_time += data["unloading_time"]

            if total_time:
                hours = total_time.total_seconds() / 3600
                min_hours = float(loading_pricing.min_hours)
                base_rate = float(loading_pricing.base_rate_per_hour)

                if hours > min_hours:
                    overtime_hours = hours - min_hours
                    loading_cost = (min_hours * base_rate) + (
                        overtime_hours
                        * base_rate
                        * float(loading_pricing.overtime_multiplier)
                    )
                else:
                    loading_cost = hours * base_rate

                total_price += loading_cost
                price_breakdown["loading_time_cost"] = loading_cost

        # Weather conditions
        weather_pricing = WeatherPricing.objects.filter(is_active=True).first()
        if weather_pricing and data.get("weather_condition") != "normal":
            weather_condition = data["weather_condition"]
            weather_multiplier = 1.0

            if weather_condition == "rain":
                weather_multiplier = float(weather_pricing.rain_multiplier)
            elif weather_condition == "snow":
                weather_multiplier = float(weather_pricing.snow_multiplier)
            elif weather_condition == "extreme":
                weather_multiplier = float(weather_pricing.extreme_weather_multiplier)

            if weather_multiplier > 1.0:
                weather_cost = total_price * (weather_multiplier - 1)
                total_price *= weather_multiplier
                price_breakdown["weather_cost"] = weather_cost

        # Vehicle type
        if data.get("vehicle_type"):
            vehicle_pricing = VehicleTypePricing.objects.filter(
                is_active=True, vehicle_type=data["vehicle_type"]
            ).first()
            if vehicle_pricing:
                vehicle_cost = float(vehicle_pricing.base_rate)
                total_price += vehicle_cost
                total_price *= float(vehicle_pricing.capacity_multiplier)
                price_breakdown["vehicle_cost"] = vehicle_cost

        # Special requirements
        special_pricing = SpecialRequirementsPricing.objects.filter(
            is_active=True
        ).first()
        if special_pricing:
            special_cost = 0
            if data.get("has_fragile_items"):
                fragile_cost = total_price * (
                    float(special_pricing.fragile_items_multiplier) - 1
                )
                total_price *= float(special_pricing.fragile_items_multiplier)
                special_cost += fragile_cost
            if data.get("requires_assembly"):
                assembly_cost = float(special_pricing.assembly_required_rate)
                total_price += assembly_cost
                special_cost += assembly_cost
            if data.get("requires_special_equipment"):
                equipment_cost = float(special_pricing.special_equipment_rate)
                total_price += equipment_cost
                special_cost += equipment_cost

            if special_cost > 0:
                price_breakdown["special_requirements_cost"] = special_cost

        # Insurance
        if data.get("insurance_required") and data.get("insurance_value"):
            insurance_pricing = InsurancePricing.objects.filter(is_active=True).first()
            if insurance_pricing:
                insurance_cost = max(
                    float(insurance_pricing.min_premium),
                    float(data["insurance_value"])
                    * float(insurance_pricing.value_percentage)
                    / 100,
                )
                total_price += insurance_cost
                price_breakdown["insurance_cost"] = insurance_cost

        # Location factors
        if data.get("pickup_city") or data.get("dropoff_city"):
            location_query = Q()
            if data.get("pickup_city"):
                location_query |= Q(city_name=data["pickup_city"])
            if data.get("dropoff_city"):
                location_query |= Q(city_name=data["dropoff_city"])

            location_pricing = LocationPricing.objects.filter(is_active=True).filter(
                location_query
            )

            location_cost = 0
            for location in location_pricing:
                total_price *= float(location.zone_multiplier)
                location_cost += float(location.congestion_charge)
                location_cost += float(location.parking_fee)

            if location_cost > 0:
                total_price += location_cost
                price_breakdown["location_cost"] = location_cost

        # Environmental factors
        if data.get("carbon_offset") and config.carbon_offset_rate > 0:
            carbon_cost = float(config.carbon_offset_rate) * total_price / 100
            total_price += carbon_cost
            price_breakdown["carbon_offset_cost"] = carbon_cost

        # Fuel surcharge
        if config.fuel_surcharge_percentage > 0:
            fuel_surcharge = float(config.fuel_surcharge_percentage) * total_price / 100
            total_price += fuel_surcharge
            price_breakdown["fuel_surcharge"] = fuel_surcharge

        # Apply min price and max multiplier constraints
        total_price = max(float(config.min_price), total_price)
        max_price = float(config.base_price) * float(config.max_price_multiplier)
        total_price = min(max_price, total_price)

        return Response(
            {
                "total_price": round(total_price, 2),
                "currency": "GBP",
                "price_breakdown": price_breakdown,
            }
        )

    @action(detail=False, methods=["post"])
    def calculate_date_based_prices(self, request):
        """
        Calculate prices for the next two months with different staff requirements.
        Returns a calendar-friendly format with staff prices for each day.
        """
        PricingService.ensure_default_config_exists()

        print("Pricing endpoint accessed", request.data)
        serializer = DateBasedPriceCalculationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Set start date to today and end date to two months from today
        start_date = date.today()
        end_date = start_date + timedelta(days=90)  # Approximately two months

        # Get UK holidays
        uk_holidays = holidays.UK()

        # Initialize response structure
        calendar_prices = []
        current_date = start_date

        while current_date <= end_date:
            # Determine if it's a weekend or holiday
            is_weekend = current_date.weekday() >= 5
            is_holiday = current_date in uk_holidays

            # Get weather prediction (mock for now - integrate with weather API later)
            weather_condition = self._get_weather_prediction(
                current_date, data.get("pickup_city")
            )

            # Calculate traffic multiplier (mock for now - integrate with traffic API later)
            traffic_multiplier = self._get_traffic_prediction(current_date)

            # Calculate prices for different staff counts (1 to 4 staff members)
            staff_prices = {}
            for staff_count in range(1, 5):
                price_data = {
                    **data,
                    "staff_required": staff_count,
                    "is_weekend": is_weekend,
                    "is_holiday": is_holiday,
                    "weather_condition": weather_condition,
                    "traffic_multiplier": traffic_multiplier,
                    "request_id": request.request_id,
                }

                # Create a request object for the pricing view
                pricing_request = type("Request", (), {"data": price_data})()
                response = self.calculate_price(pricing_request)

                if response.status_code == 200:
                    staff_prices[f"staff_{staff_count}"] = {
                        "total_price": response.data["total_price"],
                        "currency": response.data["currency"],
                        "price_breakdown": response.data["price_breakdown"],
                    }

            # Add day information to calendar
            calendar_prices.append(
                {
                    "date": current_date.isoformat(),
                    "day_of_week": current_date.strftime("%A"),
                    "is_weekend": is_weekend,
                    "is_holiday": is_holiday,
                    "weather_condition": weather_condition,
                    "traffic_multiplier": traffic_multiplier,
                    "staff_prices": staff_prices,
                    "request_id": request.request_id,
                }
            )

            current_date += timedelta(days=1)

        # Sort calendar by date
        calendar_prices.sort(key=lambda x: x["date"])

        # Group by month for easier display
        monthly_calendar = {}
        for day in calendar_prices:
            date_obj = datetime.strptime(day["date"], "%Y-%m-%d").date()
            month_key = date_obj.strftime("%Y-%m")
            if month_key not in monthly_calendar:
                monthly_calendar[month_key] = []
            monthly_calendar[month_key].append(day)

        return Response(
            {
                "monthly_calendar": monthly_calendar,
                "date_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            }
        )

    def _get_weather_prediction(self, date, city):
        """
        Mock weather prediction - integrate with weather API
        """
        # This is a placeholder - integrate with a real weather API
        return "normal"

    def _get_traffic_prediction(self, date):
        """
        Mock traffic prediction - integrate with traffic API
        """
        # This is a placeholder - integrate with a real traffic API
        return 1.0


class AdminPricingFactorsViewSet(viewsets.ViewSet):
    """ViewSet to get/update all pricing factors for admin purposes."""

    permission_classes = [
        permissions.AllowAny
    ]  # For development, change to IsAuthenticated/IsAdminUser for production

    def list(self, request):
        """Get all pricing factors grouped by type"""
        # Get active configuration for reference
        active_config = PricingConfiguration.objects.filter(is_active=True).first()

        response_data = {
            "distance": self._serialize_model(DistancePricing, active_config),
            "weight": self._serialize_model(WeightPricing, active_config),
            "time": self._serialize_model(TimePricing, active_config),
            "weather": self._serialize_model(WeatherPricing, active_config),
            "vehicle_type": self._serialize_model(VehicleTypePricing, active_config),
            "special_requirements": self._serialize_model(
                SpecialRequirementsPricing, active_config
            ),
            "location": self._serialize_model(LocationPricing, active_config),
            "service_level": self._serialize_model(ServiceLevelPricing, active_config),
            "staff_required": self._serialize_model(
                StaffRequiredPricing, active_config
            ),
            "property_type": self._serialize_model(PropertyTypePricing, active_config),
            "insurance": self._serialize_model(InsurancePricing, active_config),
            "loading_time": self._serialize_model(LoadingTimePricing, active_config),
            "configurations": self._serialize_model(PricingConfiguration),
        }

        if active_config:
            response_data["active_configuration"] = PricingConfigurationSerializer(
                active_config
            ).data

        return Response(response_data)

    def _serialize_model(self, model_class, active_config=None):
        """Helper to serialize all instances of a model class"""
        serializer_class = self._get_serializer_for_model(model_class)
        instances = model_class.objects.all()

        # Use context={'request': None} to prevent URL generation
        serialized_data = serializer_class(
            instances, many=True, context={"request": None}
        ).data

        # If we have an active config, mark which factors are associated with it
        if active_config and model_class != PricingConfiguration:
            relation_name = self._get_relation_name(model_class)
            if relation_name:
                active_ids = set(
                    getattr(active_config, relation_name).values_list("id", flat=True)
                )

                for item in serialized_data:
                    item["in_active_config"] = item["id"] in active_ids

        return serialized_data

    def _get_relation_name(self, model_class):
        """Get the related name for a factor model class"""
        model_name = model_class.__name__
        relation_map = {
            "DistancePricing": "distance_factors",
            "WeightPricing": "weight_factors",
            "TimePricing": "time_factors",
            "WeatherPricing": "weather_factors",
            "VehicleTypePricing": "vehicle_factors",
            "SpecialRequirementsPricing": "special_requirement_factors",
            "LocationPricing": "location_factors",
            "ServiceLevelPricing": "service_level_factors",
            "StaffRequiredPricing": "staff_factors",
            "PropertyTypePricing": "property_type_factors",
            "InsurancePricing": "insurance_factors",
            "LoadingTimePricing": "loading_time_factors",
        }
        return relation_map.get(model_name)

    def _get_serializer_for_model(self, model_class):
        """Get the appropriate serializer for a model class"""
        model_name = model_class.__name__
        if model_name == "PricingConfiguration":
            return PricingConfigurationSerializer
        else:
            # Use CamelCase naming convention to match your imports
            serializer_name = f"{model_name}Serializer"
            return globals()[serializer_name]
