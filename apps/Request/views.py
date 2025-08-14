import json
import sys
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Request
from .serializer import (
    RequestSerializer,
    RequestItemSerializer,
    ItemCategorySerializer,
    CommonItemSerializer,
)
from apps.pricing.views import PricingConfigurationViewSet
from apps.pricing.serializers import (
    PriceCalculationSerializer,
    DateBasedPriceCalculationSerializer,
)
from apps.pricing.models import PricingConfiguration
import logging
from datetime import date, timedelta
from apps.Job.services import JobTimelineService
from .utils import get_request_forecast_data
from apps.JourneyStop.views import JourneyStopViewSet
from apps.JourneyStop.models import JourneyStop
from apps.Location.models import Location
from apps.RequestItems.models import RequestItem
from apps.CommonItems.models import ItemCategory
import os
import requests
from apps.Location.services import get_distance_and_travel_time


class RequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Request instances.
    """

    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get_queryset(self):
        queryset = Request.objects.all()
        user_id = self.request.query_params.get("user_id", None)
        driver_id = self.request.query_params.get("driver", None)
        status_param = self.request.query_params.get("status", None)
        request_type = self.request.query_params.get("type", None)

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
        if status_param:
            queryset = queryset.filter(status=status_param)
        if request_type:
            queryset = queryset.filter(request_type=request_type)

        return queryset

    @action(detail=False, methods=["get"])
    def drafts(self, request):
        """Get all draft requests for a user"""
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response(
                {"detail": "user_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        drafts = Request.objects.filter(user_id=user_id, status="draft")
        serializer = self.get_serializer(drafts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Submit a draft request for processing"""
        # Create a job based on the request
        from Job.models import Job
        from Job.serializers import JobSerializer
        import uuid

        print("Request endpoint accessed")
        sys.stdout.flush()
        request_obj = self.get_object()

        # Debug information
        print(f"Request object ID: {request_obj.id}")
        print(f"Request object type: {type(request_obj.id)}")
        sys.stdout.flush()

        # Check if request is in draft status
        if request_obj.status != "draft":
            return Response(
                {"error": "Only draft requests can be submitted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Submit the request (this will trigger the pricing calculation)
            request_obj.submit()

            # Print the price in yellow
            print(
                "\033[93m" + f"Request Price: £{request_obj.base_price:.2f}" + "\033[0m"
            )
            if request_obj.price_breakdown:
                print("\033[93m" + "Price Breakdown:" + "\033[0m")
                for key, value in request_obj.price_breakdown.items():
                    print("\033[93m" + f"  {key}: £{value:.2f}" + "\033[0m")

            # Replace with simple randomizer (50% chance of being instant)
            import random

            is_instant = random.choice([True, False])

            print(
                "\033[93m"
                + f"Request Type: {'Instant' if is_instant else 'Bidding'}"
                + "\033[0m"
            )

            # Get location information from journey stops
            pickup_stops = request_obj.stops.filter(type="pickup").first()
            dropoff_stops = request_obj.stops.filter(type="dropoff").first()

            pickup_city = "Unknown location"
            dropoff_city = "Unknown location"

            if pickup_stops and pickup_stops.location:
                pickup_city = pickup_stops.location.address

            if dropoff_stops and dropoff_stops.location:
                dropoff_city = dropoff_stops.location.address

            title = f"Move from {pickup_city} to {dropoff_city}"
            description = "Moving request"

            if request_obj.total_weight:
                description = f"Moving {request_obj.total_weight}kg of items"

            # Ensure request_id is a string representation of the UUID
            request_id = str(request_obj.id)

            job_data = {
                "request_id": request_id,
                "title": title,
                "description": description,
                "status": "open",
                "is_instant": is_instant,
                "minimum_bid": request_obj.base_price * (0.8 if is_instant else 0.6),
                "base_price": request_obj.base_price,
            }

            # Debug information
            print(f"Job data to be sent: {job_data}")
            sys.stdout.flush()

            job_serializer = JobSerializer(data=job_data)
            if job_serializer.is_valid():
                job = job_serializer.save()
                JobTimelineService.create_timeline_event(
                    job=job,
                    event_type="created",
                    created_by=request_obj.user,
                )

                return Response(
                    {
                        "message": "Request submitted successfully",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                print(f"Serializer errors: {job_serializer.errors}")
                sys.stdout.flush()
                return Response(
                    job_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

        except ValueError as e:
            print(f"ValueError: {str(e)}")
            sys.stdout.flush()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Exception: {str(e)}")
            import traceback

            print(traceback.format_exc())
            sys.stdout.flush()
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_estimated_duration(self, obj):
        """Return estimated duration in human-readable format"""
        if obj.estimated_duration:
            total_seconds = int(obj.estimated_duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return None

    def create(self, request, *args, **kwargs):
        """Create a new request in draft status with minimal data"""

        try:
            # Create a mutable copy of the data
            data = request.data.copy()
            print("Creating request with data:", json.dumps(data, indent=4))
            data["status"] = "draft"

            # Create the request using serializer
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            print("serializer clean about to save", serializer.validated_data)
            instance = serializer.save()

            # --- New logic: update estimated distance/time/fuel if locations are present ---
            stops = instance.stops.order_by("sequence").select_related("location")
            locations = [
                s.location
                for s in stops
                if s.location and s.location.latitude and s.location.longitude
            ]
            if len(locations) >= 2:
                try:
                    result = get_distance_and_travel_time(locations)
                    print(f"[Request] Distance API result: {result}")
                    distance_miles = result["distance"]  # Already in miles
                    duration_sec = result["duration"]
                    fuel_used = result["estimated_fuel_liters"]
                    instance.estimated_distance = distance_miles
                    instance.estimated_fuel_consumption = fuel_used
                    instance.estimated_duration = timedelta(seconds=duration_sec)
                    if (
                        hasattr(instance, "preferred_pickup_date")
                        and instance.preferred_pickup_date
                    ):
                        from datetime import datetime
                        from django.utils import timezone

                        start_dt = datetime.combine(
                            instance.preferred_pickup_date, datetime.min.time()
                        )
                        instance.estimated_completion_time = start_dt + timedelta(
                            seconds=duration_sec
                        )
                    else:
                        from django.utils import timezone

                        instance.estimated_completion_time = timezone.now() + timedelta(
                            seconds=duration_sec
                        )
                    instance.save(
                        update_fields=[
                            "estimated_distance",
                            "estimated_fuel_consumption",
                            "estimated_duration",
                            "estimated_completion_time",
                        ]
                    )
                except Exception as e:
                    print(f"OpenRouteService error: {e}")

            # Return the essential data
            return Response(
                {
                    "message": "Request created successfully",
                    "request_id": instance.id,
                    "tracking_number": instance.tracking_number,
                    "estimated_distance": (
                        round(instance.estimated_distance, 2)
                        if instance.estimated_distance
                        else None
                    ),
                    "estimated_duration": self.get_estimated_duration(instance),
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def confirm_as_job(self, request, pk=None):
        try:
            print("Confirming request as a job...", request.data)
            data = request.data
            instance = self.get_object()
            price = data.get("price")
            minimum_bid = data.get("minimum_bid")
            is_instant = data.get("is_biddable")
            # Check if request can be confirmed as job
            if instance.status == "cancelled":
                return Response(
                    {"error": "Cannot confirm cancelled request as job"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif (
                instance.status == "confirmed"
                and hasattr(instance, "job")
                and instance.job
            ):
                return Response(
                    {"error": "Cannot confirm an already confirmed job"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Use strategy-based job creation
            from apps.Job.services import JobService

            # Seed base price if provided so strategy uses it
            if price is not None:
                instance.base_price = price
                instance.save(update_fields=["base_price"])
            job = JobService.create_job_with_strategy(instance)

            # Update request status to indicate job has been created
            instance.status = "confirmed"
            instance.save()

            return Response(
                {
                    "message": "Request confirmed as a job successfully",
                    "job_id": job.id,
                    "request_id": instance.id,
                    "job_title": job.title,
                    "is_instant": job.is_instant,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _create_journey_stops(self, instance, journey_stops, request):
        """Helper method to create journey stops - now uses serializer's logic"""
        print(
            "Creating journey stops for request ID:",
            instance.id,
            "with stops:",
            json.dumps(journey_stops, indent=4),
        )

        # Use the serializer's _process_journey_stop method
        serializer = self.get_serializer(instance)
        for idx, stop_data in enumerate(journey_stops):
            serializer._process_journey_stop(instance, stop_data, idx)

        return instance.stops.all().order_by("sequence")

    @action(detail=True, methods=["post", "put"])
    def submit_step1(self, request, pk=None):
        """Handle step 1 submission (Contact Details)"""
        try:
            print("Step 1 submission:", json.dumps(request.data, indent=4))

            # Get or create request instance
            instance = None
            if request.method == "PUT":
                request_id = request.data.get("request_id")
                if request_id:
                    instance = get_object_or_404(Request, id=request_id)
                    data = request.data.copy()
                    data["status"] = "draft"
                    serializer = self.get_serializer(instance, data=data, partial=True)
                else:
                    return Response(
                        {"error": "Request ID is required for updates"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                data = request.data.copy()
                data["status"] = "draft"
                serializer = self.get_serializer(data=data)

            serializer.is_valid(raise_exception=True)
            instance = serializer.save()

            # Handle journey stops if present
            journey_stops = request.data.get("journey_stops", [])
            if journey_stops:
                # Clear existing stops
                instance.stops.all().delete()
                self._create_journey_stops(instance, journey_stops, request)

            return Response(
                {
                    "message": "Step 1 submitted successfully",
                    "request_id": instance.id,
                    "tracking_number": instance.tracking_number,
                },
                status=(
                    status.HTTP_201_CREATED
                    if request.method == "POST"
                    else status.HTTP_200_OK
                ),
            )
        except Exception as e:
            print(f"Step 1 error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post", "put", "patch"])
    def submit_step2(self, request, pk=None):
        """Handle step 2 submission (Locations)"""
        try:
            instance = self.get_object()
            data = request.data.copy()
            print("Step 2 submission:", json.dumps(data, indent=4))
            data["status"] = "draft"

            # Handle journey stops for both request types
            journey_stops = data.get("journey_stops", [])
            if journey_stops:
                # Clear existing stops
                instance.stops.all().delete()

                # For instant requests, remove items from stops in step 2
                if instance.request_type == "instant":
                    for stop in journey_stops:
                        stop.pop("items", None)

                # Create journey stops
                self._create_journey_stops(instance, journey_stops, request)

                # Update request data
                serializer = self.get_serializer(instance, data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()

            # --- Refactored: use get_distance_and_travel_time ---
            stops = instance.stops.order_by("sequence").select_related("location")
            locations = [
                s.location
                for s in stops
                if s.location and s.location.latitude and s.location.longitude
            ]
            if len(locations) >= 2:
                try:
                    result = get_distance_and_travel_time(locations)
                    print(f"[Request] Distance API result: {result}")
                    distance_miles = result["distance"]  # Already in miles
                    duration_sec = result["duration"]
                    fuel_used = result["estimated_fuel_liters"]
                    instance.estimated_distance = distance_miles
                    instance.estimated_fuel_consumption = fuel_used
                    instance.estimated_duration = timedelta(seconds=duration_sec)
                    instance.save(
                        update_fields=[
                            "estimated_distance",
                            "estimated_fuel_consumption",
                            "estimated_duration",
                        ]
                    )
                except Exception as e:
                    print(f"OpenRouteService error: {e}")

            return Response(
                {"message": "Step 2 submitted successfully", "request_id": instance.id},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(f"Step 2 error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post", "put", "patch"])
    def submit_step3(self, request, pk=None):
        """Handle step 3 submission (Service Details)"""
        print("Step 3 submission:", json.dumps(request.data, indent=4))
        try:
            # Get the request instance
            try:
                instance = self.get_object()
            except Request.DoesNotExist:
                print("Request not found")
                return Response(
                    {"error": "Request not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            data = request.data.copy()
            print("Step 3 submission:", json.dumps(data, indent=4))
            data["status"] = "draft"

            # Handle items based on request type
            if instance.request_type == "instant":
                # For instant requests, process moving_items in step 3
                moving_items = data.get("moving_items", [])
                if moving_items:
                    # Clear existing items first
                    instance.items.all().delete()

                    # Get pickup and dropoff stops
                    pickup_stop = instance.stops.filter(type="pickup").first()
                    dropoff_stop = instance.stops.filter(type="dropoff").first()

                    if not pickup_stop or not dropoff_stop:
                        return Response(
                            {
                                "error": "Pickup and dropoff locations not found. Please complete step 2 first."
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # Create request items
                    for item_data in moving_items:
                        # Get or create item category
                        category_name = item_data.get("category", "Other")
                        category, _ = ItemCategory.objects.get_or_create(
                            name=category_name
                        )

                        # Handle photos if present
                        photos = []
                        if item_data.get("photo"):
                            photos.append(item_data["photo"])

                        # Convert weight and value to decimal
                        try:
                            weight = (
                                float(item_data.get("weight", 0))
                                if item_data.get("weight")
                                else None
                            )
                        except (ValueError, TypeError):
                            weight = None

                        try:
                            declared_value = (
                                float(item_data.get("value", 0))
                                if item_data.get("value")
                                else None
                            )
                        except (ValueError, TypeError):
                            declared_value = None

                        # Create request item with correct field names
                        RequestItem.objects.create(
                            request=instance,
                            category=category,
                            name=item_data.get("name", ""),
                            description=item_data.get("description", ""),
                            quantity=item_data.get("quantity", 1),
                            weight=weight,
                            dimensions=item_data.get("dimensions", ""),
                            fragile=item_data.get("fragile", False),
                            needs_disassembly=item_data.get("needs_disassembly", False),
                            special_instructions=item_data.get(
                                "special_instructions", ""
                            ),
                            photos=photos,
                            declared_value=declared_value,
                            pickup_stop=pickup_stop,
                            dropoff_stop=dropoff_stop,
                        )

            else:
                # For journey requests, items are already handled in step 2 with stops
                # Remove moving_items from data for journey requests
                data.pop("moving_items", None)

            # Update request data
            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(
                {"message": "Step 3 submitted successfully", "request_id": instance.id},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(f"Step 3 error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post", "put", "patch"])
    def submit_step4(self, request, pk=None):
        """Handle step 4 submission (Schedule)"""
        from apps.pricing.services import PricingService

        try:
            instance = self.get_object()
            data = request.data.copy()
            print("Step 4 submission:", json.dumps(data, indent=4))
            data["status"] = "draft"

            # Update request data
            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            print("Serializer data to be saved:", serializer.validated_data)
            serializer.save()

            serializer.save()

            # --- Refactored: use get_distance_and_travel_time ---
            stops = instance.stops.order_by("sequence").select_related("location")
            locations = [
                s.location
                for s in stops
                if s.location and s.location.latitude and s.location.longitude
            ]
            if len(locations) >= 2:
                try:
                    result = get_distance_and_travel_time(locations)
                    print(f"[Request] Distance API result: {result}")
                    distance_miles = result["distance"]  # Already in miles
                    duration_sec = result["duration"]
                    fuel_used = result["estimated_fuel_liters"]
                    instance.estimated_distance = distance_miles
                    instance.estimated_fuel_consumption = fuel_used
                    instance.estimated_duration = timedelta(seconds=duration_sec)
                    instance.save(
                        update_fields=[
                            "estimated_distance",
                            "estimated_fuel_consumption",
                            "estimated_duration",
                        ]
                    )
                except Exception as e:
                    print(f"OpenRouteService error: {e}")

            # Get forecast data from the complete request object
            forecast_data = get_request_forecast_data(instance)

            # Calculate price forecast
            forecast_response = PricingService.calculate_price_forecast(forecast_data)

            return Response(
                {
                    "message": "Step 4 submitted successfully",
                    "request_id": instance.id,
                    "price_forecast": forecast_response.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(f"Step 4 error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a request."""
        req = self.get_object()

        # Check if request can be cancelled
        if req.status in ["completed", "cancelled"]:
            return Response(
                {"detail": f"Cannot cancel a request with status '{req.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get cancellation reason if provided
        reason = request.data.get("reason", "")
        req.cancellation_reason = reason
        req.cancellation_time = timezone.now()

        # Calculate cancellation fee if applicable
        if req.status in ["accepted", "in_transit"]:
            # Example: 10% of base price
            if req.base_price:
                req.cancellation_fee = req.base_price * 0.10

        # Update status to cancelled
        req.update_status("cancelled")

        serializer = self.get_serializer(req)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def adjust_price(self, request, pk=None):
        """Adjust the price of a request."""
        req = self.get_object()
        new_price = request.data.get("price", None)
        if new_price is None:
            return Response(
                {"detail": "Price is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        req.final_price = new_price
        req.save()

        serializer = self.get_serializer(req)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        """Update the status of a request."""
        req = self.get_object()
        new_status = request.data.get("status", None)

        if not new_status:
            return Response(
                {"detail": "Status is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        req.update_status(new_status)
        serializer = self.get_serializer(req)
        return Response("Request status updated successfully")

    @action(detail=True, methods=["post"])
    def assign_driver(self, request, pk=None):
        """Assign a driver to a request."""
        req = self.get_object()
        driver_id = request.data.get("driver_id", None)

        if not driver_id:
            return Response(
                {"detail": "Driver ID is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Assign driver to request
        req.driver_id = driver_id
        req.save()

        serializer = self.get_serializer(req)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def tracking(self, request, pk=None):
        """Get tracking information for a request."""
        req = self.get_object()

        # Get tracking updates
        tracking_updates = req.trackingupdate_set.all().order_by("-created_at")

        # Build response data
        data = {
            "request_id": req.id,
            "tracking_number": req.tracking_number,
            "status": req.status,
            "created_at": req.created_at,
            "pickup_date": req.preferred_pickup_date,
            "estimated_completion": req.estimated_completion_time,
            "updates": [
                {
                    "timestamp": update.created_at,
                    "type": update.update_type,
                    "message": update.status_message,
                    "location": update.location.name if update.location else None,
                }
                for update in tracking_updates
            ],
        }

        return Response(data)

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        """Get a summary of the request including items, pickup and dropoff details."""
        req = self.get_object()

        items = RequestItemSerializer(req.items.all(), many=True).data

        data = {
            "request": self.get_serializer(req).data,
            "items": items,
        }

        return Response(data)

    @action(detail=True, methods=["post"])
    def accept_price(self, request, pk=None):
        """Accept a price for a request."""
        req = self.get_object()
        print("Accept price request data:", request.data)

        # Get the price and staff count from the request
        price = request.data.get("total_price")
        staff_count = request.data.get("staff_count")
        selected_date = request.data.get("selected_date")

        if not all([price, staff_count, selected_date]):
            return Response(
                {"error": "Price, staff count, and selected date are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Convert selected_date string to datetime.date object
            from datetime import datetime

            selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            # Calculate the base price using our pricing function
            base_price = req.calculate_base_price()

            # Update the request with the accepted price and staff count
            req.final_price = price
            req.staff_required = staff_count
            req.preferred_pickup_date = selected_date
            req.base_price = base_price
            req.status = "accepted"
            req.save()

            return Response(
                {
                    "message": "Price accepted successfully",
                    "request_id": req.id,
                    "final_price": req.final_price,
                    "staff_count": req.staff_required,
                    "selected_date": req.preferred_pickup_date,
                }
            )

        except ValueError as e:
            return Response(
                {"error": f"Invalid date format. Expected YYYY-MM-DD: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _update_journey_stops(self, instance, journey_stops, request):
        """Helper method to update journey stops"""
        print(
            "Updating journey stops for request ID:",
            instance.id,
            "with stops:",
            json.dumps(journey_stops, indent=4),
        )

        # Get existing stops
        existing_stops = list(instance.stops.all().order_by("sequence"))

        for idx, stop_data in enumerate(journey_stops):
            print("Processing stop:", stop_data)

            # Get or create location
            if idx < len(existing_stops):
                # Update existing location
                location = existing_stops[idx].location
                location.address = stop_data.get("address", location.address)
                location.address_line1 = stop_data.get(
                    "address_line1", location.address_line1
                )
                location.address_line2 = stop_data.get(
                    "address_line2", location.address_line2
                )
                location.city = stop_data.get("city", location.city)
                location.county = stop_data.get("county", location.county)
                location.postcode = stop_data.get("postcode", location.postcode)
                location.contact_name = stop_data.get(
                    "contact_name", location.contact_name
                )
                location.contact_phone = stop_data.get(
                    "contact_phone", location.contact_phone
                )
                location.use_main_contact = stop_data.get(
                    "use_main_contact", location.use_main_contact
                )
                location.save()

                # Update existing journey stop
                journey_stop = existing_stops[idx]
                journey_stop.type = stop_data.get("type", journey_stop.type)
                journey_stop.sequence = idx
                journey_stop.save()
            else:
                # Create new location and stop if we have more stops than existing ones
                location = Location.objects.create(
                    address=stop_data.get("address", ""),
                    address_line1=stop_data.get("address_line1", ""),
                    address_line2=stop_data.get("address_line2", ""),
                    city=stop_data.get("city", ""),
                    county=stop_data.get("county", ""),
                    postcode=stop_data.get("postcode", ""),
                    contact_name=stop_data.get("contact_name", ""),
                    contact_phone=stop_data.get("contact_phone", ""),
                    use_main_contact=stop_data.get("use_main_contact", True),
                )

                JourneyStop.objects.create(
                    request=instance,
                    location=location,
                    type=stop_data.get("type", "pickup"),
                    sequence=idx,
                )

        # Delete any extra stops that are no longer needed
        if len(existing_stops) > len(journey_stops):
            for stop in existing_stops[len(journey_stops) :]:
                stop.delete()

        return instance.stops.all().order_by("sequence")

    @action(detail=True, methods=["post"])
    def update_details(self, request, pk=None):
        """Update request details"""
        try:
            instance = self.get_object()

            # Update basic request details
            instance.contact_name = request.data.get(
                "contact_name", instance.contact_name
            )
            instance.contact_email = request.data.get(
                "contact_email", instance.contact_email
            )
            instance.contact_phone = request.data.get(
                "contact_phone", instance.contact_phone
            )
            instance.request_type = request.data.get(
                "request_type", instance.request_type
            )
            instance.staff_required = request.data.get(
                "staff_count", instance.staff_required
            )
            instance.user_id = request.data.get("user_id", instance.user_id)

            # Handle journey stops if present
            journey_stops = request.data.get("journey_stops", [])
            if journey_stops:
                self._update_journey_stops(instance, journey_stops, request)

            instance.save()
            return Response(
                self.get_serializer(instance).data, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def update_staff_count(self, request, pk=None):
        """Update staff count for a request"""
        try:
            request_obj = self.get_object()
            request_obj.staff_required = request.data.get(
                "staff_count", request_obj.staff_required
            )
            request_obj.save()

            return Response(
                self.get_serializer(request_obj).data, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def reconcile_statuses(self, request):
        """
        Reconcile request statuses by checking payments and jobs.
        This endpoint requires admin privileges.

        POST /api/requests/reconcile_statuses/
        {
            "date_from": "YYYY-MM-DD",  // optional
            "date_to": "YYYY-MM-DD",    // optional
            "status": "status_name",     // optional
            "poll_payments": true        // optional, default false
        }

        Returns:
            Response with reconciliation summary
        """
        # Check if user has admin privileges
        if not request.user.is_staff:
            return Response(
                {"error": "Only admin users can reconcile statuses"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Get filter parameters
            date_from = request.data.get("date_from")
            date_to = request.data.get("date_to")
            status_filter = request.data.get("status")
            poll_payments = request.data.get("poll_payments", False)

            # Log the start of reconciliation
            print(f"Starting status reconciliation by {request.user.email}")
            print(
                f"Filters - Date from: {date_from}, Date to: {date_to}, Status: {status_filter}"
            )
            print(f"Poll payments: {poll_payments}")

            # Initialize Stripe service if polling is requested
            stripe_service = None
            if poll_payments:
                from apps.Payment.stripe_service import StripeService

                stripe_service = StripeService()

            # Call the reconciliation method
            summary = Request.reconcile_statuses(
                date_from=date_from,
                date_to=date_to,
                status_filter=status_filter,
                stripe_service=stripe_service if poll_payments else None,
            )

            # Prepare the response
            response_data = {
                "message": "Reconciliation completed successfully",
                "summary": {
                    "total_requests_checked": summary["total_checked"],
                    "updates": {
                        "status_updates": summary["status_updated"],
                        "payment_fixes": summary["payment_fixed"],
                        "jobs_created": summary["jobs_created"],
                        "payments_polled": summary.get("payments_polled", 0),
                    },
                    "total_fixes": (
                        summary["status_updated"]
                        + summary["payment_fixed"]
                        + summary["jobs_created"]
                    ),
                    "error_count": len(summary["errors"]),
                },
                "details": summary["details"],
                "errors": summary["errors"] if summary["errors"] else None,
            }

            # Log completion
            print(
                f"Reconciliation completed - {response_data['summary']['total_fixes']} fixes applied"
            )
            if poll_payments:
                print(f"Payments polled: {summary.get('payments_polled', 0)}")

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = f"Error during reconciliation: {str(e)}"
            print(error_message)
            return Response(
                {
                    "error": error_message,
                    "message": "Failed to complete reconciliation",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def create_job_from_payments(self, request, pk=None):
        """
        Manually create a job from completed payments for this request

        POST /api/requests/{request_id}/create_job_from_payments/
        """
        request_obj = self.get_object()

        try:
            job = request_obj.get_or_create_job_from_payments()

            if job:
                from apps.Job.serializers import JobSerializer

                job_serializer = JobSerializer(job)

                return Response(
                    {
                        "success": True,
                        "message": f"Job created successfully for request {request_obj.id}",
                        "job": job_serializer.data,
                        "request_status": request_obj.status,
                        "payment_status": request_obj.payment_status,
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {
                        "success": False,
                        "message": "No completed payments found for this request",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Error creating job from payments for request {request_obj.id}: {str(e)}"
            )

            return Response(
                {"success": False, "error": f"Failed to create job: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def bulk_create_jobs_from_payments(self, request):
        """
        Bulk create jobs from payments for multiple requests

        POST /api/requests/bulk_create_jobs_from_payments/
        {
            "request_ids": [1, 2, 3],  // optional - if not provided, processes all requests with completed payments
            "force_create": false       // optional - force create even if job exists
        }
        """
        from apps.Payment.models import Payment
        from apps.Job.models import Job

        request_ids = request.data.get("request_ids", [])
        force_create = request.data.get("force_create", False)

        try:
            # Get requests to process
            if request_ids:
                requests_to_process = Request.objects.filter(id__in=request_ids)
            else:
                # Get all requests that have completed payments but no jobs
                requests_with_payments = Request.objects.filter(
                    payments__status="completed"
                ).distinct()

                requests_to_process = []
                for req in requests_with_payments:
                    if not Job.objects.filter(request=req).exists():
                        requests_to_process.append(req)

            results = []
            jobs_created = 0
            errors = 0

            for request_obj in requests_to_process:
                try:
                    # Check if job already exists
                    existing_job = Job.objects.filter(request=request_obj).first()

                    if existing_job and not force_create:
                        results.append(
                            {
                                "request_id": request_obj.id,
                                "success": False,
                                "message": "Job already exists",
                                "existing_job_id": existing_job.id,
                            }
                        )
                        continue

                    # Create job
                    job = request_obj.get_or_create_job_from_payments()

                    if job:
                        jobs_created += 1
                        results.append(
                            {
                                "request_id": request_obj.id,
                                "success": True,
                                "job_id": job.id,
                                "job_number": job.job_number,
                                "message": "Job created successfully",
                            }
                        )
                    else:
                        errors += 1
                        results.append(
                            {
                                "request_id": request_obj.id,
                                "success": False,
                                "message": "No completed payments found",
                            }
                        )

                except Exception as e:
                    errors += 1
                    results.append(
                        {
                            "request_id": request_obj.id,
                            "success": False,
                            "error": str(e),
                        }
                    )

            return Response(
                {
                    "success": True,
                    "summary": {
                        "total_requests_processed": len(requests_to_process),
                        "jobs_created": jobs_created,
                        "errors": errors,
                    },
                    "results": results,
                    "message": f"Bulk job creation completed: {jobs_created} jobs created, {errors} errors",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error in bulk job creation: {str(e)}")

            return Response(
                {"success": False, "error": f"Bulk job creation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
