from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import Job
from .serializers import JobSerializer
from apps.Request.models import Request
from apps.Bidding.models import Bid
from apps.Bidding.serializers import BidSerializer
from apps.Request.views import RequestViewSet

# Create your views here.


class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]
    queryset = Job.objects.all()

    def get_queryset(self):
        user = self.request.user
        queryset = Job.objects.all()

        # Add filters based on query parameters
        status_filter = self.request.query_params.get("status", None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # If user parameter is specified, override default user filtering
        user_filter = self.request.query_params.get("user_filter", "on")
        if user_filter.lower() == "off":
            return queryset.order_by("-created_at")

        try:
            if hasattr(user, "provider"):
                # For debugging purposes, let's see all jobs by default
                # but still allow filtering with query parameters
                provider_filter = self.request.query_params.get(
                    "provider_filter", "all"
                )

                if provider_filter == "unbid":
                    # Original logic: only jobs they haven't bid on
                    return (
                        queryset.filter(
                            status="active", bidding_end_time__gt=timezone.now()
                        )
                        .exclude(bids__provider=user.provider)
                        .order_by("-created_at")
                    )
                else:
                    # Show all jobs
                    return queryset.order_by("-created_at")
            else:
                # Customers see their own jobs by default
                # But can be overridden with query params
                customer_filter = self.request.query_params.get(
                    "customer_filter", "own"
                )

                if customer_filter == "own":
                    return queryset.filter(request__user=user).order_by("-created_at")
                else:
                    return queryset.order_by("-created_at")
        except Exception as e:
            print(f"Error in JobViewSet.get_queryset: {str(e)}")
            # If there's any error, show all jobs for debugging
            return Job.objects.all()

    def perform_create(self, serializer):
        request_id = self.request.data.get("request")
        request = Request.objects.get(id=request_id)

    @action(detail=True, methods=["post"])
    def accept_bid(self, request, pk=None):
        job = self.get_object()
        bid_id = request.data.get("bid_id")

        if not bid_id:
            return Response(
                {"error": "Bid ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            bid = Bid.objects.get(id=bid_id, job=job)
        except Bid.DoesNotExist:
            return Response(
                {"error": "Bid not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if job.request.customer != request.user:
            return Response(
                {"error": "Only the job owner can accept bids"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Update job and bid status
        job.status = "assigned"
        job.save()

        bid.status = "accepted"
        bid.save()

        # Reject all other bids
        Bid.objects.filter(job=job, status="pending").exclude(id=bid_id).update(
            status="rejected"
        )

        return Response(
            {"message": "Bid accepted successfully"}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def confirm_price(self, request, pk=None):
        job = self.get_object()
        try:
            staff_count = request.data.get("staff_count")
            total_price = request.data.get("total_price")
            price_breakdown = request.data.get("price_breakdown", {})

            if not staff_count or not total_price:
                return Response(
                    {"error": "Staff count and total price are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get the request object from the job
            request_obj = job.request

            # Update request with price details
            request_obj.staff_count = staff_count
            request_obj.base_price = total_price
            request_obj.final_price = total_price
            request_obj.price_breakdown = price_breakdown
            request_obj.save()

            # Submit the request using the RequestViewSet's submit endpoint
            request_viewset = RequestViewSet()
            request_viewset.request = request
            return request_viewset.submit(request, pk=request_obj.id)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class JobBidViewSet(viewsets.ModelViewSet):
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated]
    queryset = Bid.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_provider:
            return Bid.objects.filter(provider=user.provider)
        else:
            return Bid.objects.filter(job__request__customer=user)

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user.provider)
