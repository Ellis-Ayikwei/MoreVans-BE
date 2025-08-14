from rest_framework import serializers
from .models import Bid


class BidSerializer(serializers.ModelSerializer):
    # Import the provider serializer
    from apps.Provider.serializer import ServiceProviderSerializer

    provider = ServiceProviderSerializer(read_only=True)
    provider_id = serializers.UUIDField(write_only=True, required=True)
    job_id = serializers.UUIDField(write_only=True, required=True)

    class Meta:
        model = Bid
        fields = [
            "id",
            "job",
            "job_id",
            "provider",
            "provider_id",
            "amount",
            "status",
            "message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        """Handle provider_id in creation"""
        provider_id = validated_data.pop("provider_id", None)
        if provider_id:
            from apps.Provider.models import ServiceProvider

            try:
                provider = ServiceProvider.objects.get(id=provider_id)
                validated_data["provider"] = provider
            except ServiceProvider.DoesNotExist:
                raise serializers.ValidationError("Provider not found")

        return super().create(validated_data)
