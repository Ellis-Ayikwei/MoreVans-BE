from rest_framework import serializers
from .models import Bid


class BidSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(
        source="provider.company_name", read_only=True
    )
    provider_rating = serializers.FloatField(source="provider.rating", read_only=True)
    provider_review_count = serializers.IntegerField(
        source="provider.review_count", read_only=True
    )

    class Meta:
        model = Bid
        fields = [
            "id",
            "job",
            "provider",
            "provider_name",
            "provider_rating",
            "provider_review_count",
            "amount",
            "status",
            "created_at",
            "expires_at",
            "notes",
            "proposed_start_time",
            "estimated_duration",
        ]
        read_only_fields = ["id", "created_at", "status"]
