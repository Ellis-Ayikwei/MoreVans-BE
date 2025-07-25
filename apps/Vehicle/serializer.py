from rest_framework import serializers

from .models import Vehicle, VehicleImages, VehicleDocuments
from apps.Driver.serializer import DriverSerializer
from apps.Provider.serializer import ServiceProviderSerializer
from apps.CommonItems.serializers import (
    VehicleCategorySerializer,
    VehicleTypeSerializer,
)


class VehicleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleImages
        fields = ["id", "image", "description", "order", "created_at"]
        read_only_fields = ["created_at"]


class VehicleDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleDocuments
        fields = [
            "id",
            "document_type",
            "document",
            "description",
            "expiry_date",
            "created_at",
            "vehicle_id",
        ]
        read_only_fields = ["created_at"]


class VehicleSerializer(serializers.ModelSerializer):
    photos = VehicleImageSerializer(many=True, read_only=True)
    documents = VehicleDocumentSerializer(many=True, read_only=True)
    provider = ServiceProviderSerializer(read_only=True)
    vehicle_category = VehicleCategorySerializer(read_only=True)
    vehicle_type = VehicleTypeSerializer(read_only=True)
    primary_driver = DriverSerializer(read_only=True)
    provider_id = serializers.UUIDField(write_only=True, required=False)
    vehicle_category_id = serializers.UUIDField(write_only=True, required=False)
    vehicle_type_id = serializers.UUIDField(write_only=True, required=False)
    primary_driver_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "registration",
            "make",
            "model",
            "year",
            "seats",
            "vehicle_type",
            "vehicle_category",
            "fuel_type",
            "transmission",
            "color",
            "payload_capacity_kg",
            "gross_vehicle_weight_kg",
            "max_length_m",
            "load_volume_m3",
            "insurance_policy_number",
            "insurance_expiry_date",
            "has_tail_lift",
            "has_tracking_device",
            "has_dash_cam",
            "additional_features",
            "provider",
            "primary_driver",
            "is_active",
            "location",
            "last_location_update",
            "primary_location",
            "is_available",
            "provider_id",
            "vehicle_category_id",
            "vehicle_type_id",
            "primary_driver_id",
            "photos",
            "documents",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        provider_id = validated_data.pop("provider_id", None)
        vehicle_category_id = validated_data.pop("vehicle_category_id", None)
        vehicle_type_id = validated_data.pop("vehicle_type_id", None)
        primary_driver_id = validated_data.pop("primary_driver_id", None)

        if provider_id:
            validated_data["provider_id"] = provider_id
        if vehicle_category_id:
            validated_data["vehicle_category_id"] = vehicle_category_id
        if vehicle_type_id:
            validated_data["vehicle_type_id"] = vehicle_type_id
        if primary_driver_id:
            validated_data["primary_driver_id"] = primary_driver_id

        return super().create(validated_data)

    def update(self, instance, validated_data):
        provider_id = validated_data.pop("provider_id", None)
        vehicle_category_id = validated_data.pop("vehicle_category_id", None)
        vehicle_type_id = validated_data.pop("vehicle_type_id", None)
        primary_driver_id = validated_data.pop("primary_driver_id", None)

        if provider_id:
            validated_data["provider_id"] = provider_id
        if vehicle_category_id:
            validated_data["vehicle_category_id"] = vehicle_category_id
        if vehicle_type_id:
            validated_data["vehicle_type_id"] = vehicle_type_id
        if primary_driver_id:
            validated_data["primary_driver_id"] = primary_driver_id

        return super().update(instance, validated_data)


class VehicleImageDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = VehicleImages
        fields = [
            "id",
            "vehicle_id",
            "image",
            "description",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class VehicleDocumentDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = VehicleDocuments
        fields = [
            "id",
            "vehicle_id",
            "document_type",
            "document",
            "description",
            "expiry_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
