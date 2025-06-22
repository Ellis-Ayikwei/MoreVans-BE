from rest_framework import serializers
from .models import Job, TimelineEvent
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


class JobSerializer(serializers.ModelSerializer):
    request = RequestSerializer(read_only=True)
    request_id = serializers.CharField(write_only=True)

    time_remaining = serializers.SerializerMethodField()
    timeline_events = serializers.SerializerMethodField()
    job_number = serializers.CharField(read_only=True)
    bids = BidSerializer(many=True, read_only=True)  # Add this line
    assigned_provider = ServiceProviderSerializer(read_only=True)

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
