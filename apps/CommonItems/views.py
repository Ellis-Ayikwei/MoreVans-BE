from django.shortcuts import render
from django.db.models import Q, Count
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import (
    ItemCategory,
    ItemType,
    ItemBrand,
    ItemModel,
    CommonItem,
    VehicleType,
    VehicleCategory,
    VehicleSize,
)
from .serializers import (
    ItemCategorySerializer,
    ItemTypeSerializer,
    ItemBrandSerializer,
    ItemModelSerializer,
    CommonItemSerializer,
    ItemCategoryWithBrandsSerializer,
    ItemBrandWithModelsSerializer,
    CommonItemListSerializer,
    CategoryForDropdownSerializer,
    TypeForDropdownSerializer,
    BrandForDropdownSerializer,
    ModelForDropdownSerializer,
    VehicleTypeSerializer,
    VehicleCategorySerializer,
    VehicleSizeSerializer,
    VehicleCategoryDropdownSerializer,
)


class ItemCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for ItemCategory model"""

    queryset = ItemCategory.objects.all()
    serializer_class = ItemCategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["name"]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = ItemCategory.objects.all()
        requires_special_handling = self.request.query_params.get(
            "special_handling", None
        )
        restricted = self.request.query_params.get("restricted", None)

        if requires_special_handling is not None:
            requires_special_handling_bool = (
                str(requires_special_handling).lower() == "true"
            )
            queryset = queryset.filter(
                requires_special_handling=requires_special_handling_bool
            )
        if restricted is not None:
            restricted_bool = str(restricted).lower() == "true"
            queryset = queryset.filter(restricted=restricted_bool)

        return queryset

    @action(detail=False, methods=["get"])
    def with_brands(self, request):
        """Get categories with nested brands"""
        categories = self.get_queryset()
        serializer = ItemCategoryWithBrandsSerializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def dropdown(self, request):
        """Get categories for dropdown"""
        categories = self.get_queryset()
        serializer = CategoryForDropdownSerializer(categories, many=True)
        return Response(serializer.data)


class ItemTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for ItemType model"""

    queryset = ItemType.objects.select_related("category").all()
    serializer_class = ItemTypeSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description", "category__name"]
    ordering_fields = ["name", "category__name", "priority", "created_at", "updated_at"]
    ordering = ["category__name", "priority", "name"]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Filter by category if provided"""
        queryset = super().get_queryset()
        category_id = self.request.query_params.get("category_id", None)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    @action(detail=False, methods=["get"])
    def dropdown(self, request):
        """Get item types for dropdown"""
        item_types = self.get_queryset()
        serializer = TypeForDropdownSerializer(item_types, many=True)
        return Response(serializer.data)


class ItemBrandViewSet(viewsets.ModelViewSet):
    """ViewSet for ItemBrand model"""

    queryset = ItemBrand.objects.select_related("category").all()
    serializer_class = ItemBrandSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description", "category__name"]
    ordering_fields = ["name", "category__name", "created_at", "updated_at"]
    ordering = ["category__name", "name"]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Filter by category if provided"""
        queryset = super().get_queryset()
        category_id = self.request.query_params.get("category_id", None)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    @action(detail=False, methods=["get"])
    def with_models(self, request):
        """Get brands with nested models"""
        brands = self.get_queryset()
        serializer = ItemBrandWithModelsSerializer(brands, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def dropdown(self, request):
        """Get brands for dropdown"""
        brands = self.get_queryset()
        serializer = BrandForDropdownSerializer(brands, many=True)
        return Response(serializer.data)


class ItemModelViewSet(viewsets.ModelViewSet):
    """ViewSet for ItemModel model"""

    queryset = ItemModel.objects.select_related("brand", "brand__category").all()
    serializer_class = ItemModelSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description", "brand__name", "brand__category__name"]
    ordering_fields = [
        "name",
        "brand__name",
        "brand__category__name",
        "created_at",
        "updated_at",
    ]
    ordering = ["brand__category__name", "brand__name", "name"]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Filter by brand if provided"""
        queryset = super().get_queryset()
        brand_id = self.request.query_params.get("brand_id", None)
        if brand_id is not None:
            queryset = queryset.filter(brand_id=brand_id)
        return queryset

    @action(detail=False, methods=["get"])
    def dropdown(self, request):
        """Get models for dropdown"""
        models = self.get_queryset()
        serializer = ModelForDropdownSerializer(models, many=True)
        return Response(serializer.data)


class CommonItemViewSet(viewsets.ModelViewSet):
    """ViewSet for CommonItem model"""

    queryset = CommonItem.objects.select_related("category", "brand", "model").all()
    serializer_class = CommonItemSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "name",
        "description",
        "category__name",
        "brand__name",
        "model__name",
    ]
    ordering_fields = [
        "name",
        "category__name",
        "brand__name",
        "model__name",
        "created_at",
        "updated_at",
    ]
    ordering = ["category__name", "brand__name", "model__name", "name"]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Apply additional filters"""
        queryset = super().get_queryset()
        # Filter by category
        category_id = self.request.query_params.get("category_id", None)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)

        # Filter by brand
        brand_id = self.request.query_params.get("brand_id", None)
        if brand_id is not None:
            queryset = queryset.filter(brand_id=brand_id)

        # Filter by model
        model_id = self.request.query_params.get("model_id", None)
        if model_id is not None:
            queryset = queryset.filter(model_id=model_id)

        # Filter by fragile
        fragile = self.request.query_params.get("fragile", None)
        if fragile is not None:
            fragile_bool = str(fragile).lower() == "true"
            queryset = queryset.filter(fragile=fragile_bool)

        # Filter by needs_disassembly
        needs_disassembly = self.request.query_params.get("needs_disassembly", None)
        if needs_disassembly is not None:
            needs_disassembly_bool = str(needs_disassembly).lower() == "true"
            queryset = queryset.filter(needs_disassembly=needs_disassembly_bool)

        return queryset

    def get_serializer_class(self):
        """Use different serializer for list view"""
        if self.action == "list":
            return CommonItemListSerializer
        return CommonItemSerializer

    @action(detail=False, methods=["get"])
    def search(self, request):
        """Search items with query parameter"""
        query = request.query_params.get("q", "")
        if not query:
            return Response(
                {"error": 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = self.get_queryset().filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
            | Q(brand__name__icontains=query)
            | Q(model__name__icontains=query)
        )
        serializer = CommonItemListSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def categories_with_items(self, request):
        """Get categories with their item counts"""
        categories = ItemCategory.objects.annotate(item_count=Count("items")).filter(
            item_count__gt=0
        )

        data = []
        for category in categories:
            items = CommonItem.objects.filter(category=category)
            data.append(
                {
                    "id": category.id,
                    "name": category.name,
                    "item_count": category.item_count,
                    "icon": category.icon,
                    "color": category.color,
                    "items": [
                        {
                            "id": item.id,
                            "name": item.name,
                            "dimensions": item.dimensions,
                            "weight": item.weight,
                            "needs_disassembly": item.needs_disassembly,
                            "fragile": item.fragile,
                            "type": item.type.name if item.type else None,
                        }
                        for item in items
                    ],
                }
            )

        return Response(data)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        """Duplicate an item"""
        item = self.get_object()
        new_item = CommonItem.objects.create(
            name=f"{item.name} (Copy)",
            category=item.category,
            brand=item.brand,
            model=item.model,
            description=item.description,
            weight=item.weight,
            dimensions=item.dimensions,
            fragile=item.fragile,
            needs_disassembly=item.needs_disassembly,
            model_number=item.model_number,
            serial_number=item.serial_number,
            year=item.year,
            model_year=item.model_year,
            icon=item.icon,
            image=item.image,
            color=item.color,
            tab_color=item.tab_color,
            service_category=item.service_category,
        )
        serializer = self.get_serializer(new_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VehicleTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for VehicleType model"""

    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "is_active", "created_at", "updated_at"]
    ordering = ["name"]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = VehicleType.objects.all()
        is_active = self.request.query_params.get("is_active", None)

        if is_active is not None:
            is_active_bool = str(is_active).lower() == "true"
            queryset = queryset.filter(is_active=is_active_bool)

        return queryset

    @action(detail=False, methods=["get"])
    def dropdown(self, request):
        """Get vehicle types for dropdown"""
        vehicle_types = self.get_queryset()
        serializer = VehicleTypeSerializer(vehicle_types, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["put"])
    def activate(self, request, pk=None):
        obj = self.get_object()
        obj.is_active = True
        obj.save()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=True, methods=["put"])
    def deactivate(self, request, pk=None):
        obj = self.get_object()
        obj.is_active = False
        obj.save()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)


class VehicleSizeViewSet(viewsets.ModelViewSet):
    """ViewSet for VehicleSize model"""

    queryset = VehicleSize.objects.all()
    serializer_class = VehicleSizeSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["name"]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = VehicleSize.objects.all()
        return queryset

    @action(detail=False, methods=["get"])
    def dropdown(self, request):
        """Get vehicle sizes for dropdown"""
        vehicle_sizes = self.get_queryset()
        serializer = VehicleSizeSerializer(vehicle_sizes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        obj = self.get_object()
        obj.is_active = True
        obj.save()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        obj = self.get_object()
        obj.is_active = False
        obj.save()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)


class VehicleCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for VehicleCategory model"""

    queryset = VehicleCategory.objects.select_related("type", "vehicle_size").all()
    serializer_class = VehicleCategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description", "type__name", "vehicle_size__name"]
    ordering_fields = [
        "name",
        "type__name",
        "vehicle_size__name",
        "is_active",
        "created_at",
        "updated_at",
    ]
    ordering = ["type__name", "vehicle_size__name", "name"]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Apply additional filters"""
        queryset = super().get_queryset()

        # Filter by vehicle type
        type_id = self.request.query_params.get("type_id", None)
        if type_id is not None:
            queryset = queryset.filter(type_id=type_id)

        # Filter by vehicle size
        size_id = self.request.query_params.get("size_id", None)
        if size_id is not None:
            queryset = queryset.filter(vehicle_size_id=size_id)

        # Filter by active status
        is_active = self.request.query_params.get("is_active", None)
        if is_active is not None:
            is_active_bool = str(is_active).lower() == "true"
            queryset = queryset.filter(is_active=is_active_bool)

        return queryset

    def get_serializer_class(self):
        """Use different serializer for list view"""
        if self.action == "list":
            return VehicleCategoryDropdownSerializer
        return VehicleCategorySerializer

    @action(detail=False, methods=["get"])
    def dropdown(self, request):
        """Get vehicle categories for dropdown"""
        categories = self.get_queryset()
        serializer = VehicleCategoryDropdownSerializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_type(self, request):
        """Get vehicle categories grouped by type"""
        type_id = request.query_params.get("type_id")
        if not type_id:
            return Response(
                {"error": "type_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        categories = self.get_queryset().filter(type_id=type_id)
        serializer = VehicleCategoryDropdownSerializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_size(self, request):
        """Get vehicle categories grouped by size"""
        size_id = request.query_params.get("size_id")
        if not size_id:
            return Response(
                {"error": "size_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        categories = self.get_queryset().filter(vehicle_size_id=size_id)
        serializer = VehicleCategoryDropdownSerializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def hierarchy(self, request):
        """Get complete vehicle hierarchy: types -> categories -> sizes"""
        vehicle_types = VehicleType.objects.filter(is_active=True).prefetch_related(
            "vehiclecategory_set__vehicle_size"
        )

        hierarchy_data = []
        for vehicle_type in vehicle_types:
            type_data = {
                "id": vehicle_type.id,
                "name": vehicle_type.name,
                "description": vehicle_type.description,
                "categories": [],
            }

            for category in vehicle_type.vehiclecategory_set.filter(is_active=True):
                category_data = {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "icon": category.icon,
                    "color": category.color,
                    "vehicle_size": (
                        {
                            "id": category.vehicle_size.id,
                            "name": category.vehicle_size.name,
                            "description": category.vehicle_size.description,
                        }
                        if category.vehicle_size
                        else None
                    ),
                }
                type_data["categories"].append(category_data)

            hierarchy_data.append(type_data)

        return Response(hierarchy_data)

    @action(detail=True, methods=["put"])
    def activate(self, request, pk=None):
        obj = self.get_object()
        obj.is_active = True
        obj.save()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=True, methods=["put"])
    def deactivate(self, request, pk=None):
        obj = self.get_object()
        obj.is_active = False
        obj.save()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
