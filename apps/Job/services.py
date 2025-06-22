from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class JobComplexityAnalyzer:
    """Analyzes job complexity based on request parameters"""

    @staticmethod
    def calculate_complexity_score(request) -> float:
        """
        Calculate complexity score for a request (0-1, higher = more complex)
        Based on the AnyVan algorithm logic we designed
        """
        complexity = 0.0

        # Special handling requirements
        if request.requires_special_handling:
            complexity += 0.3

        # Weight factor
        if request.total_weight:
            weight_kg = float(request.total_weight)
            if weight_kg > 500:  # Very heavy items
                complexity += 0.2
            elif weight_kg > 200:  # Heavy items
                complexity += 0.1

        # Staff requirements
        if request.staff_required and request.staff_required > 2:
            complexity += 0.15

        # Special instructions
        if request.special_instructions and len(request.special_instructions) > 100:
            complexity += 0.1

        # Insurance requirements
        if request.insurance_required:
            complexity += 0.1
            if request.insurance_value and float(request.insurance_value) > 10000:
                complexity += 0.1

        # Service type complexity
        if request.service_type:
            complex_services = [
                "piano_transport",
                "antique_furniture",
                "artwork",
                "fragile_items",
            ]
            if any(
                service in request.service_type.lower() for service in complex_services
            ):
                complexity += 0.2

        # Multiple locations (journey type)
        if request.request_type == "journey":
            stop_count = request.stops.count() if hasattr(request, "stops") else 0
            if stop_count > 3:  # More than pickup and dropoff + 1 stop
                complexity += 0.15

        # Time constraints
        if request.priority in ["same_day", "express"]:
            complexity += 0.1

        # Location access difficulty (if you have this data)
        if hasattr(request, "pickup_location") and request.pickup_location:
            # You might need to add these fields to your Location model
            if hasattr(request.pickup_location, "access_difficulty"):
                if request.pickup_location.access_difficulty == "difficult":
                    complexity += 0.2
                elif request.pickup_location.access_difficulty == "very_difficult":
                    complexity += 0.4

        if hasattr(request, "dropoff_location") and request.dropoff_location:
            if hasattr(request.dropoff_location, "access_difficulty"):
                if request.dropoff_location.access_difficulty == "difficult":
                    complexity += 0.2
                elif request.dropoff_location.access_difficulty == "very_difficult":
                    complexity += 0.4

        return min(1.0, complexity)


class RouteEfficiencyAnalyzer:
    """Analyzes route efficiency for instant pricing eligibility"""

    @staticmethod
    def calculate_route_efficiency(request) -> float:
        """Calculate route efficiency score (0-1, higher = better for instant pricing)"""
        if not request.pickup_location or not request.dropoff_location:
            return 0.3  # Low efficiency for incomplete location data

        pickup_postcode = getattr(request.pickup_location, "postcode", "")
        dropoff_postcode = getattr(request.dropoff_location, "postcode", "")

        if not pickup_postcode or not dropoff_postcode:
            return 0.4  # Medium-low efficiency

        # Same postcode area (first 2-3 characters)
        if pickup_postcode[:2] == dropoff_postcode[:2]:
            return 0.9  # High efficiency - same area
        elif pickup_postcode[0] == dropoff_postcode[0]:
            return 0.7  # Medium efficiency - same region
        else:
            return 0.4  # Lower efficiency - different regions


class DemandAnalyzer:
    """Analyzes demand patterns to determine pricing strategy"""

    @staticmethod
    def get_demand_score(request) -> float:
        """Get demand score (0-1, higher = more demand)"""
        if not request.preferred_pickup_date:
            return 0.6  # Default demand

        pickup_date = request.preferred_pickup_date

        # Seasonal factors
        month = pickup_date.month
        seasonal_factor = 1.2 if month in [4, 5, 6, 7, 8] else 0.8  # Peak moving season

        # Day of week factors
        weekday = pickup_date.weekday()
        weekend_factor = 1.3 if weekday >= 5 else 1.0  # Weekend premium

        # Time urgency
        days_ahead = (pickup_date - datetime.now().date()).days
        urgency_factor = 1.0
        if days_ahead <= 1:
            urgency_factor = 1.4  # Same/next day high demand
        elif days_ahead <= 7:
            urgency_factor = 1.2  # Within a week

        base_demand = 0.6
        final_score = min(
            1.0, base_demand * seasonal_factor * weekend_factor * urgency_factor
        )

        return final_score


class ProviderAvailabilityService:
    """Service to check provider availability for instant jobs"""

    @staticmethod
    def check_qualified_providers(request) -> bool:
        """Check if qualified providers are available for this request"""
        # This would integrate with your ServiceProvider model
        # For now, we'll use a simplified check

        cache_key = f"providers_available_{request.pickup_location.postcode if request.pickup_location else 'unknown'}"
        cached_result = cache.get(cache_key)

        if cached_result is not None:
            return cached_result

        # In a real implementation, you'd query your ServiceProvider model
        # Check for providers in the area with good ratings
        try:
            from apps.Provider.models import ServiceProvider

            # Get providers in the area (you might need to implement location-based filtering)
            available_providers = ServiceProvider.objects.filter(
                is_active=True,
                # Add location/area filtering based on your model structure
            ).count()

            result = available_providers > 0
            cache.set(cache_key, result, timeout=300)  # Cache for 5 minutes
            return result

        except ImportError:
            # Fallback if ServiceProvider model doesn't exist yet
            return True  # Assume providers available


class JobService:
    @staticmethod
    def create_from_request(
        request, is_instant=False, bidding_duration_hours=24, minimum_bid=None
    ):
        """
        Create a job from a request.

        Args:
            request: The Request instance to create the job from
            is_instant (bool): Whether this should be an instant job
            bidding_duration_hours (int): Duration of bidding period if not instant
            minimum_bid (Decimal): Minimum bid amount if not instant

        Returns:
            Job: The created job instance
        """
        from .models import Job, TimelineEvent

        # Create the job
        job = Job.objects.create(
            request=request,
            title=f"Move request from {request.pickup_location.city if request.pickup_location else 'Unknown'} to {request.dropoff_location.city if request.dropoff_location else 'Unknown'}",
            description="Moving request",
            status="draft",
            price=request.base_price,
            is_instant=is_instant,
        )

        # Create initial timeline event
        TimelineEvent.objects.create(
            job=job,
            event_type="created",
            description="Job created from request",
            metadata={"request_id": str(request.id), "is_instant": is_instant},
        )

        # If instant, make it instant
        if is_instant:
            job.make_instant()
        # Otherwise, make it biddable
        else:
            job.make_biddable(
                bidding_duration_hours=bidding_duration_hours, minimum_bid=minimum_bid
            )

        return job

    @staticmethod
    def determine_if_biddable_or_not(request) -> Dict[str, Any]:
        """
        Determine if a job should be biddable or instant based on request properties.
        Implements the AnyVan-style algorithm selection logic.

        Args:
            request: The Request instance to analyze

        Returns:
            dict: Decision result with strategy, confidence, and reasoning
        """
        logger.info(f"Analyzing request {request.id} for pricing strategy")

        reasoning = []
        confidence_score = 1.0

        # Step 1: Check if request type is eligible for instant pricing
        # Based on your REQUEST_TYPE_CHOICES, 'instant' type should be eligible
        instant_eligible_types = ["instant"]

        if request.request_type not in instant_eligible_types:
            reasoning.append(
                f"Request type '{request.request_type}' not eligible for instant pricing"
            )
            return {
                "strategy": "biddable",
                "is_instant": False,
                "confidence_score": 1.0,
                "reasoning": reasoning,
                "estimated_response_time": "2-6 hours",
                "recommendation": "Route to auction for competitive bidding",
            }

        # Step 2: Assess job complexity
        complexity_score = JobComplexityAnalyzer.calculate_complexity_score(request)
        if complexity_score > 0.6:
            reasoning.append(f"High complexity score: {complexity_score:.2f}")
            confidence_score -= 0.3

        # Step 3: Check route efficiency
        route_efficiency = RouteEfficiencyAnalyzer.calculate_route_efficiency(request)
        if route_efficiency < 0.5:
            reasoning.append(f"Low route efficiency: {route_efficiency:.2f}")
            confidence_score -= 0.2

        # Step 4: Check provider availability
        providers_available = ProviderAvailabilityService.check_qualified_providers(
            request
        )
        if not providers_available:
            reasoning.append("No qualified providers available")
            confidence_score -= 0.4

        # Step 5: Check timing constraints
        if request.preferred_pickup_date:
            days_ahead = (request.preferred_pickup_date - datetime.now().date()).days
            if days_ahead < 2:
                reasoning.append("Short notice booking - limited route optimization")
                confidence_score -= 0.3

        # Step 6: Demand analysis
        demand_score = DemandAnalyzer.get_demand_score(request)
        if demand_score > 0.8:
            reasoning.append(f"High demand period: {demand_score:.2f}")
            confidence_score -= 0.2

        # Step 7: Service level check
        if request.service_level in ["same_day", "express"]:
            reasoning.append("Express/same-day service requires special handling")
            confidence_score -= 0.2

        # Step 8: Weight and size constraints
        if request.total_weight and float(request.total_weight) > 1000:  # 1 ton
            reasoning.append("Heavy items require specialized equipment")
            confidence_score -= 0.2

        # Step 9: Distance check
        if (
            request.estimated_distance and float(request.estimated_distance) > 500
        ):  # 500km
            reasoning.append("Long distance move requires custom planning")
            confidence_score -= 0.3

        # Final decision logic
        decision_threshold = 0.7
        complexity_threshold = 0.6

        if (
            confidence_score >= decision_threshold
            and complexity_score <= complexity_threshold
            and providers_available
            and route_efficiency >= 0.5
        ):

            # Use instant pricing
            reasoning.append("Job suitable for instant pricing algorithm")
            return {
                "strategy": "instant",
                "is_instant": True,
                "confidence_score": confidence_score,
                "reasoning": reasoning,
                "estimated_price": request.base_price,
                "booking_expires_minutes": 5,
                "recommendation": "Show instant price and booking option",
            }
        else:
            # Use auction bidding
            reasoning.append("Job requires human assessment via auction")

            # Determine bidding duration based on complexity
            if complexity_score > 0.8:
                bidding_hours = 48  # Complex jobs get longer bidding
            elif complexity_score > 0.6:
                bidding_hours = 24  # Standard bidding time
            else:
                bidding_hours = 12  # Simple jobs get shorter bidding

            return {
                "strategy": "biddable",
                "is_instant": False,
                "confidence_score": confidence_score,
                "reasoning": reasoning,
                "estimated_response_time": f"{bidding_hours//12 * 2}-{bidding_hours//6} hours",
                "bidding_duration_hours": bidding_hours,
                "minimum_bid": request.base_price * 0.8 if request.base_price else None,
                "recommendation": "Create auction listing for competitive bidding",
            }

    @staticmethod
    def create_job_with_strategy(request):
        """
        Create a job using the determined strategy (instant or biddable)

        Args:
            request: The Request instance

        Returns:
            Job: The created job instance
        """
        from .models import Job, TimelineEvent

        # Determine strategy
        strategy_result = JobService.determine_if_biddable_or_not(request)

        # Log the decision
        logger.info(
            f"Job strategy for request {request.id}: {strategy_result['strategy']} "
            f"(confidence: {strategy_result['confidence_score']:.2f})"
        )

        # Create job based on strategy
        if strategy_result["strategy"] == "instant":
            job = JobService.create_from_request(request=request, is_instant=True)

            # Create timeline event explaining instant decision
            TimelineEvent.objects.create(
                job=job,
                event_type="system_notification",
                description="Job qualified for instant pricing",
                metadata={
                    "strategy": "instant",
                    "confidence_score": strategy_result["confidence_score"],
                    "reasoning": strategy_result["reasoning"],
                },
                visibility="system",
            )

        else:  # biddable
            bidding_hours = strategy_result.get("bidding_duration_hours", 24)
            minimum_bid = strategy_result.get("minimum_bid")

            job = JobService.create_from_request(
                request=request,
                is_instant=False,
                bidding_duration_hours=bidding_hours,
                minimum_bid=minimum_bid,
            )

            # Create timeline event explaining auction decision
            TimelineEvent.objects.create(
                job=job,
                event_type="system_notification",
                description="Job routed to auction for competitive bidding",
                metadata={
                    "strategy": "biddable",
                    "confidence_score": strategy_result["confidence_score"],
                    "reasoning": strategy_result["reasoning"],
                    "bidding_duration_hours": bidding_hours,
                },
                visibility="system",
            )

        return job


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
        from .models import Job, TimelineEvent

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
        from .models import Job, TimelineEvent

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
        from .models import Job, TimelineEvent

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
