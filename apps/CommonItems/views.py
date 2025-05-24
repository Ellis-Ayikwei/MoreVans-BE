from django.shortcuts import render
from .models import ItemCategory, CommonItem
from .serializers import ItemCategorySerializer, CommonItemSerializer
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action


class ItemCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing ItemCategory instances.
    """

    queryset = ItemCategory.objects.all()
    serializer_class = ItemCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ItemCategory.objects.all()
        requires_special_handling = self.request.query_params.get(
            "special_handling", None
        )
        restricted = self.request.query_params.get("restricted", None)

        if requires_special_handling is not None:
            requires_special_handling_bool = requires_special_handling.lower() == "true"
            queryset = queryset.filter(
                requires_special_handling=requires_special_handling_bool
            )
        if restricted is not None:
            restricted_bool = restricted.lower() == "true"
            queryset = queryset.filter(restricted=restricted_bool)

        return queryset


class CommonItemViewset(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing CommonItem instances.
    """

    queryset = CommonItem.objects.all()
    serializer_class = CommonItemSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = CommonItem.objects.all()
        category_id = self.request.query_params.get("category", None)
        category_name = self.request.query_params.get("category_name", None)
        fragile = self.request.query_params.get("fragile", None)
        needs_disassembly = self.request.query_params.get("needs_disassembly", None)

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        if category_name:
            queryset = queryset.filter(category__name__iexact=category_name)

        if fragile is not None:
            fragile_bool = fragile.lower() == "true"
            queryset = queryset.filter(fragile=fragile_bool)

        if needs_disassembly is not None:
            needs_disassembly_bool = needs_disassembly.lower() == "true"
            queryset = queryset.filter(needs_disassembly=needs_disassembly_bool)

        return queryset

    @action(detail=False, methods=["get"])
    def categories_with_items(self, request):
        """
        Get all categories with their associated common items.
        """
        categories = ItemCategory.objects.all()
        result = []

        for category in categories:
            items = CommonItem.objects.filter(category=category)

            category_data = {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "icon": category.icon,
                "color": category.color,
                "tab_color": category.tab_color,
                "items": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "dimensions": item.dimensions,
                        "weight": item.weight,
                        "needs_disassembly": item.needs_disassembly,
                        "fragile": item.fragile,
                    }
                    for item in items
                ],
            }

            result.append(category_data)

        return Response(result)

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Search common items by name.
        """
        search_term = request.query_params.get("q", "")
        if not search_term:
            return Response([])

        items = CommonItem.objects.filter(name__icontains=search_term)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
