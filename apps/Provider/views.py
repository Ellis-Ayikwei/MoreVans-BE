from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import (
    ServiceProvider,
    ServiceArea,
    InsurancePolicy,
    ProviderVehicle,
    SavedJob,
    WatchedJob,
)
from .serializer import (
    ServiceProviderSerializer,
    ServiceAreaSerializer,
    InsurancePolicySerializer,
    ProviderVehicleSerializer,
    SavedJobSerializer,
    WatchedJobSerializer,
)
from Job.serializers import JobSerializer


class ServiceProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing ServiceProvider instances.
    """

    queryset = ServiceProvider.objects.all()
    serializer_class = ServiceProviderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ServiceProvider.objects.all()
        user_id = self.request.query_params.get("user", None)
        verification_status = self.request.query_params.get("verification_status", None)
        service_category = self.request.query_params.get("service_category", None)

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if verification_status:
            queryset = queryset.filter(verification_status=verification_status)
        if service_category:
            queryset = queryset.filter(service_categories__id=service_category)

        return queryset


class ServiceAreaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing ServiceArea instances.
    """

    queryset = ServiceArea.objects.all()
    serializer_class = ServiceAreaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ServiceArea.objects.all()
        provider_id = self.request.query_params.get("provider", None)
        is_primary = self.request.query_params.get("is_primary", None)

        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        if is_primary is not None:
            is_primary_bool = is_primary.lower() == "true"
            queryset = queryset.filter(is_primary=is_primary_bool)

        return queryset


class InsurancePolicyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing InsurancePolicy instances.
    """

    queryset = InsurancePolicy.objects.all()
    serializer_class = InsurancePolicySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = InsurancePolicy.objects.all()
        provider_id = self.request.query_params.get("provider", None)
        policy_type = self.request.query_params.get("policy_type", None)

        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        if policy_type:
            queryset = queryset.filter(policy_type=policy_type)

        return queryset


class ProviderVehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing ProviderVehicle instances.
    """

    queryset = ProviderVehicle.objects.all()
    serializer_class = ProviderVehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ProviderVehicle.objects.all()
        provider_id = self.request.query_params.get("provider", None)
        vehicle_type = self.request.query_params.get("vehicle_type", None)

        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type)

        return queryset


class SavedJobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for provider's saved jobs
    """

    serializer_class = SavedJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedJob.objects.filter(provider=self.request.user)

    @action(detail=False, methods=["get"])
    def jobs(self, request):
        """Return the actual job objects the provider has saved"""
        from Job.models import Job

        saved_job_ids = SavedJob.objects.filter(provider=request.user).values_list(
            "job_id", flat=True
        )

        jobs = Job.objects.filter(id__in=saved_job_ids)
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def toggle(self, request):
        """Toggle saving/unsaving a job"""
        job_id = request.data.get("job_id")
        if not job_id:
            return Response(
                {"error": "job_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from Job.models import Job

            job = Job.objects.get(pk=job_id)

            saved_job, created = SavedJob.objects.get_or_create(
                job=job, provider=request.user
            )

            if not created:
                # If already saved, remove it (toggle off)
                saved_job.delete()
                return Response({"status": "job unsaved"})

            return Response({"status": "job saved"})

        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND
            )


class WatchedJobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for provider's watched jobs
    """

    serializer_class = WatchedJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WatchedJob.objects.filter(provider=self.request.user)

    @action(detail=False, methods=["get"])
    def jobs(self, request):
        """Return the actual job objects the provider is watching"""
        from Job.models import Job

        watched_job_ids = WatchedJob.objects.filter(provider=request.user).values_list(
            "job_id", flat=True
        )

        jobs = Job.objects.filter(id__in=watched_job_ids)
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def toggle(self, request):
        """Toggle watching/unwatching a job"""
        job_id = request.data.get("job_id")
        if not job_id:
            return Response(
                {"error": "job_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from Job.models import Job

            job = Job.objects.get(pk=job_id)

            watched_job, created = WatchedJob.objects.get_or_create(
                job=job, provider=request.user
            )

            if not created:
                # If already watching, remove it (toggle off)
                watched_job.delete()
                return Response({"status": "job unwatched"})

            return Response({"status": "job watched"})

        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND
            )
