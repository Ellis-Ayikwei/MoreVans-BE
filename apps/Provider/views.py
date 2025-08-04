from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from .models import (
    ServiceProvider,
    ServiceArea,
    InsurancePolicy,
    ProviderDocument,
    ProviderReview,
    ProviderPayment,
    SavedJob,
    WatchedJob,
)
from .serializer import (
    ServiceProviderSerializer,
    ServiceAreaSerializer,
    InsurancePolicySerializer,
    ProviderDocumentSerializer,
    ProviderReviewSerializer,
    ProviderPaymentSerializer,
    SavedJobSerializer,
    WatchedJobSerializer,
)
from apps.Job.serializers import JobSerializer
from apps.Job.models import Job
from apps.User.models import User
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class ServiceProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing ServiceProvider instances.
    """

    queryset = ServiceProvider.objects.all()
    serializer_class = ServiceProviderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # If user is not staff, only show their own provider profile
        if not self.request.user.is_staff:
            return queryset.filter(user=self.request.user)

        # For staff users, allow filtering by user_id
        user_id = self.request.query_params.get("user_id")
        if user_id:
            # Check if the user exists and is a provider
            try:
                user = User.objects.get(id=user_id)
                if user.user_type == "provider":
                    return queryset.filter(user=user)
                else:
                    # Return empty queryset if user is not a provider
                    return queryset.none()
            except ObjectDoesNotExist:
                # Return empty queryset if user doesn't exist
                return queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Override list method to return single object when filtering by user_id
        """
        user_id = request.query_params.get("user_id")

        # If filtering by user_id, return single object instead of list
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                if user.user_type == "provider":
                    provider = self.get_queryset().first()
                    if provider:
                        serializer = self.get_serializer(provider)
                        return Response(serializer.data)
                    else:
                        return Response(
                            {"detail": "Provider profile not found"},
                            status=status.HTTP_404_NOT_FOUND,
                        )
                else:
                    return Response(
                        {"detail": "User is not a service provider"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except ObjectDoesNotExist:
                return Response(
                    {"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

        # Default list behavior for other cases
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=["post", "patch"])
    def activate(self, request, pk=None):
        provider = self.get_object()
        provider.status = "active"
        provider.save()
        return Response({"status": "provider activated"})

    @action(detail=True, methods=["post", "patch"])
    def suspend(self, request, pk=None):
        provider = self.get_object()
        provider.status = "suspended"
        provider.save()
        return Response({"status": "provider suspended"})

    @action(detail=True, methods=["post", "patch"])
    def verify(self, request, pk=None):
        provider = self.get_object()
        provider.verification_status = "verified"
        provider.last_verified = timezone.now()
        provider.save()
        return Response({"status": "provider verified"})

    @action(detail=True, methods=["get", "post"])
    def documents(self, request, pk=None):
        provider = self.get_object()
        if request.method == "GET":
            documents = provider.documents.all()
            serializer = ProviderDocumentSerializer(
                documents, many=True, context={"request": request}
            )
            return Response(serializer.data)
        elif request.method == "POST":
            serializer = ProviderDocumentSerializer(
                data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save(provider=provider)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def verify_document(self, request, pk=None):
        """
        Verify a provider's document.
        """
        provider = self.get_object()
        document_id = request.data.get("document_id")
        verification_note = request.data.get("verification_note")

        try:
            document = provider.documents.get(id=document_id)
            document.is_verified = True
            document.rejection_reason = None
            document.status = "verified"
            if verification_note:
                document.notes = verification_note
            document.save()
            serializer = ProviderDocumentSerializer(document)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["post"])
    def reject_document(self, request, pk=None):
        """
        Reject a provider's document.
        """
        provider = self.get_object()
        document_id = request.data.get("document_id")
        rejection_reason = request.data.get("rejection_reason")

        if not rejection_reason:
            return Response(
                {"detail": "Rejection reason is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            document = provider.documents.get(id=document_id)
            document.is_verified = False
            document.rejection_reason = rejection_reason
            document.status = "rejected"
            document.save()
            serializer = ProviderDocumentSerializer(document)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["post"])
    def update_document_status(self, request, pk=None):
        """
        Update the status of a provider's document.
        """
        provider = self.get_object()
        document_id = request.data.get("document_id")
        new_status = request.data.get("status")
        notes = request.data.get("notes")

        if not new_status:
            return Response(
                {"detail": "Status is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        if new_status not in dict(ProviderDocument.DOCUMENT_STATUS):
            return Response(
                {
                    "detail": f"Invalid status. Must be one of: {', '.join(dict(ProviderDocument.DOCUMENT_STATUS).keys())}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            document = provider.documents.get(id=document_id)
            document.status = new_status
            if notes:
                document.notes = notes
            if new_status == "verified":
                document.is_verified = True
                document.rejection_reason = None
            elif new_status == "rejected":
                document.is_verified = False
                if not notes:
                    return Response(
                        {"detail": "Notes are required when rejecting a document."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                document.rejection_reason = notes
            document.save()
            serializer = ProviderDocumentSerializer(document)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["get"])
    def reviews(self, request, pk=None):
        provider = self.get_object()
        reviews = provider.reviews.all()
        serializer = ProviderReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def payments(self, request, pk=None):
        provider = self.get_object()
        payments = provider.payments.all()
        serializer = ProviderPaymentSerializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def saved_jobs(self, request, pk=None):
        provider = self.get_object()
        saved_jobs = SavedJob.objects.filter(provider=provider.user)
        serializer = SavedJobSerializer(saved_jobs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def watched_jobs(self, request, pk=None):
        provider = self.get_object()
        watched_jobs = WatchedJob.objects.filter(provider=provider.user)
        serializer = WatchedJobSerializer(watched_jobs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def get_provider_by_user_id(self, request):
        """Get provider by user id - only works when user type is provider"""
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response(
                {"detail": "user_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # First check if the user exists and is a provider
            user = User.objects.get(id=user_id)

            if user.user_type != "provider":
                return Response(
                    {"detail": "User is not a service provider"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get the provider profile
            provider = ServiceProvider.objects.get(user=user)
            serializer = ServiceProviderSerializer(provider)
            return Response(serializer.data)

        except ObjectDoesNotExist:
            return Response(
                {"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Provider profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    def accept_job(self, request):
        """Accept a job"""
        job_id = request.query_params.get("job_id")

        if not job_id:
            return Response(
                {"error": "job_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            job = Job.objects.get(id=job_id)
            job.accept_bid(request.user)
            return Response({"status": "Job accepted"})
        except ObjectDoesNotExist:
            return Response(
                {"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAdminUser]
    )
    def sync_provider_users(self, request):
        """
        Sync users with user_type 'provider' to the ServiceProvider table.
        This will:
        1. Find all users with user_type 'provider'
        2. Create ServiceProvider entries for those who don't have one
        3. Return statistics about the sync operation
        """
        try:
            with transaction.atomic():
                # Get all users with user_type 'provider'
                provider_users = User.objects.filter(user_type="provider")

                stats = {
                    "total_provider_users": provider_users.count(),
                    "existing_entries": 0,
                    "new_entries": 0,
                    "errors": [],
                }

                for user in provider_users:
                    try:
                        # Check if ServiceProvider entry exists
                        provider, created = ServiceProvider.objects.get_or_create(
                            user=user,
                            defaults={
                                "business_type": "sole_trader",  # Default business type
                                "company_name": f"{user.first_name}'s Service",  # Default company name
                                "verification_status": "unverified",  # Default verification status
                            },
                        )

                        if created:
                            stats["new_entries"] += 1
                            logger.info(
                                f"Created new ServiceProvider entry for user {user.id}"
                            )
                        else:
                            stats["existing_entries"] += 1
                            logger.info(
                                f"ServiceProvider entry already exists for user {user.id}"
                            )

                    except Exception as e:
                        error_msg = f"Error processing user {user.id}: {str(e)}"
                        stats["errors"].append(error_msg)
                        logger.error(error_msg)

                return Response(
                    {
                        "status": "success",
                        "message": "Provider sync completed",
                        "statistics": stats,
                    }
                )

        except Exception as e:
            error_msg = f"Error during provider sync: {str(e)}"
            logger.error(error_msg)
            return Response(
                {"status": "error", "message": error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ServiceAreaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing ServiceArea instances.
    """

    queryset = ServiceArea.objects.all()
    serializer_class = ServiceAreaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        provider_id = self.request.query_params.get("provider_id")
        if provider_id:
            return queryset.filter(provider_id=provider_id)
        return queryset


class InsurancePolicyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing InsurancePolicy instances.
    """

    queryset = InsurancePolicy.objects.all()
    serializer_class = InsurancePolicySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        provider_id = self.request.query_params.get("provider_id")
        if provider_id:
            return queryset.filter(provider_id=provider_id)
        return queryset


class ProviderDocumentViewSet(viewsets.ModelViewSet):
    queryset = ProviderDocument.objects.all()
    serializer_class = ProviderDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        provider_id = self.request.query_params.get("provider_id")
        if provider_id:
            return queryset.filter(provider_id=provider_id)
        return queryset

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        document = self.get_object()
        document.status = "approved"
        document.save()
        return Response({"status": "document approved"})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        document = self.get_object()
        document.status = "rejected"
        document.save()
        return Response({"status": "document rejected"})


class ProviderReviewViewSet(viewsets.ModelViewSet):
    queryset = ProviderReview.objects.all()
    serializer_class = ProviderReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        provider_id = self.request.query_params.get("provider_id")
        if provider_id:
            return queryset.filter(provider_id=provider_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class ProviderPaymentViewSet(viewsets.ModelViewSet):
    queryset = ProviderPayment.objects.all()
    serializer_class = ProviderPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        provider_id = self.request.query_params.get("provider_id")
        if provider_id:
            return queryset.filter(provider_id=provider_id)
        return queryset


class SavedJobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for provider's saved jobs
    """

    queryset = SavedJob.objects.all()
    serializer_class = SavedJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(provider=self.request.user)

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user)

    @action(detail=False, methods=["get"])
    def jobs(self, request):
        """Return the actual job objects the provider has saved"""
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
            job = Job.objects.get(pk=job_id)

            saved_job, created = SavedJob.objects.get_or_create(
                job=job, provider=request.user
            )

            if not created:
                # If already saved, remove it (toggle off)
                saved_job.delete()
                return Response({"status": "job unsaved"})

            return Response({"status": "job saved"})

        except ObjectDoesNotExist:
            return Response(
                {"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND
            )


class WatchedJobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for provider's watched jobs
    """

    queryset = WatchedJob.objects.all()
    serializer_class = WatchedJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(provider=self.request.user)

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user)

    @action(detail=False, methods=["get"])
    def jobs(self, request):
        """Return the actual job objects the provider is watching"""
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
            job = Job.objects.get(pk=job_id)

            watched_job, created = WatchedJob.objects.get_or_create(
                job=job, provider=request.user
            )

            if not created:
                # If already watching, remove it (toggle off)
                watched_job.delete()
                return Response({"status": "job unwatched"})

            return Response({"status": "job watched"})

        except ObjectDoesNotExist:
            return Response(
                {"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND
            )
