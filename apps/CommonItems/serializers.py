from rest_framework import serializers
from .models import ItemCategory, CommonItem


class ItemCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = [
            "id",
            "name",
            "requires_special_handling",
            "restricted",
            "insurance_required",
            "price_multiplier",
            "special_instructions",
            "icon",
            "image",
        ]


class CommonItemSerializer(serializers.ModelSerializer):
    category = ItemCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ItemCategory.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_icon = serializers.CharField(source="category.icon", read_only=True)
    category_color = serializers.CharField(source="category.color", read_only=True)

    class Meta:
        model = CommonItem
        fields = [
            "id",
            "name",
            "category",
            "category_id",
            "category_name",
            "category_icon",
            "category_color",
            "description",
            "weight",
            "dimensions",
            "fragile",
            "needs_disassembly",
            "icon",
            "image",
            "dimensions",
            "weight",
        ]
