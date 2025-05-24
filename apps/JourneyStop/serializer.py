from rest_framework import serializers
from .models import JourneyStop
from apps.RequestItems.serializers import RequestItemSerializer


class JourneyStopSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    linked_items = serializers.SerializerMethodField()
    estimated_time = serializers.TimeField(
        format="%H:%M",
        input_formats=["%H:%M", "%I:%M %p", "%H:%M:%S"],
        required=False,
        allow_null=True,
    )
    service_type = serializers.ChoiceField(
        choices=JourneyStop.SERVICE_TYPE_CHOICES, required=False, allow_null=True
    )
    floor = serializers.IntegerField(required=False, allow_null=True, default=0)

    class Meta:
        model = JourneyStop
        fields = [
            "id",
            "external_id",
            "type",
            "address",
            "unit_number",
            "floor",
            "has_elevator",
            "parking_info",
            "instructions",
            "estimated_time",
            "scheduled_time",
            "completed_time",
            "property_type",
            "number_of_rooms",
            "number_of_floors",
            "service_type",
            "sequence",
            "items",
            "linked_items",
        ]

    def get_items(self, obj):
        """Returns items that are picked up at this stop"""
        if obj.type == "pickup":
            items = obj.pickup_items.all()
            return RequestItemSerializer(items, many=True).data
        return []

    def get_linked_items(self, obj):
        """Returns items that are dropped off at this stop"""
        if obj.type == "dropoff":
            items = obj.dropoff_items.all()
            return RequestItemSerializer(items, many=True).data
        return []

    def to_internal_value(self, data):
        """Override to handle time format conversion on input"""
        if "estimated_time" in data and data["estimated_time"]:
            try:
                time_str = data["estimated_time"].strip()

                # Handle empty or invalid time strings
                if not time_str:
                    data["estimated_time"] = None
                else:
                    # Try parsing different time formats
                    from datetime import datetime

                    try:
                        # Handle HTML time input format (HH:MM)
                        if ":" in time_str and len(time_str.split(":")) == 2:
                            hours, minutes = map(int, time_str.split(":"))
                            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                                data["estimated_time"] = datetime.strptime(
                                    time_str, "%H:%M"
                                ).time()
                        # Try 12-hour format with AM/PM
                        elif "AM" in time_str.upper() or "PM" in time_str.upper():
                            data["estimated_time"] = datetime.strptime(
                                time_str, "%I:%M %p"
                            ).time()
                        # Try 24-hour format with seconds
                        elif time_str.count(":") == 2:
                            data["estimated_time"] = datetime.strptime(
                                time_str, "%H:%M:%S"
                            ).time()
                        # Try 24-hour format without seconds
                        else:
                            data["estimated_time"] = datetime.strptime(
                                time_str, "%H:%M"
                            ).time()
                    except ValueError:
                        raise serializers.ValidationError(
                            {
                                "estimated_time": "Invalid time format. Use HH:MM (24-hour format)"
                            }
                        )
            except Exception as e:
                # Make sure we don't catch unrelated errors
                if "floor" in str(e):
                    # Let the original error through
                    raise
                raise serializers.ValidationError(
                    {"estimated_time": f"Error processing time: {str(e)}"}
                )

        return super().to_internal_value(data)

    def to_representation(self, instance):
        """Override to format time for output"""
        data = super().to_representation(instance)
        if instance.estimated_time:
            data["estimated_time"] = instance.estimated_time.strftime("%H:%M")
        return data
