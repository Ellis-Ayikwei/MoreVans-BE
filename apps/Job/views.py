from django.shortcuts import render
from rest_framework import viewsets, status, permissions
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
from decimal import Decimal
from apps.Chat.utils import (
    create_job_conversation,
    get_or_create_conversation_for_object,
    add_system_message,
)

# Create your views here.


class JobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Job instances.
    """

    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Job.objects.all()
        status_param = self.request.query_params.get("status", None)
        is_instant = self.request.query_params.get("is_instant", None)
        provider = self.request.query_params.get("provider", None)

        if status_param:
            queryset = queryset.filter(status=status_param)
        if is_instant is not None:
            is_instant_bool = is_instant.lower() == "true"
            queryset = queryset.filter(is_instant=is_instant_bool)
        if provider:
            queryset = queryset.filter(provider_id=provider)

        return queryset

    def perform_create(self, serializer):
        request_id = self.request.data.get("request")
        request = Request.objects.get(id=request_id)

    @action(detail=True, methods=["post"])
    def make_biddable(self, request, pk=None):
        """
        Convert a job to a biddable job.

        Expected request body:
        {
            "bidding_duration_hours": 24,  # Optional, defaults to 24
            "minimum_bid": 100.00  # Optional
        }
        """
        job = self.get_object()

        try:
            bidding_duration_hours = int(request.data.get("bidding_duration_hours", 24))
            minimum_bid = request.data.get("minimum_bid")
            if minimum_bid:
                minimum_bid = Decimal(str(minimum_bid))

            job.make_biddable(
                bidding_duration_hours=bidding_duration_hours, minimum_bid=minimum_bid
            )

            return Response(
                {
                    "status": "success",
                    "message": "Job converted to biddable",
                    "job": JobSerializer(job).data,
                }
            )

        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def make_instant(self, request, pk=None):
        """
        Convert a job to an instant job.
        """
        job = self.get_object()

        try:
            job.make_instant()

            return Response(
                {
                    "status": "success",
                    "message": "Job converted to instant",
                    "job": JobSerializer(job).data,
                }
            )

        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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

        # if job.request.customer != request.user:
        #     return Response(
        #         {"error": "Only the job owner can accept bids"},
        #         status=status.HTTP_403_FORBIDDEN,
        #     )

        # assign provider to job
        job.assigned_provider = bid.provider
        job.save()

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

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        job = self.get_object()
        job.accept(request.user)
        return Response({"status": "Job accepted"})

    @action(detail=True, methods=["post"])
    def assign_provider(self, request, pk=None):
        """Assign a provider to a job"""
        from apps.Provider.models import ServiceProvider

        job = self.get_object()
        provider_id = request.data.get("provider_id")
        provider = ServiceProvider.objects.get(id=provider_id)
        job.assign_provider(provider)
        job.save()

        # Create or update job conversation
        try:
            conversation, created = get_or_create_conversation_for_object(job, "job")

            # Add provider to conversation if not already there
            if provider.user:
                conversation.add_participant(provider.user)

            # Add system message
            add_system_message(
                conversation,
                f"Provider {provider.company_name or provider.user.username} has been assigned to this job.",
                metadata={
                    "job_id": str(job.id),
                    "provider_id": str(provider.id),
                    "action": "provider_assigned",
                },
            )
        except Exception as e:
            print(f"Error creating job conversation: {e}")

        return Response({"status": "Provider assigned"})

    @action(detail=True, methods=["post"])
    def unassign_provider(self, request, pk=None):
        """Unassign a provider to a job"""
        from apps.Provider.models import ServiceProvider

        job = self.get_object()
        job.unassign_provider()
        job.save()
        return Response({"status": "Provider unassigned"})

    @action(detail=True, methods=["get"])
    def conversation(self, request, pk=None):
        """Get the chat conversation for a job"""
        job = self.get_object()
        user = request.user

        # Check if user has access to this job
        is_admin = user.is_staff or user.is_superuser
        is_job_owner = job.request.user == user
        is_assigned_provider = (
            job.assigned_provider
            and hasattr(job.assigned_provider, "user")
            and job.assigned_provider.user == user
        )

        if not (is_admin or is_job_owner or is_assigned_provider):
            return Response(
                {"error": "You don't have permission to view this conversation"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get or create conversation
        conversation, created = get_or_create_conversation_for_object(job, "job")

        if created:
            # Set up participants
            participants = []
            if job.request and job.request.user:
                participants.append(job.request.user)
            if job.assigned_provider and hasattr(job.assigned_provider, "user"):
                participants.append(job.assigned_provider.user)

            for participant in participants:
                conversation.add_participant(participant)

            # Add initial message
            add_system_message(
                conversation,
                f"Job conversation started for: {job.title or job.job_number}",
                metadata={"job_id": str(job.id), "action": "job_conversation_created"},
            )

        return Response(
            {
                "conversation_id": str(conversation.id),
                "conversation_type": conversation.conversation_type,
                "title": conversation.title,
                "created": created,
            }
        )

    @action(detail=False, methods=["get"])
    def bids(self, request, pk=None):
        job = self.get_object()
        bids = job.bids.all()
        return Response({"bids": BidSerializer(bids, many=True).data})

    @action(detail=True, methods=["post"])
    def add_bid(self, request, pk=None):
        """Add a bid to a job"""
        from apps.Provider.models import ServiceProvider

        job = self.get_object()
        user = request.user
        provider = ServiceProvider.objects.get(user=user)
        if not provider:
            return Response(
                {"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND
            )
        if job.status != "bidding":
            return Response(
                {"error": "Job is not in bidding status"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        bid = Bid.objects.create(
            job=job,
            provider=provider,
            amount=request.data.get("amount"),
            message=request.data.get("message"),
            status="pending",
        )
        bid.save()
        # Create or update job conversation
        return Response({"status": "Bid added"})

    @action(detail=True, methods=["delete"])
    def delete_bid(self, request, pk=None):
        """Delete a bid from a job"""
        job = self.get_object()
        user = request.user
        provider = ServiceProvider.objects.get(user=user)
        if not provider:
            return Response(
                {"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND
            )
        bid = Bid.objects.get(job=job, provider=provider)
        if not bid:
            return Response(
                {"error": "Bid not found"}, status=status.HTTP_404_NOT_FOUND
            )
        bid.delete()
        return Response({"status": "Bid deleted"})

    @action(detail=True, methods=["put"])
    def update_bid(self, request, pk=None):
        """Update a bid"""
        bid = Bid.objects.get(id=pk)
        bid.message = request.data.get("message")
        bid.save()
        return Response({"status": "Bid updated"})

    @action(detail=False, methods=["get"])
    def bookings(self, request):
        """Alias for jobs - returns the same data as the main jobs endpoint"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
