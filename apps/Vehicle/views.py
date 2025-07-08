from django.http import request
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Vehicle, VehicleImages, VehicleDocuments
from .serializer import (
    VehicleSerializer,
    VehicleImageSerializer,
    VehicleDocumentSerializer,
    VehicleImageDetailSerializer,
    VehicleDocumentDetailSerializer,
)


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Vehicle instances.
    """

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        print("CREATE - Request data:", request.data)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        print("UPDATE - Request data:", request.data)
        return super().update(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Vehicle.objects.all()
        provider_id = self.request.query_params.get("provider", None)
        vehicle_type = self.request.query_params.get("type", None)
        is_active = self.request.query_params.get("active", None)
        registration = self.request.query_params.get("registration", None)
        driver_id = self.request.query_params.get("driver", None)

        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        if vehicle_type:
            queryset = queryset.filter(vehicle_type_id=vehicle_type)
        if is_active is not None:
            is_active_bool = is_active.lower() == "true"
            queryset = queryset.filter(is_active=is_active_bool)
        if registration:
            queryset = queryset.filter(registration__icontains=registration)
        if driver_id:
            queryset = queryset.filter(primary_driver_id=driver_id)

        return queryset

    @action(detail=True, methods=["get", "post"])
    def photos(self, request, pk=None):
        """Manage vehicle photos"""
        vehicle = self.get_object()

        if request.method == "GET":
            photos = VehicleImages.objects.filter(vehicle=vehicle).order_by("order")
            serializer = VehicleImageDetailSerializer(photos, many=True)
            return Response(serializer.data)

        elif request.method == "POST":
            print("PHOTOS POST - Request data:", request.data)
            # Check if we already have 5 photos
            existing_photos = VehicleImages.objects.filter(vehicle=vehicle).count()
            if existing_photos >= 5:
                return Response(
                    {"error": "Maximum 5 photos allowed per vehicle"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = VehicleImageDetailSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(vehicle=vehicle)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get", "post"])
    def documents(self, request, pk=None):
        """Manage vehicle documents"""
        vehicle = self.get_object()

        if request.method == "GET":
            documents = VehicleDocuments.objects.filter(vehicle=vehicle)
            serializer = VehicleDocumentDetailSerializer(documents, many=True)
            return Response(serializer.data)

        elif request.method == "POST":
            print("DOCUMENTS POST - Request data:", request.data)
            serializer = VehicleDocumentDetailSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(vehicle=vehicle)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    def update_availability(self, request, pk=None):
        """Update vehicle availability status"""
        vehicle = self.get_object()
        is_available = request.data.get("is_available")

        if is_available is not None:
            vehicle.is_available = is_available
            vehicle.save()
            serializer = self.get_serializer(vehicle)
            return Response(serializer.data)

        return Response(
            {"error": "is_available field is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["patch"])
    def update_location(self, request, pk=None):
        """Update vehicle location"""
        vehicle = self.get_object()
        location = request.data.get("location")

        if location:
            vehicle.location = location
            vehicle.last_location_update = timezone.now()
            vehicle.save()
            serializer = self.get_serializer(vehicle)
            return Response(serializer.data)

        return Response(
            {"error": "location field is required"}, status=status.HTTP_400_BAD_REQUEST
        )


class VehicleImageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing vehicle photos"""

    def create(self, request, *args, **kwargs):
        print("CREATE - Request data:", request.data)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        print("UPDATE - Request data:", request.data)
        return super().update(request, *args, **kwargs)

    queryset = VehicleImages.objects.all()
    serializer_class = VehicleImageDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = VehicleImages.objects.all()
        vehicle_id = self.request.query_params.get("vehicle", None)
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        return queryset


class VehicleDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing vehicle documents"""

    def create(self, request, *args, **kwargs):
        print("CREATE - Request data:", request.data)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        print("UPDATE - Request data:", request.data)
        return super().update(request, *args, **kwargs)

    queryset = VehicleDocuments.objects.all()
    serializer_class = VehicleDocumentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = VehicleDocuments.objects.all()
        vehicle_id = self.request.query_params.get("vehicle", None)
        document_type = self.request.query_params.get("type", None)

        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        return queryset
