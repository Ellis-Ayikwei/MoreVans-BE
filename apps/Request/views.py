import json
import sys
from django.shortcuts import render
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


class RequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Request instances.
    """

    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.AllowAny]

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

    # def create(self, request, *args, **kwargs):
    #     """
    #     Create a request and return the two-month price forecast with staff prices for each day.
    #     """
    #     from pricing.services import PricingService
    #     import logging

    #     logger = logging.getLogger(__name__)

    #     # Create a mutable copy of the data
    #     data = request.data.copy()

    #     # Set the user to the current authenticated user
    #     data["user"] = request.user.id

    #     # Set initial status to draft
    #     data["status"] = "draft"

    #     # Remove tracking_number if provided, as we'll generate it
    #     if "tracking_number" in data:
    #         del data["tracking_number"]

    #     # Create request with the modified data
    #     serializer = self.get_serializer(data=data)
    #     serializer.is_valid(raise_exception=True)

    #     # Save the request first so we have an ID
    #     instance = serializer.save()

    #     # Generate tracking number and booking code
    #     instance.tracking_number = instance.generate_tracking_number()
    #     instance.booking_code = instance.generate_booking_code()
    #     instance.save()

    #     # Prepare data for price forecast
    #     forecast_data = {
    #         "distance": float(data.get("estimated_distance", 0)),
    #         "weight": float(data.get("total_weight", 0)),
    #         "service_level": data.get("service_level", "standard"),
    #         "property_type": data.get("property_type", "other"),
    #         "number_of_rooms": data.get("number_of_rooms", 1),
    #         "floor_number": data.get("floor_number", 0),
    #         "has_elevator": data.get("has_elevator", False),
    #         "loading_time": data.get("loading_time"),
    #         "unloading_time": data.get("unloading_time"),
    #         "vehicle_type": data.get("vehicle_type", "van"),
    #         "pickup_city": data.get("pickup_city"),
    #         "dropoff_city": data.get("dropoff_city"),
    #         "request_id": instance.id,  # Include the request ID in the forecast data
    #     }

    #     # Use the pricing service to calculate price forecast
    #     forecast_response = PricingService.calculate_price_forecast(forecast_data)

    #     if forecast_response.status_code != 200:
    #         logger.error(f"Forecast calculation failed: {forecast_response.data}")
    #         return Response(
    #             {
    #                 "error": "Failed to calculate price forecast",
    #                 "message": "Price calculation failed",
    #             },
    #             status=status.HTTP_400_BAD_REQUEST,
    #         )

    #     # Get the serialized request data
    #     response_data = self.get_serializer(instance).data

    #     # Add the price forecast to the response
    #     response_data["price_forecast"] = forecast_response.data

    #     return Response(response_data, status=status.HTTP_201_CREATED)

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

            # Make sure we have a valid title and description
            title = "Move request"
            description = "Moving request"

            if hasattr(request_obj, "pickup_location") and request_obj.pickup_location:
                if (
                    hasattr(request_obj.pickup_location, "city")
                    and request_obj.pickup_location.city
                ):
                    pickup_city = request_obj.pickup_location.city
                else:
                    pickup_city = "Unknown location"
            else:
                pickup_city = "Unknown location"

            if (
                hasattr(request_obj, "dropoff_location")
                and request_obj.dropoff_location
            ):
                if (
                    hasattr(request_obj.dropoff_location, "city")
                    and request_obj.dropoff_location.city
                ):
                    dropoff_city = request_obj.dropoff_location.city
                else:
                    dropoff_city = "Unknown location"
            else:
                dropoff_city = "Unknown location"

            title = f"Move from {pickup_city} to {dropoff_city}"

            if request_obj.total_weight:
                description = f"Moving {request_obj.total_weight}kg of items"

            # Ensure request_id is a string representation of the UUID
            request_id = str(request_obj.id)

            job_data = {
                "request_id": request_id,  # Changed from "request" to "request_id" to match the serializer
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

                # Return a simplified response that doesn't access the related bids
                return Response(
                    {
                        "message": "Request submitted successfully",
                        # "job": {
                        #     "id": job.id,
                        #     "title": title,
                        #     #   "description": job.description,
                        #     "status": job.status,
                        #     "is_instant": job.is_instant,
                        #     "minimum_bid": job.minimum_bid,
                        #     "base_price": job.base_price,
                        #     "request_id": job.request_id,
                        # },
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                # Print serializer errors for debugging
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

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Cancel a request.
        """
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
    def update_status(self, request, pk=None):
        """
        Update the status of a request.
        """
        req = self.get_object()
        new_status = request.data.get("status", None)

        if not new_status:
            return Response(
                {"detail": "Status is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        req.update_status(new_status)
        serializer = self.get_serializer(req)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def assign_driver(self, request, pk=None):
        """
        Assign a driver to a request.
        """
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
        """
        Get tracking information for a request.
        """
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
        """
        Get a summary of the request including items, pickup and dropoff details.
        """
        req = self.get_object()

        items = RequestItemSerializer(req.items.all(), many=True).data
        pickup_schedules = PickupScheduleSerializer(
            PickupSchedule.objects.filter(request=req), many=True
        ).data
        dropoff_schedules = DropoffScheduleSerializer(
            DropoffSchedule.objects.filter(request=req), many=True
        ).data

        data = {
            "request": self.get_serializer(req).data,
            "items": items,
            "pickup_schedules": pickup_schedules,
            "dropoff_schedules": dropoff_schedules,
        }

        return Response(data)

    @action(detail=False, methods=["put"])
    def submit_step1(self, request):
        """Handle step 1 submission (Contact Details)"""
        try:
            data = request.data.copy()
            data["status"] = "draft"

            if request.method == "POST":
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                instance = serializer.save()
            else:  # PUT
                request_id = data.pop("request_id", None)
                if not request_id:
                    return Response(
                        {"error": "request_id is required for update"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                instance = self.get_queryset().get(id=request_id)
                serializer = self.get_serializer(instance, data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()

            return Response(
                {"message": "Step 1 submitted successfully", "request_id": instance.id},
                status=(
                    status.HTTP_201_CREATED
                    if request.method == "POST"
                    else status.HTTP_200_OK
                ),
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch", "put"])
    def submit_step2(self, request, pk=None):
        """Handle step 2 submission (Locations)"""
        try:
            if request.method == "patch":
                data = request.data.copy()
                data["status"] = "draft"
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                instance = serializer.save()
            else:  # PUT
                instance = self.get_object()
                serializer = self.get_serializer(
                    instance, data=request.data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

            return Response(
                {"message": "Step 2 submitted successfully", "request_id": instance.id},
                status=(
                    status.HTTP_201_CREATED
                    if request.method == "POST"
                    else status.HTTP_200_OK
                ),
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post", "put", "patch"])
    def submit_step3(self, request, pk=None):
        """Handle step 3 submission (Service Details)"""
        try:
            if request.method == "POST":
                data = request.data.copy()
                print("the third step", data)
                data["status"] = "draft"
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                instance = serializer.save()
            elif request.method == "PUT":
                instance = self.get_object()
                serializer = self.get_serializer(instance, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            else:  # PATCH
                instance = self.get_object()
                serializer = self.get_serializer(
                    instance, data=request.data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

            return Response(
                {"message": "Step 3 submitted successfully", "request_id": instance.id},
                status=(
                    status.HTTP_201_CREATED
                    if request.method == "POST"
                    else status.HTTP_200_OK
                ),
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post", "put", "patch"])
    def submit_step4(self, request, pk=None):
        """Handle step 4 submission (Schedule)"""
        from pricing.services import PricingService

        try:
            # Save the request data
            if request.method == "POST":
                data = request.data.copy()
                data["status"] = "draft"
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                instance = serializer.save()
            elif request.method == "PUT":
                instance = self.get_object()
                serializer = self.get_serializer(instance, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            else:  # PATCH
                instance = self.get_object()
                serializer = self.get_serializer(
                    instance, data=request.data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

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
                status=(
                    status.HTTP_201_CREATED
                    if request.method == "POST"
                    else status.HTTP_200_OK
                ),
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        """Create a new request in draft status with minimal data"""
        # Create a mutable copy of the data
        data = request.data.copy()

        # Set initial status to draft
        data["status"] = "draft"
        print("the initial data", data)
        # Set the user if authenticated
        if request.user and request.user.is_authenticated:
            data["user"] = request.user.id

        # Create serializer with the data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Generate tracking number if needed
        if not instance.tracking_number:
            instance.tracking_number = instance.generate_tracking_number()
            instance.save(update_fields=["tracking_number"])

        # Return just the essential data
        return Response(
            {
                "message": "Request created successfully",
                "request_id": instance.id,
                "tracking_number": instance.tracking_number,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def accept_price(self, request, pk=None):
        """
        Accept a price for a request.
        """
        req = self.get_object()
        print(" the request data ", request.data)
        
        # Get the price and staff count from the request
        price = request.data.get("total_price")
        staff_count = request.data.get("staff_count")
        selected_date = request.data.get("selected_date")
        
        if not all([price, staff_count, selected_date]):
            return Response(
                {"error": "Price, staff count, and selected date are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Convert selected_date string to datetime.date object
            from datetime import datetime
            selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            
            # Update the request with the accepted price and staff count
            req.final_price = price
            req.stuff_required = staff_count
            req.preferred_pickup_date = selected_date
            req.status = "accepted"
            req.save()
            
            return Response({
                "message": "Price accepted successfully",
                "request_id": req.id,
                "final_price": req.final_price,
                "staff_count": req.stuff_required,
                "selected_date": req.preferred_pickup_date
            })
            
        except ValueError as e:
            return Response(
                {"error": f"Invalid date format. Expected YYYY-MM-DD: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
