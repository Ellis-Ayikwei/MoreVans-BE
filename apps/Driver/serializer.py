from rest_framework import serializers
from apps.Driver.models import (
    Driver,
    DriverLocation,
    DriverAvailability,
    DriverDocument,
    DriverInfringement,
)
from django.utils import timezone


class DriverSerializer(serializers.ModelSerializer):
    is_license_valid = serializers.BooleanField(read_only=True)
    is_cpc_valid = serializers.BooleanField(read_only=True)
    needs_license_renewal = serializers.BooleanField(read_only=True)
    adr_expiry_date = serializers.DateField(allow_null=True, required=False)
    induction_date = serializers.DateField(allow_null=True, required=False)

    def to_internal_value(self, data):
        # Handle empty strings for date fields
        if "adr_expiry_date" in data and data["adr_expiry_date"] == "":
            data["adr_expiry_date"] = None
        if "induction_date" in data and data["induction_date"] == "":
            data["induction_date"] = None
        return super().to_internal_value(data)

    class Meta:
        model = Driver
        fields = [
            "id",
            "name",
            "email",
            "phone_number",
            "date_of_birth",
            "national_insurance_number",
            "address",
            "postcode",
            "location",
            "last_location_update",
            "provider",
            "employment_type",
            "date_started",
            "license_number",
            "license_country_of_issue",
            "license_categories",
            "license_expiry_date",
            "digital_tachograph_card_number",
            "tacho_card_expiry_date",
            "has_cpc",
            "cpc_expiry_date",
            "has_adr",
            "adr_expiry_date",
            "induction_completed",
            "induction_date",
            "max_weekly_hours",
            "opted_out_of_working_time_directive",
            "status",
            "verification_status",
            "last_verified",
            "verification_notes",
            "penalty_points",
            "preferred_vehicle_types",
            "notes",
            "is_license_valid",
            "is_cpc_valid",
            "needs_license_renewal",
            "all_documents_verified",
            "has_required_documents",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "verification_status",
            "last_verified",
            "all_documents_verified",
            "has_required_documents",
        ]


class DriverLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverLocation
        fields = [
            "id",
            "driver",
            "location",
            "timestamp",
            "speed",
            "heading",
            "accuracy",
        ]
        read_only_fields = ["timestamp"]


class DriverAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverAvailability
        fields = [
            "id",
            "driver",
            "date",
            "time_slots",
            "service_areas",
            "max_jobs",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class DriverDocumentSerializer(serializers.ModelSerializer):
    front_url = serializers.SerializerMethodField()
    back_url = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    issue_date = serializers.DateField()
    expiry_date = serializers.DateField()
    has_two_sides = serializers.BooleanField()
    status = serializers.ChoiceField(
        choices=DriverDocument.DOCUMENT_STATUS, default="pending"
    )

    class Meta:
        model = DriverDocument
        fields = [
            "id",
            "document_type",
            "document_front",
            "document_back",
            "front_url",
            "back_url",
            "has_two_sides",
            "name",
            "type",
            "issue_date",
            "expiry_date",
            "has_two_sides",
            "reference_number",
            "notes",
            "is_verified",
            "rejection_reason",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "is_verified",
            "rejection_reason",
            "status",
        ]

    def get_front_url(self, obj):
        if obj.document_front:
            return f"uploads/docs/drivers/{obj.driver.id}/{obj.id}/{obj.document_front.name.split('/')[-1]}"
        return None

    def get_back_url(self, obj):
        if obj.document_back:
            return f"uploads/docs/drivers/{obj.driver.id}/{obj.id}/{obj.document_back.name.split('/')[-1]}"
        return None

    def get_name(self, obj):
        return obj.get_document_type_display()

    def get_type(self, obj):
        return obj.document_type

    def create(self, validated_data):
        driver = self.context["driver"]
        document_front = validated_data.pop("document_front", None)
        document_back = validated_data.pop("document_back", None)

        document = DriverDocument.objects.create(driver=driver, **validated_data)

        if document_front:
            document.document_front.save(document_front.name, document_front)
        if document_back:
            document.document_back.save(document_back.name, document_back)

        return document


class DriverInfringementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverInfringement
        fields = [
            "id",
            "driver",
            "infringement_type",
            "infringement_date",
            "description",
            "penalty_points_added",
            "fine_amount",
            "reported_by",
            "is_resolved",
            "resolution_date",
            "resolution_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


# Extended serializer that includes related data
class DriverDetailSerializer(DriverSerializer):
    documents = DriverDocumentSerializer(many=True, read_only=True)
    infringements = DriverInfringementSerializer(many=True, read_only=True)
    availability_slots = DriverAvailabilitySerializer(many=True, read_only=True)

    class Meta(DriverSerializer.Meta):
        fields = DriverSerializer.Meta.fields + [
            "documents",
            "infringements",
            "availability_slots",
        ]
