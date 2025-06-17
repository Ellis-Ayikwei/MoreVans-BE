import json
from rest_framework import serializers
from .models import JourneyStop
from apps.Location.serializer import LocationSerializer
from apps.Location.models import Location
from apps.Request.models import Request


class JourneyStopSerializer(serializers.ModelSerializer):
    location = LocationSerializer()
    service_type = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    floor = serializers.IntegerField(required=False, allow_null=True, default=0)
    request = serializers.PrimaryKeyRelatedField(
        queryset=Request.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = JourneyStop
        fields = [
            "id",
            "request",
            "location",
            "external_id",
            "type",
            "unit_number",
            "floor",
            "has_elevator",
            "parking_info",
            "instructions",
            "scheduled_time",
            "completed_time",
            "property_type",
            "number_of_rooms",
            "number_of_floors",
            "service_type",
            "sequence",
        ]
        read_only_fields = ["id", "external_id"]

    def create(self, validated_data):
        print("validated_data", json.dumps(validated_data, indent=4, default=str))
        location_data = validated_data.pop("location", {})

        # Handle case where location is already an ID (from bulk_create)
        if isinstance(location_data, int):
            location = Location.objects.get(id=location_data)
        elif isinstance(location_data, dict):
            # Ensure location has required fields with defaults
            location_data.setdefault("address", "")
            location_data.setdefault("postcode", "")
            location_data.setdefault("contact_name", "")
            location_data.setdefault("contact_phone", "")
            
            # # Round coordinates to 6 decimal places
            # if "latitude" in location_data and location_data["latitude"] is not None:
            #     location_data["latitude"] = round(float(location_data["latitude"]), 12)
            # if "longitude" in location_data and location_data["longitude"] is not None:
            #     location_data["longitude"] = round(float(location_data["longitude"]), 12)

            location = Location.objects.create(**location_data)
        else:
            raise serializers.ValidationError(
                {"location": "Location data must be a dictionary or ID"}
            )

        journey_stop = JourneyStop.objects.create(location=location, **validated_data)
        return journey_stop

    def update(self, instance, validated_data):
        location_data = validated_data.pop("location", None)
        if location_data:
            if not isinstance(location_data, dict):
                raise serializers.ValidationError(
                    {"location": "Location data must be a dictionary"}
                )

            location = instance.location
            for key, value in location_data.items():
                setattr(location, key, value)
            location.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        """Convert the instance to a dictionary representation"""
        ret = super().to_representation(instance)
        # Convert UUID to string
        if "id" in ret:
            ret["id"] = str(ret["id"])
        if "request" in ret:
            ret["request"] = str(ret["request"])
        return ret
