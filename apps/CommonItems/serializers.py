from rest_framework import serializers
from .models import (
    ItemCategory,
    ItemType,
    ItemBrand,
    ItemModel,
    CommonItem,
    VehicleCategory,
    VehicleSize,
    VehicleType,
)


class ItemCategorySerializer(serializers.ModelSerializer):
    """Serializer for ItemCategory model"""

    class Meta:
        model = ItemCategory
        fields = [
            "id",
            "name",
            "description",
            "requires_special_handling",
            "restricted",
            "insurance_required",
            "price_multiplier",
            "special_instructions",
            "icon",
            "image",
            "color",
            "tab_color",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ItemTypeSerializer(serializers.ModelSerializer):
    """Serializer for ItemType model"""

    category = ItemCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = ItemType
        fields = [
            "id",
            "name",
            "category",
            "category_id",
            "description",
            "icon",
            "image",
            "color",
            "tab_color",
            "priority",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ItemBrandSerializer(serializers.ModelSerializer):
    """Serializer for ItemBrand model"""

    category = ItemCategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ItemBrand
        fields = [
            "id",
            "name",
            "category",
            "category_id",
            "description",
            "icon",
            "image",
            "color",
            "tab_color",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ItemModelSerializer(serializers.ModelSerializer):
    """Serializer for ItemModel model"""

    brand = ItemBrandSerializer(read_only=True)
    brand_id = serializers.IntegerField(write_only=True)
    category = serializers.SerializerMethodField()

    class Meta:
        model = ItemModel
        fields = [
            "id",
            "name",
            "brand",
            "brand_id",
            "category",
            "description",
            "icon",
            "image",
            "color",
            "tab_color",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_category(self, obj):
        """Get category through brand relationship"""
        if obj.brand and obj.brand.category:
            return {"id": obj.brand.category.id, "name": obj.brand.category.name}
        return None


class CommonItemSerializer(serializers.ModelSerializer):
    """Serializer for CommonItem model"""

    category = ItemCategorySerializer(read_only=True)
    brand = ItemBrandSerializer(read_only=True)
    model = ItemModelSerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    brand_id = serializers.IntegerField(write_only=True)
    model_id = serializers.IntegerField(write_only=True)

    # Display fields for better frontend experience
    category_name = serializers.CharField(source="category.name", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    model_name = serializers.CharField(source="model.name", read_only=True)
    weight = serializers.CharField(source="get_weight_display", read_only=True)
    dimensions = serializers.CharField(source="get_dimensions_display", read_only=True)
    fragile = serializers.CharField(source="get_fragile_display", read_only=True)
    disassembly = serializers.CharField(
        source="get_disassembly_display", read_only=True
    )

    class Meta:
        model = CommonItem
        fields = [
            "id",
            "name",
            "category",
            "brand",
            "model",
            "category_id",
            "brand_id",
            "model_id",
            "category_name",
            "brand_name",
            "model_name",
            "description",
            "weight",
            "dimensions",
            "fragile",
            "needs_disassembly",
            "disassembly",
            "model_number",
            "serial_number",
            "year",
            "model_year",
            "icon",
            "image",
            "color",
            "tab_color",
            "service_category",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ItemCategoryWithBrandsSerializer(ItemCategorySerializer):
    """Serializer for ItemCategory with nested brands"""

    brands = ItemBrandSerializer(many=True, read_only=True)

    class Meta(ItemCategorySerializer.Meta):
        fields = ItemCategorySerializer.Meta.fields + ["brands"]


class ItemBrandWithModelsSerializer(ItemBrandSerializer):
    """Serializer for ItemBrand with nested models"""

    models = ItemModelSerializer(many=True, read_only=True)

    class Meta(ItemBrandSerializer.Meta):
        fields = ItemBrandSerializer.Meta.fields + ["models"]


class CommonItemListSerializer(serializers.ModelSerializer):
    """Simplified serializer for CommonItem list view"""

    category = ItemCategorySerializer(read_only=True)
    brand = ItemBrandSerializer(read_only=True)
    model = ItemModelSerializer(read_only=True)
    type = ItemTypeSerializer(read_only=True)
    weight = serializers.CharField(source="get_weight_display", read_only=True)
    dimensions = serializers.CharField(source="get_dimensions_display", read_only=True)
    fragile = serializers.CharField(source="get_fragile_display", read_only=True)
    disassembly = serializers.CharField(
        source="get_disassembly_display", read_only=True
    )

    def get_brand(self, obj):
        """Get brand name, handling None values"""
        return obj.brand.name if obj.brand else ""

    def get_model(self, obj):
        """Get model name, handling None values"""
        return obj.model.name if obj.model else ""

    class Meta:
        model = CommonItem
        fields = [
            "id",
            "name",
            "category",
            "brand",
            "model",
            "type",
            "weight",
            "dimensions",
            "fragile",
            "disassembly",
            "icon",
            "image",
        ]


# Nested serializers for cascading dropdowns
class CategoryForDropdownSerializer(serializers.ModelSerializer):
    """Simplified serializer for category dropdown"""

    class Meta:
        model = ItemCategory
        fields = ["id", "name"]


class TypeForDropdownSerializer(serializers.ModelSerializer):
    """Simplified serializer for type dropdown"""

    category = CategoryForDropdownSerializer(read_only=True)

    class Meta:
        model = ItemType
        fields = ["id", "name", "category"]


class BrandForDropdownSerializer(serializers.ModelSerializer):
    """Simplified serializer for brand dropdown"""

    category = CategoryForDropdownSerializer(read_only=True)

    class Meta:
        model = ItemBrand
        fields = ["id", "name", "category"]


class ModelForDropdownSerializer(serializers.ModelSerializer):
    """Simplified serializer for model dropdown"""

    brand = BrandForDropdownSerializer(read_only=True)

    class Meta:
        model = ItemModel
        fields = ["id", "name", "brand"]


class VehicleSizeSerializer(serializers.ModelSerializer):
    """Serializer for VehicleSize model"""

    class Meta:
        model = VehicleSize
        fields = [
            "id",
            "name",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class VehicleTypeSerializer(serializers.ModelSerializer):
    """Serializer for VehicleType model"""

    class Meta:
        model = VehicleType
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class VehicleCategorySerializer(serializers.ModelSerializer):
    """Serializer for VehicleCategory model"""

    vehicle_size = VehicleSizeSerializer(read_only=True)
    type = VehicleTypeSerializer(read_only=True)
    vehicle_size_id = serializers.IntegerField(write_only=True, required=False)
    type_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = VehicleCategory
        fields = [
            "id",
            "name",
            "description",
            "icon",
            "image",
            "color",
            "tab_color",
            "is_active",
            "vehicle_size",
            "vehicle_size_id",
            "type",
            "type_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class VehicleCategoryDropdownSerializer(serializers.ModelSerializer):
    """Simplified serializer for vehicle category dropdown"""

    vehicle_size = VehicleSizeSerializer(read_only=True)
    type = VehicleTypeSerializer(read_only=True)

    class Meta:
        model = VehicleCategory
        fields = ["id", "name", "icon", "color", "vehicle_size", "type"]
