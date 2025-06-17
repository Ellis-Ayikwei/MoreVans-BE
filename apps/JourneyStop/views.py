import json
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import JourneyStop
from .serializers import JourneyStopSerializer
from apps.Request.models import Request
from apps.Location.models import Location


class JourneyStopViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing journey stops.
    Provides CRUD operations for journey stops and additional actions.
    """

    queryset = JourneyStop.objects.all()
    serializer_class = JourneyStopSerializer
    format_kwarg = "format"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = None
        self.format_kwarg = "format"

    def get_queryset(self):
        """
        Optionally filter stops by request_id if provided in query params
        """
        queryset = JourneyStop.objects.all()
        request_id = self.request.query_params.get("request_id", None)
        if request_id is not None:
            queryset = queryset.filter(request_id=request_id)
        return queryset.order_by("sequence")

    def create(self, request, *args, **kwargs):
        """
        Create a new journey stop with location data
        """
        print("creating with data", request.data)
        try:
            # Extract location data from request
            location_data = request.data.pop("location", None)
            if not location_data:
                return Response(
                    {"error": "Location data is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create or get location
            location = Location.objects.create(**location_data)

            # Create journey stop with location
            request.data["location"] = location.id
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Update a journey stop and its associated location
        """
        try:
            instance = self.get_object()
            location_data = request.data.pop("location", None)

            if location_data:
                # Update location
                location = instance.location
                for key, value in location_data.items():
                    setattr(location, key, value)
                location.save()

            # Update journey stop
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        """
        Create multiple journey stops at once
        """
        print("Hit the bulk create endpoint")
        try:
            stops_data = (
                request.data if isinstance(request.data, list) else [request.data]
            )
            created_stops = []

            for stop_data in stops_data:
                # Don't pop location data - let the serializer handle it
                serializer = self.get_serializer(data=stop_data)
                serializer.is_valid(raise_exception=True)
                created_stop = serializer.save()
                created_stops.append(created_stop)

            # Serialize the created stops with their locations
            response_data = self.get_serializer(created_stops, many=True).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Error in bulk_create: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        """
        Reorder journey stops for a request
        """
        try:
            request_id = request.data.get("request_id")
            stop_orders = request.data.get("stop_orders", [])

            if not request_id or not stop_orders:
                return Response(
                    {"error": "request_id and stop_orders are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Update sequence for each stop
            for order in stop_orders:
                stop = get_object_or_404(JourneyStop, id=order["stop_id"])
                stop.sequence = order["sequence"]
                stop.save()

            return Response({"message": "Stops reordered successfully"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        """
        Update the status of a journey stop
        """
        try:
            stop = self.get_object()
            new_status = request.data.get("status")

            if not new_status:
                return Response(
                    {"error": "status is required"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Update status and related fields
            if new_status == "completed":
                stop.completed_time = request.data.get("completed_time")
            elif new_status == "scheduled":
                stop.scheduled_time = request.data.get("scheduled_time")

            stop.save()
            return Response(self.get_serializer(stop).data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
