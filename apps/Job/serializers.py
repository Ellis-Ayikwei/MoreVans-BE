from rest_framework import serializers

from apps.Provider.models import ServiceProvider
from .models import Job, JobProviderAcceptance, TimelineEvent
from apps.Request.serializer import RequestSerializer
from apps.Bidding.serializers import BidSerializer
from apps.Provider.serializer import ServiceProviderSerializer


class TimelineEventSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TimelineEvent
        fields = [
            "id",
            "event_type",
            "description",
            "visibility",
            "metadata",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class JobProviderAcceptanceSerializer(serializers.ModelSerializer):
    provider = ServiceProviderSerializer(read_only=True)

    class Meta:
        model = JobProviderAcceptance
        fields = ["id", "provider", "accepted_at"]


class JobSerializer(serializers.ModelSerializer):
    request = RequestSerializer(read_only=True)
    request_id = serializers.CharField(write_only=True)

    time_remaining = serializers.SerializerMethodField()
    timeline_events = serializers.SerializerMethodField()
    job_number = serializers.CharField(read_only=True)
    bids = BidSerializer(many=True, read_only=True)  # Add this line
    assigned_provider = ServiceProviderSerializer(read_only=True)
    # Direct providers list (from M2M)
    # accepted_providers = ServiceProviderSerializer(many=True, read_only=True)
    # Through-model entries with accepted_at metadata
    accepted_providers = JobProviderAcceptanceSerializer(
        source="accepted_provider_links", many=True, read_only=True
    )

    class Meta:
        model = Job
        fields = [
            "id",
            "job_number",
            "title",
            "description",
            "is_instant",
            "request",
            "request_id",
            "status",
            "is_completed",  # Add this if it exists in your model
            "created_at",
            "updated_at",
            "bidding_end_time",
            "minimum_bid",
            "preferred_vehicle_types",
            "required_qualifications",
            "notes",
            "assigned_provider",
            "accepted_providers",
            "time_remaining",
            "price",
            "timeline_events",
            "bids",  # Add this line
        ]
        read_only_fields = ["id", "job_number", "created_at", "updated_at", "bids"]

    def get_time_remaining(self, obj):
        if obj.bidding_end_time:
            from django.utils import timezone

            remaining = obj.bidding_end_time - timezone.now()
            return max(0, remaining.total_seconds())
        return None

    def get_timeline_events(self, obj):
        # Import here to avoid circular imports
        try:
            from .services import JobTimelineService

            # Get the requesting user
            user = None
            request = self.context.get("request")
            if request and hasattr(request, "user"):
                user = request.user

            # Get timeline events with proper visibility filtering
            events = JobTimelineService.get_job_timeline(job=obj, user=user)
            return TimelineEventSerializer(events, many=True).data
        except ImportError:
            # Fallback if service is not available
            return []


class ProviderSideJobSerializer(serializers.ModelSerializer):
    request = RequestSerializer(read_only=True)
    request_id = serializers.CharField(write_only=True)

    time_remaining = serializers.SerializerMethodField()
    timeline_events = serializers.SerializerMethodField()
    job_number = serializers.CharField(read_only=True)
    bids = BidSerializer(many=True, read_only=True)  # Add this line
    # Direct providers list (from M2M)
    # accepted_providers = ServiceProviderSerializer(many=True, read_only=True)
    # Through-model entries with accepted_at metadata
    is_accepted = serializers.SerializerMethodField(default=False)

    class Meta:
        model = Job
        fields = [
            "id",
            "job_number",
            "title",
            "description",
            "is_instant",
            "request",
            "request_id",
            "status",
            "is_completed",
            "created_at",
            "updated_at",
            "bidding_end_time",
            "minimum_bid",
            "preferred_vehicle_types",
            "required_qualifications",
            "notes",
            "time_remaining",
            "price",
            "is_accepted",
            "timeline_events",
            "bids",
        ]
        read_only_fields = ["id", "job_number", "created_at", "updated_at", "bids"]

    def get_is_accepted(self, obj):
        request = self.context.get("request")
        if (
            not request
            or not getattr(request, "user", None)
            or request.user.is_anonymous
        ):
            return False
        try:
            provider = ServiceProvider.objects.get(user=request.user)
        except ServiceProvider.DoesNotExist:
            return False
        return (
            obj.accepted_providers.filter(pk=provider.pk).exists()
            or getattr(obj, "assigned_provider_id", None) == provider.id
        )

    def get_time_remaining(self, obj):
        if obj.bidding_end_time:
            from django.utils import timezone

            remaining = obj.bidding_end_time - timezone.now()
            return max(0, remaining.total_seconds())
        return None

    def get_timeline_events(self, obj):
        # Import here to avoid circular imports
        try:
            from .services import JobTimelineService

            # Get the requesting user
            user = None
            request = self.context.get("request")
            if request and hasattr(request, "user"):
                user = request.user

            # Get timeline events with proper visibility filtering
            events = JobTimelineService.get_job_timeline(job=obj, user=user)
            return TimelineEventSerializer(events, many=True).data
        except ImportError:
            # Fallback if service is not available
            return []
