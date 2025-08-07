from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Bid
from .serializers import BidSerializer
from apps.Chat.utils import create_bid_conversation, get_or_create_conversation_for_object, add_system_message


class BidViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Bid instances.
    """

    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Admin can see all bids
        if self.is_admin(user):
            return Bid.objects.all().select_related("provider", "job__request")

        # Provider can see their own bids
        if hasattr(user, "provider") and user.user_type == "provider":
            return (
                Bid.objects.filter(provider=user.provider)
                .select_related("job__request")
                .union(Bid.objects.all().select_related("provider", "job__request"))
            )

        # Customer can see bids for their jobs
        return Bid.objects.filter(job__request__user=user).select_related(
            "provider", "job"
        )

    def is_admin(self, user):
        """Check if user is admin"""
        return (
            user.is_staff
            or user.is_superuser
            or getattr(user, "user_type", None) == "admin"
        )
    
    def perform_create(self, serializer):
        """Override to create chat conversation when bid is created"""
        bid = serializer.save()
        
        # Create a chat conversation for this bid
        try:
            conversation = create_bid_conversation(bid)
            # Add initial system message
            add_system_message(
                conversation,
                f"Bid conversation started. Bid amount: ${bid.amount}",
                metadata={'bid_id': str(bid.id), 'action': 'bid_created'}
            )
        except Exception as e:
            # Log error but don't fail the bid creation
            print(f"Error creating bid conversation: {e}")
        
        return bid

    def can_modify_bid(self, user, bid):
        """Check if user can modify a bid"""
        is_admin = self.is_admin(user)
        is_bid_owner = hasattr(user, "provider") and bid.provider == user.provider
        is_job_owner = bid.job.request.user == user

        return is_admin or is_bid_owner or is_job_owner

    def perform_create(self, serializer):
        """Override create to handle admin creating bids for providers"""
        user = self.request.user

        if self.is_admin(user):
            # Admin can create bid for any provider
            provider_id = self.request.data.get("provider_id")
            if provider_id:
                from apps.Provider.models import ServiceProvider

                try:
                    provider = ServiceProvider.objects.get(id=provider_id)
                    serializer.save(provider=provider)
                except ServiceProvider.DoesNotExist:
                    raise ValidationError("Provider not found")
            else:
                serializer.save()
        else:
            # Regular provider creates their own bid
            if hasattr(user, "provider") and user.provider:
                serializer.save(provider=user.provider)
            else:
                raise PermissionDenied("Only providers can create bids")

    def perform_update(self, serializer):
        """Override update to check permissions"""
        bid = self.get_object()
        user = self.request.user

        if not self.can_modify_bid(user, bid):
            raise PermissionDenied("You don't have permission to modify this bid")

        # Only allow editing if bid is pending
        if bid.status != "pending":
            raise ValidationError("Only pending bids can be modified")

        serializer.save()

    def perform_destroy(self, serializer):
        """Override destroy to check permissions"""
        bid = self.get_object()
        user = self.request.user

        if not self.can_modify_bid(user, bid):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You don't have permission to delete this bid")

        # Only allow deletion if bid is pending
        if bid.status != "pending":
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Only pending bids can be deleted")

        # Actually delete the bid
        bid.delete()

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """Accept a bid - Admin, job owner, or provider can accept"""
        bid = self.get_object()
        job = bid.job
        user = request.user

        # Check permissions
        is_admin = self.is_admin(user)
        is_job_owner = job.request.user == user

        if not (is_admin or is_job_owner):
            return Response(
                {"error": "Only admins or job owners can accept bids"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if bid can be accepted
        if bid.status != "pending":
            return Response(
                {"error": "Only pending bids can be accepted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Accept the bid
        bid.status = "accepted"
        bid.save()

        # Update job
        job.status = "assigned"
        job.assigned_provider = bid.provider
        job.save()

        # Reject all other pending bids
        Bid.objects.filter(job=job, status="pending").exclude(id=bid.id).update(
            status="rejected"
        )
        
        # Add system message to bid conversation
        try:
            conversation, _ = get_or_create_conversation_for_object(bid, 'bid')
            add_system_message(
                conversation,
                f"Bid has been accepted! Amount: ${bid.amount}",
                metadata={'bid_id': str(bid.id), 'action': 'bid_accepted'}
            )
        except Exception as e:
            print(f"Error updating bid conversation: {e}")

        return Response(
            {"message": "Bid accepted successfully", "bid": BidSerializer(bid).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Reject a bid - Admin or job owner can reject"""
        bid = self.get_object()
        job = bid.job
        user = request.user

        # Check permissions
        is_admin = self.is_admin(user)
        is_job_owner = job.request.user == user

        if not (is_admin or is_job_owner):
            return Response(
                {"error": "Only admins or job owners can reject bids"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if bid can be rejected
        if bid.status != "pending":
            return Response(
                {"error": "Only pending bids can be rejected"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bid.status = "rejected"
        bid.save()

        return Response(
            {"message": "Bid rejected successfully", "bid": BidSerializer(bid).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def make_counter_offer(self, request, pk=None):
        """Make a counter offer - Admin or job owner only"""
        bid = self.get_object()
        job = bid.job
        user = request.user

        # Check permissions
        is_admin = self.is_admin(user)
        is_job_owner = job.request.user == user

        if not (is_admin or is_job_owner):
            return Response(
                {"error": "Only admins or job owners can make counter offers"},
                status=status.HTTP_403_FORBIDDEN,
            )

        counter_amount = request.data.get("counter_offer")
        if not counter_amount:
            return Response(
                {"error": "Counter offer amount is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if bid can have counter offer
        if bid.status != "pending":
            return Response(
                {"error": "Only pending bids can have counter offers"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bid.counter_offer = counter_amount
        bid.save()

        return Response(
            {
                "message": "Counter offer made successfully",
                "bid": BidSerializer(bid).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def my_bids(self, request):
        """Get current user's bids"""
        user = request.user

        if hasattr(user, "provider") and user.provider:
            bids = Bid.objects.filter(provider=user.provider).select_related(
                "job__request"
            )
        else:
            return Response(
                {"error": "Only providers can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BidSerializer(bids, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def job_bids(self, request):
        """Get bids for jobs owned by current user"""
        user = request.user
        job_id = request.query_params.get("job_id")

        if job_id:
            bids = Bid.objects.filter(
                job_id=job_id, job__request__user=user
            ).select_related("provider", "job")
        else:
            bids = Bid.objects.filter(job__request__user=user).select_related(
                "provider", "job"
            )

        serializer = BidSerializer(bids, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=["get"])
    def conversation(self, request, pk=None):
        """Get the chat conversation for a bid"""
        bid = self.get_object()
        user = request.user
        
        # Check if user has access to this bid
        is_admin = self.is_admin(user)
        is_provider = hasattr(user, "provider") and bid.provider == user.provider
        is_job_owner = bid.job.request.user == user
        
        if not (is_admin or is_provider or is_job_owner):
            return Response(
                {"error": "You don't have permission to view this conversation"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        # Get or create conversation
        conversation, created = get_or_create_conversation_for_object(bid, 'bid')
        
        if created:
            # If newly created, set up participants
            participants = []
            if bid.provider and hasattr(bid.provider, 'user'):
                participants.append(bid.provider.user)
            if bid.job and bid.job.request and bid.job.request.user:
                participants.append(bid.job.request.user)
            
            for participant in participants:
                conversation.add_participant(participant)
            
            # Add initial message
            add_system_message(
                conversation,
                f"Bid conversation started. Bid amount: ${bid.amount}",
                metadata={'bid_id': str(bid.id), 'action': 'bid_created'}
            )
        
        return Response({
            "conversation_id": str(conversation.id),
            "conversation_type": conversation.conversation_type,
            "title": conversation.title,
            "created": created
        })
