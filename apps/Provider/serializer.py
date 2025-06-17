from rest_framework import serializers
from .models import (
    ServiceProvider,
    ServiceArea,
    InsurancePolicy,
    ProviderDocument,
    ProviderReview,
    ProviderPayment,
    SavedJob,
    WatchedJob,
)

from apps.User.serializer import UserSerializer


class ServiceAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceArea
        fields = ["id", "name", "area", "is_primary", "price_multiplier"]


class InsurancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsurancePolicy
        fields = [
            "id",
            "policy_type",
            "coverage_amount",
            "policy_number",
            "expiry_date",
        ]


class ProviderDocumentSerializer(serializers.ModelSerializer):
    front_url = serializers.SerializerMethodField()
    back_url = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    issue_date = serializers.DateField()
    expiry_date = serializers.DateField()
    has_two_sides = serializers.BooleanField()
    status = serializers.ChoiceField(
        choices=ProviderDocument.DOCUMENT_STATUS, default="pending"
    )

    class Meta:
        model = ProviderDocument
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
            return self.context["request"].build_absolute_uri(obj.document_front.url)
        return None

    def get_back_url(self, obj):
        if obj.document_back:
            return self.context["request"].build_absolute_uri(obj.document_back.url)
        return None

    def get_name(self, obj):
        return obj.get_document_type_display()

    def get_type(self, obj):
        return obj.document_type

    def validate(self, data):
        document_type = data.get("document_type")
        has_two_sides = data.get("has_two_sides", False)
        document_back = data.get("document_back")

        # Get the document type info from the choices
        document_types = dict(ProviderDocument.DOCUMENT_TYPES)

        # Validate two-sided documents
        if has_two_sides and not document_back:
            raise serializers.ValidationError(
                "Back side document is required for two-sided documents."
            )

        # Validate expiry date is after issue date
        issue_date = data.get("issue_date")
        expiry_date = data.get("expiry_date")
        if issue_date and expiry_date and expiry_date <= issue_date:
            raise serializers.ValidationError(
                "Expiry date must be after the issue date."
            )

        return data


class ProviderReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = ProviderReview
        fields = [
            "id",
            "customer",
            "customer_name",
            "rating",
            "comment",
            "created_at",
            "is_verified",
        ]

    def get_customer_name(self, obj):
        return obj.customer.get_full_name() if obj.customer else "Anonymous"


class ProviderPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderPayment
        fields = [
            "id",
            "transaction_id",
            "amount",
            "payment_type",
            "status",
            "created_at",
            "completed_at",
            "notes",
        ]


class ServiceProviderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    service_areas = ServiceAreaSerializer(many=True, read_only=True)
    insurance_policies = InsurancePolicySerializer(many=True, read_only=True)
    documents = ProviderDocumentSerializer(many=True, read_only=True)
    reviews = ProviderReviewSerializer(many=True, read_only=True)
    payments = ProviderPaymentSerializer(many=True, read_only=True)

    # Computed fields
    average_rating = serializers.SerializerMethodField()
    completed_bookings_count = serializers.SerializerMethodField()
    vehicle_count = serializers.SerializerMethodField()
    last_active = serializers.SerializerMethodField()

    class Meta:
        model = ServiceProvider
        fields = [
            "id",
            "user",
            "business_type",
            "company_name",
            "company_reg_number",
            "vat_registered",
            "vat_number",
            "business_description",
            "website",
            "founded_year",
            "operating_areas",
            "contact_person_name",
            "contact_person_position",
            "contact_person_email",
            "contact_person_phone",
            "bank_account_holder",
            "bank_name",
            "bank_account_number",
            "bank_routing_number",
            "service_categories",
            "specializations",
            "service_image",
            "base_location",
            "hourly_rate",
            "accepts_instant_bookings",
            "service_radius_km",
            "insurance_policies",
            "payment_methods",
            "minimum_job_value",
            "verification_status",
            "last_verified",
            "service_areas",
            "documents",
            "reviews",
            "payments",
            "average_rating",
            "completed_bookings_count",
            "vehicle_count",
            "last_active",
        ]

    def get_average_rating(self, obj):
        return obj.rating

    def get_completed_bookings_count(self, obj):
        return obj.completed_bookings

    def get_vehicle_count(self, obj):
        return obj.vehicle_count

    def get_last_active(self, obj):
        return obj.last_active

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Import here to avoid circular import
        from apps.Services.serializers import ServiceCategorySerializer

        if instance.service_categories.exists():
            data["service_categories"] = ServiceCategorySerializer(
                instance.service_categories.all(), many=True
            ).data

        if instance.specializations.exists():
            data["specializations"] = ServiceCategorySerializer(
                instance.specializations.all(), many=True
            ).data

        return data


class SavedJobSerializer(serializers.ModelSerializer):
    job_details = serializers.SerializerMethodField()

    class Meta:
        model = SavedJob
        fields = ["id", "job", "job_details", "saved_at", "notes"]

    def get_job_details(self, obj):
        from apps.Job.serializers import JobSerializer

        return JobSerializer(obj.job).data


class WatchedJobSerializer(serializers.ModelSerializer):
    job_details = serializers.SerializerMethodField()

    class Meta:
        model = WatchedJob
        fields = [
            "id",
            "job",
            "job_details",
            "started_watching",
            "notify",
            "notification_preferences",
        ]

    def get_job_details(self, obj):
        from apps.Job.serializers import JobSerializer

        return JobSerializer(obj.job).data
