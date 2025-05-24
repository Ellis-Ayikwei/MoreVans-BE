from rest_framework import serializers
from .models import RequestItem
from apps.CommonItems.serializers import ItemCategorySerializer
from apps.CommonItems.models import ItemCategory


class RequestItemSerializer(serializers.ModelSerializer):
    request_id = serializers.IntegerField(write_only=True, required=False)
    category = ItemCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ItemCategory.objects.all(), source="category", write_only=True
    )

    class Meta:
        model = RequestItem
        fields = [
            "id",
            "request_id",
            "category",
            "category_id",
            "name",
            "description",
            "quantity",
            "weight",
            "dimensions",
            "fragile",
            "needs_disassembly",
            "special_instructions",
            "photos",
            "declared_value",
        ]
        extra_kwargs = {"request": {"read_only": True}}
