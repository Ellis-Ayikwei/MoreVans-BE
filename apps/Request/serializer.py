from apps.Driver.models import Driver
from rest_framework import serializers
from .models import (
    Request,
    MoveMilestone,
)
from apps.RequestItems.serializers import RequestItemSerializer
from apps.RequestItems.models import RequestItem
from apps.JourneyStop.models import JourneyStop
from apps.CommonItems.models import CommonItem, ItemCategory
from apps.CommonItems.serializers import CommonItemSerializer, ItemCategorySerializer
from apps.JourneyStop.serializer import JourneyStopSerializer
from apps.Location.models import Location
from apps.Location.serializer import LocationSerializer
from apps.Location.models import Location
from apps.Driver.serializer import DriverSerializer
from datetime import datetime, timedelta
from django.utils import timezone


class MoveMilestoneSerializer(serializers.ModelSerializer):
    estimated_duration = serializers.DurationField(required=False)
    actual_duration = serializers.DurationField(read_only=True)
    scheduled_start = serializers.DateTimeField(required=False, allow_null=True)
    actual_start = serializers.DateTimeField(read_only=True)
    actual_end = serializers.DateTimeField(read_only=True)

    class Meta:
        model = MoveMilestone
        fields = [
            "id",
            "milestone_type",
            "status",
            "estimated_duration",
            "actual_duration",
            "scheduled_start",
            "actual_start",
            "actual_end",
            "notes",
            "delay_reason",
            "sequence",
        ]
        read_only_fields = ["actual_duration", "actual_start", "actual_end"]

    def validate(self, data):
        """Validate milestone data"""
        if data.get("scheduled_start") and data.get("estimated_duration"):
            # Ensure scheduled start is in the future
            if data["scheduled_start"] < timezone.now():
                raise serializers.ValidationError(
                    "Scheduled start time must be in the future"
                )

            # Ensure estimated duration is positive
            if data["estimated_duration"].total_seconds() <= 0:
                raise serializers.ValidationError("Estimated duration must be positive")

        return data

    def update(self, instance, validated_data):
        """Handle status updates and related timestamp changes"""
        new_status = validated_data.get("status")
        if new_status and new_status != instance.status:
            instance.update_status(new_status)

        return super().update(instance, validated_data)


class RequestSerializer(serializers.ModelSerializer):
    items = RequestItemSerializer(many=True, required=False)
    driver = DriverSerializer(read_only=True)
    driver_id = serializers.PrimaryKeyRelatedField(
        queryset=Driver.objects.all(),
        source="driver",
        write_only=True,
        required=False,
        allow_null=True,
    )
    tracking_number = serializers.CharField(read_only=True)
    preferred_pickup_date = serializers.DateField(required=False, allow_null=True)
    preferred_delivery_date = serializers.DateField(required=False, allow_null=True)
    journey_stops = JourneyStopSerializer(many=True, required=False)
    stops = JourneyStopSerializer(many=True, required=False)
    moving_items = serializers.JSONField(required=False, allow_null=True)
    photo_urls = serializers.JSONField(required=False, allow_null=True)
    all_locations = serializers.SerializerMethodField()
    milestones = MoveMilestoneSerializer(many=True, required=False)

    class Meta:
        model = Request
        fields = [
            "id",
            "user",
            "driver",
            "driver_id",
            "request_type",
            "status",
            "service_type",
            "contact_name",
            "contact_phone",
            "contact_email",
            "journey_stops",
            "preferred_pickup_date",
            "preferred_pickup_time",
            "preferred_pickup_time_window",
            "preferred_delivery_date",
            "preferred_delivery_time",
            "is_flexible",
            "estimated_completion_time",
            "items_description",
            "total_weight",
            "dimensions",
            "requires_special_handling",
            "special_instructions",
            "moving_items",
            "photo_urls",
            "base_price",
            "final_price",
            "price_factors",
            "tracking_number",
            "insurance_required",
            "insurance_value",
            "payment_status",
            "cancellation_reason",
            "cancellation_time",
            "cancellation_fee",
            "service_level",
            "estimated_distance",
            "route_waypoints",
            "loading_time",
            "unloading_time",
            "price_breakdown",
            "items",
            "all_locations",
            "created_at",
            "updated_at",
            "stops",
            "milestones",
        ]
        extra_kwargs = {"user": {"read_only": True, "required": False}}

    def get_all_locations(self, obj):
        """Return all locations associated with this request"""
        return obj.get_all_locations()

    def validate(self, data):
        """
        Validate the request data based on request_type
        """
        request_type = data.get("request_type")
        journey_stops = data.get("journey_stops", [])

        # if not journey_stops:
        #     raise serializers.ValidationError(
        #         "journey_stops is required for all request types"
        #     )

        # Validate that there's at least one pickup and one dropoff stop
        pickup_stops = [stop for stop in journey_stops if stop.get("type") == "pickup"]
        dropoff_stops = [
            stop for stop in journey_stops if stop.get("type") == "dropoff"
        ]

        # if not pickup_stops:
        #     raise serializers.ValidationError("At least one pickup stop is required")
        # if not dropoff_stops:
        #     raise serializers.ValidationError("At least one dropoff stop is required")

        # For instant requests, validate moving_items
        # if request_type == "instant" and not data.get("moving_items"):
        #     raise serializers.ValidationError("Instant requests require moving_items")

        return data

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        journey_stops_data = validated_data.pop("journey_stops", [])
        moving_items_data = validated_data.pop("moving_items", [])

        # Remove any potential reverse relation fields that might cause issues
        if "items" in validated_data:
            validated_data.pop("items")
        if "stops" in validated_data:
            validated_data.pop("stops")

        # Get user from context (or use specified user for admin usage)
        user = validated_data.get("user", None)
        if not user and "request" in self.context:
            user = self.context["request"].user
            validated_data["user"] = user

        # Create the request
        request = Request.objects.create(**validated_data)

        # Create items
        for item_data in items_data:
            category_id = item_data.pop("category_id", None)
            if category_id:
                try:
                    category = ItemCategory.objects.get(id=category_id)
                    RequestItem.objects.create(
                        request=request, category=category, **item_data
                    )
                except ItemCategory.DoesNotExist:
                    pass

        # Process journey stops if present
        journey_stops_data = validated_data.pop("journey_stops", None)
        if journey_stops_data and isinstance(journey_stops_data, list):
            for i, stop_data in enumerate(journey_stops_data):
                self._process_journey_stop(request, stop_data, i)

        # Process moving items if no journey stops or items weren't processed
        moving_items_data = validated_data.pop("moving_items", None)
        if moving_items_data and isinstance(moving_items_data, list):
            # Find a pickup stop or create one if none exists
            pickup_stop = JourneyStop.objects.filter(
                request=request, type="pickup"
            ).first()

            # Process each moving item with the pickup stop
            for item_data in moving_items_data:
                self._process_item(request, pickup_stop, item_data)

        return request

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        journey_stops_data = validated_data.pop("journey_stops", None)
        milestones_data = validated_data.pop("milestones", None)

        # Update the request instance with validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update items if provided - delete and recreate for simplicity
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                category_object = item_data.pop("category_id", None)
                if category_object:
                    RequestItem.objects.create(
                        request=instance, category=category_object, **item_data
                    )

        # Update journey stops if provided
        if journey_stops_data is not None:
            # Delete existing stops
            instance.stops.all().delete()
            # Create new stops
            for idx, stop_data in enumerate(journey_stops_data):
                self._process_journey_stop(instance, stop_data, idx)

        # Update milestones if provided
        if milestones_data is not None:
            # Delete existing milestones
            instance.milestones.all().delete()
            # Create new milestones
            for milestone_data in milestones_data:
                MoveMilestone.objects.create(request=instance, **milestone_data)

        instance.save()
        return instance

    def _process_journey_stop(self, request, stop_data, sequence):
        # Helper function to handle empty time strings
        def clean_time_value(value):
            """Convert empty strings to None for time fields"""
            if value == "":
                return None
            return value

        # Helper function to handle empty numeric strings
        def clean_numeric_value(value, default=1):
            """Convert empty strings to default value for numeric fields"""
            if value == "" or value is None:
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default

        # Clean up time fields - convert empty strings to None
        estimated_time = clean_time_value(stop_data.get("estimatedTime", None))
        scheduled_time = clean_time_value(stop_data.get("scheduledTime", None))
        completed_time = clean_time_value(stop_data.get("completedTime", None))

        # Clean up numeric fields with default values
        number_of_rooms = clean_numeric_value(
            stop_data.get("number_of_rooms", None), default=1
        )
        number_of_floors = clean_numeric_value(
            stop_data.get("number_of_floors", None), default=1
        )
        floor = clean_numeric_value(stop_data.get("floor", None), default=0)

        # Create the stop
        stop = JourneyStop.objects.create(
            request=request,
            external_id=stop_data.get("id", ""),
            type=stop_data.get("type", "pickup"),
            address=stop_data.get("address", ""),  # Map location to address
            unit_number=stop_data.get("unit_number", ""),
            floor=floor,
            has_elevator=stop_data.get("has_elevator", False),
            parking_info=stop_data.get("parking_info", ""),
            instructions=stop_data.get("instructions", ""),
            estimated_time=estimated_time,  # Use the cleaned value
            property_type=stop_data.get("property_type", "house"),
            number_of_rooms=number_of_rooms,
            number_of_floors=number_of_floors,
            service_type=stop_data.get("service_type", ""),
            sequence=sequence,
        )

        # Process items for pickup stops
        if stop.type == "pickup":
            # Get items from either 'items' or 'moving_items' key
            items_to_process = []
            if "items" in stop_data and stop_data["items"]:
                items_to_process = stop_data["items"]

            if items_to_process:
                for item_data in items_to_process:
                    # Create the item and associate it with this pickup stop
                    item = self._process_item(request, stop, item_data)

        # Process linked items for dropoff stops
        if stop.type == "dropoff" and "linked_items" in stop_data:
            linked_item_ids = stop_data["linked_items"]
            if linked_item_ids:
                # Find all items with these IDs and link them to this dropoff stop
                for item_id in linked_item_ids:
                    try:
                        item = RequestItem.objects.get(id=item_id, request=request)
                        item.dropoff_stop = stop
                        item.save()
                    except RequestItem.DoesNotExist:
                        # Log that the item wasn't found - could add logger here
                        pass

        return stop

    def _process_item(self, request, stop, item_data):
        """Process and create a request item"""
        try:
            # Get category
            category = None
            if "category_id" in item_data and item_data["category_id"]:
                try:
                    category = ItemCategory.objects.get(id=item_data["category_id"])
                except ItemCategory.DoesNotExist:
                    # Try to find by name if ID fails
                    if "category" in item_data and item_data["category"]:
                        category = ItemCategory.objects.filter(
                            name__iexact=item_data["category"]
                        ).first()

            # Handle photos if present
            photos = []
            if item_data.get("photo"):
                photos.append(item_data["photo"])

            # Create the item and explicitly save it
            item = RequestItem(
                request=request,
                category=category,
                name=item_data.get("name", "Unnamed Item"),
                quantity=item_data.get("quantity", 1),
                weight=item_data.get("weight") if item_data.get("weight") else None,
                dimensions=item_data.get("dimensions", ""),
                fragile=item_data.get("fragile", False),
                needs_disassembly=item_data.get("needs_disassembly", False),
                special_instructions=item_data.get("special_instructions", ""),
                photos=photos,
                declared_value=item_data.get("declared_value", ""),
                pickup_stop=stop,
            )

            # Explicitly save the item
            item.save()
            print(f"Item saved: {item.id} - {item.name}")  # Debug logging

            return item
        except Exception as e:
            # Log the error for debugging
            print(f"Error saving item: {str(e)}")
            raise

    def to_representation(self, instance):
        """Override to ensure journey stops and items are properly included"""
        data = super().to_representation(instance)

        # Ensure journey_stops field contains all stops with their items
        if instance.request_type == "journey":
            stops = instance.stops.all().order_by("sequence")
            data["journey_stops"] = JourneyStopSerializer(stops, many=True).data

        # Ensure items are properly included
        if instance.items.exists():
            data["items"] = RequestItemSerializer(instance.items.all(), many=True).data

        return data
