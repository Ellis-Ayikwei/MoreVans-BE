from rest_framework import serializers
from .models import ServiceCategory, Services


class ServiceCategorySerializer(serializers.ModelSerializer):
    services_count = serializers.SerializerMethodField()

    class Meta:
        model = ServiceCategory
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "icon",
            "services_count",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at", "is_active"]

    def get_services_count(self, obj):
        return obj.services.count()


class ServiceCategoryDetailSerializer(serializers.ModelSerializer):
    services = serializers.SerializerMethodField()

    class Meta:
        model = ServiceCategory
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "icon",
            "services",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at", "is_active"]

    def get_services(self, obj):
        services = obj.services.all()
        return ServiceListSerializer(services, many=True).data


class ServiceListSerializer(serializers.ModelSerializer):
    service_category = ServiceCategorySerializer(read_only=True)
    providers_count = serializers.SerializerMethodField()

    class Meta:
        model = Services
        fields = [
            "id",
            "name",
            "description",
            "service_category",
            "icon",
            "providers_count",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_providers_count(self, obj):
        return obj.providers.count()


class ServiceDetailSerializer(serializers.ModelSerializer):
    service_category = ServiceCategorySerializer(read_only=True)
    providers = serializers.SerializerMethodField()

    class Meta:
        model = Services
        fields = [
            "id",
            "name",
            "description",
            "service_category",
            "icon",
            "providers",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_providers(self, obj):
        from apps.Provider.serializer import ServiceProviderSerializer

        providers = obj.providers.all()
        return ServiceProviderSerializer(providers, many=True).data


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = ["name", "description", "service_category", "icon", "is_active"]

    def validate(self, attrs):
        # Check if service with same name exists in the same category
        name = attrs.get("name")
        service_category = attrs.get("service_category")

        if name and service_category:
            existing_service = Services.objects.filter(
                name=name, service_category=service_category
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing_service.exists():
                raise serializers.ValidationError(
                    f"A service with name '{name}' already exists in this category."
                )
        return attrs


class ServiceCategoryCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ["name", "description", "icon", "is_active"]

    def validate_name(self, value):
        # Check if category with same name exists
        existing_category = ServiceCategory.objects.filter(name=value)
        if self.instance:
            existing_category = existing_category.exclude(pk=self.instance.pk)

        if existing_category.exists():
            raise serializers.ValidationError(
                f"A service category with name '{value}' already exists."
            )
        return value
