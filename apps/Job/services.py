from .models import Job, TimelineEvent
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class JobTimelineService:
    """
    Service class to handle creation and management of job timeline events.
    """

    @staticmethod
    def create_timeline_event(
        job,
        event_type,
        description=None,
        visibility="all",
        metadata=None,
        created_by=None,
    ):
        """
        Creates a new timeline event for a job.

        Args:
            job (Job): The job instance
            event_type (str): Type of event from TimelineEvent.EVENT_TYPE_CHOICES
            description (str, optional): Custom description. If None, uses default based on event type
            visibility (str): Who can see this event ('all', 'provider', 'customer', 'system')
            metadata (dict, optional): Additional data to store with the event
            created_by (User, optional): User who triggered this event

        Returns:
            TimelineEvent: The created timeline event instance
        """
        if description is None:
            # Set default descriptions based on event type
            descriptions = {
                "created": f"Job #{job.id} was created",
                "updated": f"Job #{job.id} details were updated",
                "status_changed": f"Job status changed to {job.status}",
                "provider_assigned": "A service provider was assigned to this job",
                "provider_accepted": "The service provider accepted the job",
                "job_started": "The job has started",
                "in_transit": "Your items are now in transit",
                "completed": "The job has been completed",
                "cancelled": "The job was cancelled",
                "document_uploaded": "A new document was uploaded",
                "message_sent": "A new message was sent",
                "payment_processed": "A payment was processed",
                "rating_submitted": "A rating was submitted",
                "system_notification": "System notification",
            }
            description = descriptions.get(event_type, "Event recorded")

        # Create the timeline event
        event = TimelineEvent.objects.create(
            job=job,
            event_type=event_type,
            description=description,
            visibility=visibility,
            metadata=metadata or {},
            created_by=created_by,
        )

        return event

    @staticmethod
    def get_job_timeline(job, user=None, visibility=None):
        """
        Retrieves timeline events for a job, filtered by visibility and user access.

        Args:
            job (Job): The job instance
            user (User, optional): User requesting the timeline
            visibility (list, optional): List of visibility types to include

        Returns:
            QuerySet: Filtered timeline events
        """
        events = TimelineEvent.objects.filter(job=job)

        # If no user provided, return only 'all' visibility
        if user is None:
            return events.filter(visibility="all")

        # Check user's role relative to the job to determine visibility
        is_customer = hasattr(job.request, "user") and job.request.user == user
        is_provider = False  # Implement based on your provider-job relationship
        is_staff = user.is_staff if hasattr(user, "is_staff") else False

        # Filter by visibility based on user's role
        if visibility:
            events = events.filter(visibility__in=visibility)
        elif is_staff:
            # Staff can see everything
            pass
        elif is_customer:
            # Customers can see 'all' and 'customer' events
            events = events.filter(visibility__in=["all", "customer"])
        elif is_provider:
            # Providers can see 'all' and 'provider' events
            events = events.filter(visibility__in=["all", "provider"])
        else:
            # Others can only see 'all' events
            events = events.filter(visibility="all")

        return events

    @staticmethod
    def create_status_change_event(job, old_status, new_status, user=None):
        """
        Creates a timeline event for job status changes with appropriate visibility.

        Args:
            job (Job): The job instance
            old_status (str): Previous status
            new_status (str): New status
            user (User, optional): User who changed the status

        Returns:
            TimelineEvent: The created timeline event
        """
        description = f"Job status changed from {old_status} to {new_status}"
        metadata = {
            "old_status": old_status,
            "new_status": new_status,
            "changed_at": timezone.now().isoformat(),
        }

        return JobTimelineService.create_timeline_event(
            job=job,
            event_type="status_changed",
            description=description,
            metadata=metadata,
            created_by=user,
        )
