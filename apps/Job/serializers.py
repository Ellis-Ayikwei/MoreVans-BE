from rest_framework import serializers
from .models import Job, TimelineEvent
from apps.Request.serializer import RequestSerializer


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
    timeline_events = serializers.SerializerMethodField()  # Add this line

    class Meta:
        model = Job
        fields = [
            "id",
            "request",
            "request_id",
            "status",
            "created_at",
            "updated_at",
            "bidding_end_time",
            "minimum_bid",
            "preferred_vehicle_types",
            "required_qualifications",
            "notes",
            "time_remaining",
            "timeline_events",  # Add this field
        ]
        read_only_fields = ["id", "created_at", "updated_at", "status"]

    # Comment out method that uses non-existent table
    # def get_bid_count(self, obj):
    #     return obj.bids.count()

    def get_time_remaining(self, obj):
        if obj.bidding_end_time:
            from django.utils import timezone

            remaining = obj.bidding_end_time - timezone.now()
            return max(0, remaining.total_seconds())
        return None

    def get_timeline_events(self, obj):
        # Import here to avoid circular imports
        from .services import JobTimelineService

        # Get the requesting user
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        # Get timeline events with proper visibility filtering
        events = JobTimelineService.get_job_timeline(job=obj, user=user)
        return TimelineEventSerializer(events, many=True).data
