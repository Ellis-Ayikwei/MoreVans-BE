from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework import status
from .models import (
    ServiceProvider,
    ServiceArea,
    InsurancePolicy,
    ProviderDocument,
    ProviderReview,
    ProviderPayment,
    SavedJob,
    WatchedJob,
    ServiceProviderAddress,
)

from apps.User.serializer import UserSerializer
from apps.User.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from django.db import transaction
import logging


class EmailAlreadyExistsException(APIException):
    """Custom exception for email already exists with 409 status code"""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Email address is already registered"
    default_code = "email_already_exists"


logger = logging.getLogger(__name__)


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

    # FIXED: Use CharField for input, handle conversion in to_internal_value
    founded_year = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    minimum_job_value = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    payment_methods = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    service_categories = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    service_image = serializers.ImageField(
        required=False, allow_null=True, allow_empty_file=True
    )
    specializations = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

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
            "created_at",
            "updated_at",
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
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "user",
            "average_rating",
            "completed_bookings_count",
            "vehicle_count",
            "last_active",
        ]

    def to_internal_value(self, data):
        """Override to preprocess data before field validation"""
        # Make a copy to avoid modifying the original data
        data = data.copy() if hasattr(data, "copy") else dict(data)

        # Define empty values
        empty_values = [None, "", "null", "undefined", "NULL", "Null", " ", "  "]

        # Preprocess founded_year
        if "founded_year" in data:
            value = data["founded_year"]
            if value in empty_values or (
                isinstance(value, str) and value.strip() in empty_values
            ):
                data["founded_year"] = None
            elif isinstance(value, str) and value.strip():
                try:
                    data["founded_year"] = int(value)
                except (ValueError, TypeError):
                    data["founded_year"] = None
            elif value is not None:
                # Handle non-string values
                try:
                    data["founded_year"] = int(value)
                except (ValueError, TypeError):
                    data["founded_year"] = None

        # Preprocess minimum_job_value
        if "minimum_job_value" in data:
            value = data["minimum_job_value"]
            if value in empty_values or (
                isinstance(value, str) and value.strip() in empty_values
            ):
                data["minimum_job_value"] = None
            elif isinstance(value, str) and value.strip():
                try:
                    data["minimum_job_value"] = float(value)
                except (ValueError, TypeError):
                    data["minimum_job_value"] = None
            elif value is not None:
                # Handle non-string values
                try:
                    data["minimum_job_value"] = float(value)
                except (ValueError, TypeError):
                    data["minimum_job_value"] = None

        # Preprocess base_location (GIS PointField)
        if "base_location" in data:
            value = data["base_location"]
            if value in empty_values or (
                isinstance(value, str) and value.strip() in empty_values
            ):
                data["base_location"] = None
            elif isinstance(value, str) and value.strip():
                try:
                    import json

                    coords = json.loads(value)
                    if isinstance(coords, list) and len(coords) == 2:
                        from django.contrib.gis.geos import Point

                        data["base_location"] = Point(
                            float(coords[0]), float(coords[1])
                        )
                    else:
                        data["base_location"] = None
                except (json.JSONDecodeError, ValueError, TypeError, ImportError):
                    data["base_location"] = None

        # FIXED: Preprocess list fields with better handling
        list_fields = ["payment_methods", "service_categories", "specializations"]
        for field_name in list_fields:
            if field_name in data:
                value = data[field_name]

                # Handle None and empty values
                if value in empty_values:
                    data[field_name] = "[]"  # Convert to empty JSON array string
                # Handle lists - convert to JSON string
                elif isinstance(value, list):
                    try:
                        import json

                        data[field_name] = json.dumps(value)
                    except (TypeError, ValueError):
                        data[field_name] = "[]"
                # Handle strings
                elif isinstance(value, str):
                    if value.strip() in empty_values:
                        data[field_name] = "[]"
                    else:
                        # Keep as is if it's already a string
                        data[field_name] = value
                # Handle other data types - convert to JSON string
                else:
                    try:
                        import json

                        data[field_name] = (
                            json.dumps(value) if value is not None else "[]"
                        )
                    except (TypeError, ValueError):
                        data[field_name] = "[]"

        # Preprocess service_image
        if "service_image" in data:
            value = data["service_image"]
            if value in empty_values or (
                isinstance(value, str) and value.strip() in empty_values
            ):
                data["service_image"] = None

        # Call the parent method with preprocessed data
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """Custom representation to handle ManyToMany fields properly"""
        data = super().to_representation(instance)

        # Handle ManyToMany fields properly for output
        try:
            # Service categories
            if (
                hasattr(instance, "service_categories")
                and instance.service_categories.exists()
            ):
                from apps.Services.serializers import ServiceCategorySerializer

                data["service_categories"] = ServiceCategorySerializer(
                    instance.service_categories.all(), many=True
                ).data
            else:
                data["service_categories"] = []

            # Specializations
            if (
                hasattr(instance, "specializations")
                and instance.specializations.exists()
            ):
                from apps.Services.serializers import ServiceCategorySerializer

                data["specializations"] = ServiceCategorySerializer(
                    instance.specializations.all(), many=True
                ).data
            else:
                data["specializations"] = []

            # Payment methods
            if (
                hasattr(instance, "payment_methods")
                and instance.payment_methods.exists()
            ):
                try:
                    from apps.Payment.serializers import PaymentMethodSerializer

                    data["payment_methods"] = PaymentMethodSerializer(
                        instance.payment_methods.all(), many=True
                    ).data
                except ImportError:
                    # If PaymentMethodSerializer doesn't exist, just return IDs
                    data["payment_methods"] = [
                        pm.id for pm in instance.payment_methods.all()
                    ]
            else:
                data["payment_methods"] = []

        except ImportError:
            # Fallback: return empty lists if serializers don't exist
            data["service_categories"] = []
            data["specializations"] = []
            data["payment_methods"] = []

        return data

    def get_average_rating(self, obj):
        return getattr(obj, "rating", 0)

    def get_completed_bookings_count(self, obj):
        return getattr(obj, "completed_bookings", 0)

    def get_vehicle_count(self, obj):
        return getattr(obj, "vehicle_count", 0)

    def get_last_active(self, obj):
        return getattr(obj, "last_active", None)

    def update(self, instance, validated_data):
        # Extract ManyToMany data
        service_categories_data = validated_data.pop("service_categories", None)
        specializations_data = validated_data.pop("specializations", None)
        payment_methods_data = validated_data.pop("payment_methods", None)

        # Update the instance with non-ManyToMany fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update ManyToMany fields
        if service_categories_data is not None:
            from apps.Services.models import ServiceCategory

            if isinstance(service_categories_data, list):
                categories = ServiceCategory.objects.filter(
                    id__in=service_categories_data
                )
                instance.service_categories.set(categories)

        if specializations_data is not None:
            from apps.Services.models import ServiceCategory

            if isinstance(specializations_data, list):
                specializations = ServiceCategory.objects.filter(
                    id__in=specializations_data
                )
                instance.specializations.set(specializations)

        if payment_methods_data is not None:
            try:
                from apps.Payment.models import PaymentMethod

                if isinstance(payment_methods_data, list):
                    payment_methods = PaymentMethod.objects.filter(
                        id__in=payment_methods_data
                    )
                    instance.payment_methods.set(payment_methods)
            except ImportError:
                pass

        return instance

    def validate_payment_methods(self, value):
        """Handle payment_methods validation"""
        return self._process_list_field(value)

    def validate_service_categories(self, value):
        """Handle service_categories validation"""
        return self._process_list_field(value)

    def validate_specializations(self, value):
        """Handle specializations validation"""
        return self._process_list_field(value)

    def _process_list_field(self, value):
        """Common processing for list fields"""
        empty_values = [None, "", "null", "undefined", "NULL", "Null", " ", "  "]

        # Handle empty values
        if value in empty_values or (
            isinstance(value, str) and value.strip() in empty_values
        ):
            return []

        # If it's already a list, return it
        if isinstance(value, list):
            return value

        # If it's a string, try to parse it
        if isinstance(value, str):
            if value.strip() == "":
                return []
            try:
                import json

                parsed = json.loads(value)
                return (
                    parsed
                    if isinstance(parsed, list)
                    else [parsed] if parsed is not None else []
                )
            except (json.JSONDecodeError, TypeError):
                items = [item.strip() for item in value.split(",") if item.strip()]
                return [int(item) for item in items if item.isdigit()] if items else []

        return []


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


class ServiceProviderAddressSerializer(serializers.ModelSerializer):
    """Serializer for ServiceProviderAddress model"""

    class Meta:
        model = ServiceProviderAddress
        fields = [
            "id",
            "address_type",
            "address_line_1",
            "address_line_2",
            "city",
            "postcode",
            "state",
            "country",
            "business_name",
            "is_primary",
            "is_verified",
            "is_active",
            "verification_date",
            "verification_method",
            "notes",
        ]
        read_only_fields = ["id", "verification_date"]


class ProviderRegistrationSerializer(serializers.Serializer):
    """Comprehensive serializer for provider registration"""

    # User fields
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    confirm_password = serializers.CharField(write_only=True, required=True)
    mobile_number = serializers.CharField(max_length=15, required=True)
    phone_number = serializers.CharField(max_length=15, required=True)

    # Provider fields
    business_name = serializers.CharField(max_length=200, required=True)
    business_type = serializers.ChoiceField(
        choices=ServiceProvider.BUSINESS_TYPES, required=True
    )
    vat_registered = serializers.CharField(required=True)  # "yes" or "no"
    number_of_vehicles = serializers.CharField(required=True)
    work_types = serializers.ListField(child=serializers.CharField(), required=True)

    # Address fields
    address_line_1 = serializers.CharField(max_length=255, required=True)
    address_line_2 = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    city = serializers.CharField(max_length=100, required=True)
    postcode = serializers.CharField(max_length=20, required=True)
    country = serializers.CharField(max_length=100, required=True)

    # Business address fields (optional)
    has_separate_business_address = serializers.BooleanField(required=True)
    business_address_line_1 = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    business_address_line_2 = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    business_city = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    business_postcode = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    business_country = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )

    # Non-UK address fields (optional)
    has_non_uk_address = serializers.BooleanField(required=True)
    non_uk_address_line_1 = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    non_uk_address_line_2 = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    non_uk_city = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    non_uk_postal_code = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    non_uk_country = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )

    # Additional fields
    accepted_privacy_policy = serializers.BooleanField(required=True)
    selected_address = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """Validate the registration data"""
        # Check if passwords match
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")

        # Check if email already exists
        if User.objects.filter(email=attrs["email"]).exists():
            raise EmailAlreadyExistsException()

        # Validate business address fields if has_separate_business_address is True
        if attrs.get("has_separate_business_address"):
            required_business_fields = [
                "business_address_line_1",
                "business_city",
                "business_postcode",
                "business_country",
            ]
            for field in required_business_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError(
                        f"{field.replace('_', ' ').title()} is required when separate business address is selected"
                    )

        # Validate non-UK address fields if has_non_uk_address is True
        if attrs.get("has_non_uk_address"):
            required_non_uk_fields = [
                "non_uk_address_line_1",
                "non_uk_city",
                "non_uk_postal_code",
                "non_uk_country",
            ]
            for field in required_non_uk_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError(
                        f"{field.replace('_', ' ').title()} is required when non-UK address is selected"
                    )

        # Validate privacy policy acceptance
        if not attrs.get("accepted_privacy_policy"):
            raise serializers.ValidationError("You must accept the privacy policy")

        return attrs

    def create(self, validated_data):
        """Create user, provider, and addresses in a transaction"""
        with transaction.atomic():
            # Create user
            user_data = {
                "email": validated_data["email"].lower().strip(),
                "password": make_password(validated_data["password"]),
                "first_name": validated_data["first_name"],
                "last_name": validated_data["last_name"],
                "phone_number": validated_data["phone_number"],
                "user_type": "provider",
            }

            user = User.objects.create(**user_data)

            # Create provider
            provider_data = {
                "user": user,
                "company_name": validated_data["business_name"],
                "business_type": validated_data["business_type"],
                "vat_registered": validated_data["vat_registered"].lower() == "yes",
                "vehicle_count": self._parse_vehicle_count(
                    validated_data["number_of_vehicles"]
                ),
            }

            provider = ServiceProvider.objects.create(**provider_data)

            # Create addresses
            addresses = []

            # Home address (always created)
            home_address_data = {
                "provider": provider,
                "address_type": "home",
                "address_line_1": self._to_lowercase(validated_data["address_line_1"]),
                "address_line_2": self._to_lowercase(
                    validated_data.get("address_line_2", "")
                ),
                "city": self._to_lowercase(validated_data["city"]),
                "postcode": self._to_lowercase(validated_data["postcode"]),
                "country": self._to_lowercase(validated_data["country"]),
                "is_primary": True,  # Home address is primary by default
                "is_verified": True,  # Auto-verify for registration
                "verification_method": "manual_verification",
            }

            home_address = ServiceProviderAddress.objects.create(**home_address_data)
            addresses.append(home_address)

            # Business address (if separate business address is selected)
            if validated_data.get("has_separate_business_address"):
                business_address_data = {
                    "provider": provider,
                    "address_type": "business",
                    "address_line_1": self._to_lowercase(
                        validated_data["business_address_line_1"]
                    ),
                    "address_line_2": self._to_lowercase(
                        validated_data.get("business_address_line_2", "")
                    ),
                    "city": self._to_lowercase(validated_data["business_city"]),
                    "postcode": self._to_lowercase(validated_data["business_postcode"]),
                    "country": self._to_lowercase(validated_data["business_country"]),
                    "business_name": validated_data["business_name"],
                    "is_primary": False,
                    "is_verified": True,
                    "verification_method": "manual_verification",
                }

                business_address = ServiceProviderAddress.objects.create(
                    **business_address_data
                )
                addresses.append(business_address)

            # Non-UK address (if non-UK address is selected)
            if validated_data.get("has_non_uk_address"):
                non_uk_address_data = {
                    "provider": provider,
                    "address_type": "non_uk",
                    "address_line_1": self._to_lowercase(
                        validated_data["non_uk_address_line_1"]
                    ),
                    "address_line_2": self._to_lowercase(
                        validated_data.get("non_uk_address_line_2", "")
                    ),
                    "city": self._to_lowercase(validated_data["non_uk_city"]),
                    "postcode": self._to_lowercase(
                        validated_data["non_uk_postal_code"]
                    ),
                    "country": self._to_lowercase(validated_data["non_uk_country"]),
                    "is_primary": False,
                    "is_verified": True,
                    "verification_method": "manual_verification",
                }

                non_uk_address = ServiceProviderAddress.objects.create(
                    **non_uk_address_data
                )
                addresses.append(non_uk_address)

            logger.info(
                f"Provider registration completed: User ID {user.id}, Provider ID {provider.id}"
            )

            return {
                "user": user,
                "provider": provider,
                "addresses": addresses,
                "work_types": validated_data.get("work_types", []),
            }

    def _parse_vehicle_count(self, vehicle_count_str):
        """Parse vehicle count string to integer"""
        if vehicle_count_str == "1":
            return 1
        elif vehicle_count_str == "2-5":
            return 3  # Average
        elif vehicle_count_str == "6-10":
            return 8  # Average
        elif vehicle_count_str == "11+":
            return 15  # Representative value
        elif vehicle_count_str == "No Vehicle":
            return 0
        return 0

    def _to_lowercase(self, value):
        """Convert value to lowercase safely, handling None and empty strings"""
        if value is None:
            return ""
        return str(value).lower().strip()

    def _process_work_types(self, provider, work_types):
        """Process work types and link to services"""
        try:
            from apps.Services.models import Services

            # Map frontend work types to service names
            service_mapping = {
                "Home removals": "Home Removals",
                "International removals": "International Removals",
                "Office removals": "Office Removals",
                "Student removals": "Student Removals",
                "Storage services": "Storage Services",
                "Furniture & appliance delivery": "Furniture Delivery",
                "Piano delivery": "Piano Delivery",
                "Parcel delivery": "Parcel Delivery",
                "eBay delivery": "eBay Delivery",
                "Gumtree delivery": "Gumtree Delivery",
                "Heavy & large item delivery": "Heavy Item Delivery",
                "Specialist & antiques delivery": "Antiques Delivery",
                "Car transport": "Car Transport",
                "Motorcycle transport": "Motorcycle Transport",
            }

            services_to_add = []
            for work_type in work_types:
                service_name = service_mapping.get(work_type, work_type)
                try:
                    service = Services.objects.get(name__icontains=service_name)
                    services_to_add.append(service)
                except Services.DoesNotExist:
                    # If service doesn't exist, try to find a default category or skip
                    try:
                        # Try to get a default service category
                        from apps.Services.models import ServiceCategory

                        default_category = ServiceCategory.objects.first()

                        if default_category:
                            service = Services.objects.create(
                                name=work_type,
                                description=f"Service for {work_type}",
                                is_active=True,
                                service_category=default_category,
                            )
                        else:
                            # Skip creating service if no category exists
                            logger.warning(
                                f"No service category found, skipping service creation for: {work_type}"
                            )
                            continue
                    except Exception as category_error:
                        logger.error(
                            f"Error creating service for {work_type}: {str(category_error)}"
                        )
                        continue

                    services_to_add.append(service)

            # Add services to provider
            if services_to_add:
                provider.services_offered.set(services_to_add)

        except ImportError:
            logger.warning("Services app not available, skipping work types processing")
        except Exception as e:
            logger.error(f"Error processing work types: {str(e)}")

    def to_representation(self, instance):
        """Return serialized data"""
        if isinstance(instance, dict):
            return {
                "user": UserSerializer(instance["user"]).data,
                "provider": ServiceProviderSerializer(instance["provider"]).data,
                "addresses": ServiceProviderAddressSerializer(
                    instance["addresses"], many=True
                ).data,
                "message": "Provider registration successful. Please verify your email to activate your account.",
            }
        return super().to_representation(instance)
