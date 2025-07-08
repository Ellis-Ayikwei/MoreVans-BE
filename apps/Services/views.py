from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db.models import Count, Q
from .models import ServiceCategory, Services
from .serializers import (
    ServiceCategorySerializer,
    ServiceCategoryDetailSerializer,
    ServiceCategoryCreateUpdateSerializer,
    ServiceListSerializer,
    ServiceDetailSerializer,
    ServiceCreateUpdateSerializer,
)


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ServiceCategory model.
    Provides CRUD operations for service categories.
    """

    queryset = ServiceCategory.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return ServiceCategorySerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ServiceCategoryCreateUpdateSerializer
        else:
            return ServiceCategoryDetailSerializer

    def get_queryset(self):
        queryset = ServiceCategory.objects.annotate(services_count=Count("services"))

        # Filter by services count if provided
        min_services = self.request.query_params.get("min_services", None)
        if min_services:
            queryset = queryset.filter(services_count__gte=int(min_services))

        return queryset

    @action(detail=True, methods=["get"])
    def services(self, request, pk=None):
        """Get all services for a specific category"""
        category = self.get_object()
        services = category.services.all()
        serializer = ServiceListSerializer(services, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["put"])
    def activate(self, request, pk=None):
        """Activate a service category"""
        category = self.get_object()
        category.is_active = True
        category.save()
        serializer = ServiceCategoryDetailSerializer(category)
        return Response(serializer.data)

    @action(detail=True, methods=["put"])
    def deactivate(self, request, pk=None):
        """Deactivate a service category"""
        category = self.get_object()
        category.is_active = False
        category.save()
        serializer = ServiceCategoryDetailSerializer(category)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def popular(self, request):
        """Get categories with most services"""
        categories = (
            ServiceCategory.objects.annotate(services_count=Count("services"))
            .filter(services_count__gt=0)
            .order_by("-services_count")[:10]
        )

        serializer = ServiceCategorySerializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def search(self, request):
        """Search categories by name or description"""
        query = request.query_params.get("q", "")
        if query:
            categories = ServiceCategory.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        else:
            categories = ServiceCategory.objects.all()

        serializer = ServiceCategorySerializer(categories, many=True)
        return Response(serializer.data)


class ServicesViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Services model.
    Provides CRUD operations for services.
    """

    queryset = Services.objects.select_related("service_category").prefetch_related(
        "providers"
    )
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return ServiceListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ServiceCreateUpdateSerializer
        else:
            return ServiceDetailSerializer

    def get_queryset(self):
        queryset = Services.objects.select_related("service_category").prefetch_related(
            "providers"
        )

        # Filter by category
        category_slug = self.request.query_params.get("category", None)
        if category_slug:
            queryset = queryset.filter(service_category__slug=category_slug)

        # Filter by providers count
        min_providers = self.request.query_params.get("min_providers", None)
        if min_providers:
            queryset = queryset.annotate(providers_count=Count("providers")).filter(
                providers_count__gte=int(min_providers)
            )

        return queryset

    @action(detail=True, methods=["get"])
    def providers(self, request, pk=None):
        """Get all providers for a specific service"""
        service = self.get_object()
        providers = service.providers.all()

        from apps.Provider.serializer import ServiceProviderSerializer

        serializer = ServiceProviderSerializer(providers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["put"])
    def activate(self, request, pk=None):
        """Activate a service"""
        service = self.get_object()
        service.is_active = True
        service.save()
        serializer = ServiceDetailSerializer(service)
        return Response(serializer.data)

    @action(detail=True, methods=["put"])
    def deactivate(self, request, pk=None):
        """Deactivate a service"""
        service = self.get_object()
        service.is_active = False
        service.save()
        serializer = ServiceDetailSerializer(service)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_category(self, request):
        """Get services grouped by category"""
        category_slug = request.query_params.get("category", None)
        if category_slug:
            services = Services.objects.filter(service_category__slug=category_slug)
        else:
            services = Services.objects.all()

        serializer = ServiceListSerializer(services, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def popular(self, request):
        """Get services with most providers"""
        services = (
            Services.objects.annotate(providers_count=Count("providers"))
            .filter(providers_count__gt=0)
            .order_by("-providers_count")[:10]
        )

        serializer = ServiceListSerializer(services, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def search(self, request):
        """Search services by name or description"""
        query = request.query_params.get("q", "")
        if query:
            services = Services.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        else:
            services = Services.objects.all()

        serializer = ServiceListSerializer(services, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        """Create multiple services at once"""
        serializer = ServiceCreateUpdateSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        """Create a new service with validation"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            service = serializer.save()
            response_serializer = ServiceDetailSerializer(service)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """Update a service with validation"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            service = serializer.save()
            response_serializer = ServiceDetailSerializer(service)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
