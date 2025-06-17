from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
import json
import logging

from .models import PaymentMethod, Payment, StripeEvent
from .serializer import (
    PaymentMethodSerializer,
    PaymentSerializer,
    CreateRefundSerializer,
)
from .stripe_service import StripeService
from apps.Job.models import Job
from apps.Job.serializers import JobSerializer
from apps.Job.services import JobService
from apps.Request.models import Request
import uuid

logger = logging.getLogger(__name__)


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing PaymentMethod instances.
    Admins can see all payment methods, regular users only see their own.
    """

    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer

    def get_queryset(self):
        # Check if user is admin
        is_admin = (
            self.request.user.is_staff
            or self.request.user.is_superuser
            or getattr(self.request.user, "user_type", None) == "admin"
        )

        if is_admin:
            # Admins can see all payment methods
            queryset = PaymentMethod.objects.all()

            # Optional filter by specific user if provided
            user_id = self.request.query_params.get("user_id", None)
            if user_id:
                queryset = queryset.filter(user_id=user_id)
        else:
            # Regular users only see their own payment methods
            queryset = PaymentMethod.objects.filter(user=self.request.user)

        return queryset.select_related("user").order_by("-created_at")

    @action(detail=True, methods=["post"])
    def set_as_default(self, request, pk=None):
        """
        Set a payment method as the default for a user.
        """
        payment_method = self.get_object()

        # Check permissions
        is_admin = (
            request.user.is_staff
            or request.user.is_superuser
            or getattr(request.user, "user_type", None) == "admin"
        )

        if not is_admin and payment_method.user != request.user:
            return Response(
                {"detail": "You can only modify your own payment methods."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # First, reset all payment methods for this user
        PaymentMethod.objects.filter(user=payment_method.user, is_default=True).update(
            is_default=False
        )

        # Set this one as default
        payment_method.is_default = True
        payment_method.save()

        return Response(
            {
                "detail": "Payment method set as default",
                "payment_method": self.get_serializer(payment_method).data,
            }
        )

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAdminUser])
    def admin_overview(self, request):
        """
        Get payment method statistics for admins
        """
        from django.db.models import Count

        stats = {
            "total_payment_methods": PaymentMethod.objects.count(),
            "active_payment_methods": PaymentMethod.objects.filter(
                is_active=True
            ).count(),
            "default_payment_methods": PaymentMethod.objects.filter(
                is_default=True
            ).count(),
            "by_type": PaymentMethod.objects.values("stripe_payment_method_type")
            .annotate(count=Count("id"))
            .order_by("stripe_payment_method_type"),
            "recent_additions": PaymentMethod.objects.select_related("user")
            .order_by("-created_at")[:10]
            .values(
                "id",
                "user__email",
                "stripe_payment_method_type",
                "is_default",
                "is_active",
                "created_at",
            ),
        }

        return Response(stats)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Payment instances.
    Admins can see all payments, regular users only see their own.
    """

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Payment.objects.all()
        request_id = self.request.query_params.get("request", None)
        status_param = self.request.query_params.get("status", None)
        user_id = self.request.query_params.get("user_id", None)

        # Check if user is admin (can see all payments)
        is_admin = (
            self.request.user.is_staff
            or self.request.user.is_superuser
            or getattr(self.request.user, "user_type", None) == "admin"
        )

        if not is_admin:
            # Regular users only see their own payments
            queryset = queryset.filter(request__user=self.request.user)
        else:
            # Admin users can see all payments
            # Optional filter by specific user if provided
            if user_id:
                queryset = queryset.filter(request__user_id=user_id)

        # Apply additional filters
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset.select_related("request", "request__user").order_by(
            "-created_at"
        )

    def get_permissions(self):
        """
        Instantiate and return the list of permissions that this view requires.
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            # Only admins can create/update/delete payments directly
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAdminUser])
    def admin_stats(self, request):
        """
        Get payment statistics for admins
        """
        from django.db.models import Count, Sum, Avg
        from datetime import datetime, timedelta

        queryset = Payment.objects.all()

        # Get date range from query params (default to last 30 days)
        days = int(request.query_params.get("days", 30))
        start_date = datetime.now() - timedelta(days=days)
        queryset = queryset.filter(created_at__gte=start_date)

        stats = {
            "total_payments": queryset.count(),
            "total_amount": queryset.aggregate(Sum("amount"))["amount__sum"] or 0,
            "average_amount": queryset.aggregate(Avg("amount"))["amount__avg"] or 0,
            "by_status": queryset.values("status")
            .annotate(count=Count("id"), total_amount=Sum("amount"))
            .order_by("status"),
            "by_currency": queryset.values("currency")
            .annotate(count=Count("id"), total_amount=Sum("amount"))
            .order_by("currency"),
            "recent_payments": queryset.order_by("-created_at")[:10].values(
                "id",
                "amount",
                "currency",
                "status",
                "created_at",
                "request__tracking_number",
                "request__user__email",
            ),
        }

        return Response(stats)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAdminUser])
    def failed_payments(self, request):
        """
        Get all failed payments for admin review
        """
        failed_payments = (
            Payment.objects.filter(status__in=["failed", "cancelled"])
            .select_related("request", "request__user")
            .order_by("-created_at")
        )

        # Add pagination
        page = self.paginate_queryset(failed_payments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(failed_payments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAdminUser])
    def pending_payments(self, request):
        """
        Get all pending payments for admin monitoring
        """
        pending_payments = (
            Payment.objects.filter(status__in=["pending", "processing"])
            .select_related("request", "request__user")
            .order_by("-created_at")
        )

        # Add pagination
        page = self.paginate_queryset(pending_payments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(pending_payments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def admin_refund(self, request, pk=None):
        """
        Allow admin to process refunds
        """
        payment = self.get_object()

        if payment.status != "completed":
            return Response(
                {"detail": "Only completed payments can be refunded"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CreateRefundSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        stripe_service = StripeService()
        result = stripe_service.create_refund(
            payment_intent_id=payment.stripe_payment_intent_id,
            amount=serializer.validated_data.get("amount"),
            reason=serializer.validated_data.get("reason", "requested_by_customer"),
        )

        if result:
            # Update payment record
            if serializer.validated_data.get("amount"):
                payment.status = "partially_refunded"
            else:
                payment.status = "refunded"
            payment.refunded_at = timezone.now()
            payment.refund_reason = serializer.validated_data.get(
                "reason", "Admin processed refund"
            )
            payment.save()

            return Response(
                {
                    "detail": "Refund processed successfully",
                    "refund": result,
                    "payment_status": payment.status,
                }
            )
        else:
            return Response(
                {"detail": "Failed to create refund"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True, methods=["patch"], permission_classes=[permissions.IsAdminUser]
    )
    def update_status(self, request, pk=None):
        """
        Allow admin to manually update payment status
        """
        payment = self.get_object()
        new_status = request.data.get("status")
        admin_note = request.data.get("admin_note", "")

        if not new_status:
            return Response(
                {"detail": "status is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate status
        valid_statuses = [
            "pending",
            "processing",
            "completed",
            "failed",
            "cancelled",
            "refunded",
            "partially_refunded",
        ]
        if new_status not in valid_statuses:
            return Response(
                {
                    "detail": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = payment.status
        payment.status = new_status

        # Add admin note to metadata
        if not payment.metadata:
            payment.metadata = {}
        payment.metadata["admin_updates"] = payment.metadata.get("admin_updates", [])
        payment.metadata["admin_updates"].append(
            {
                "timestamp": timezone.now().isoformat(),
                "admin": request.user.email,
                "old_status": old_status,
                "new_status": new_status,
                "note": admin_note,
            }
        )

        payment.save()

        return Response(
            {
                "detail": f"Payment status updated from {old_status} to {new_status}",
                "payment": self.get_serializer(payment).data,
            }
        )

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def create_checkout_session(self, request):
        """
        Create a Stripe Checkout Session for payment
        """
        print("the request data is   .................  :", request.data)
        # Validate required fields
        request_id = request.data.get("request_id")
        amount = request.data.get("amount")
        user_id = request.data.get(
            "user_id", request.user.id if request.user.is_authenticated else None
        )
        currency = request.data.get("currency", "USD")
        success_url = request.data.get("success_url")
        cancel_url = request.data.get("cancel_url")
        description = request.data.get("description")

        if not request_id:
            return Response(
                {"detail": "request_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not amount:
            return Response(
                {"detail": "amount is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not success_url or not cancel_url:
            return Response(
                {"detail": "success_url and cancel_url are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get the request object
            request_obj = Request.objects.get(id=request_id, user=user_id)
        except Request.DoesNotExist:
            return Response(
                {"detail": "Request not found before checkout creation"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if there's already a pending payment for this request
        existing_payment = Payment.objects.filter(
            request=request_obj, status__in=["pending", "processing"]
        ).first()

        if existing_payment:
            return Response(
                {"detail": "There is already a pending payment for this request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stripe_service = StripeService()
        if user_id:
            # Get the actual user object from user_id
            from django.contrib.auth import get_user_model

            User = get_user_model()

            try:
                actual_user = User.objects.get(id=user_id)
                print(f"Found user: {actual_user.email}")
            except User.DoesNotExist:
                return Response(
                    {"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Get request with specific user
            try:
                request_obj = Request.objects.get(id=request_id, user=actual_user)
                print(f"Found request for user: {request_obj.id}")
            except Request.DoesNotExist:
                return Response(
                    {"detail": "Request not found for this user"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        # Create checkout session
        print(f"Creating checkout session for user: {actual_user.email}")
        result = stripe_service.create_checkout_session(
            amount=float(amount),
            currency=currency,
            user=actual_user,
            request_obj=request_obj,
            success_url=success_url,
            cancel_url=cancel_url,
            description=description,
        )

        if result:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"detail": "Failed to create checkout session"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["post"])
    def create_refund(self, request):
        """
        Create a refund for a payment (user-initiated)
        """
        serializer = CreateRefundSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payment_intent_id = serializer.validated_data["payment_intent_id"]

        # Verify payment belongs to current user
        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent_id, request__user=request.user
            )
        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if payment is refundable
        if payment.status != "completed":
            return Response(
                {"detail": "Only completed payments can be refunded"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stripe_service = StripeService()
        result = stripe_service.create_refund(
            payment_intent_id=payment_intent_id,
            amount=serializer.validated_data.get("amount"),
            reason=serializer.validated_data.get("reason"),
        )

        if result:
            # Update payment record
            if serializer.validated_data.get("amount"):
                payment.status = "partially_refunded"
            else:
                payment.status = "refunded"
            payment.refunded_at = timezone.now()
            payment.refund_reason = serializer.validated_data.get("reason", "")
            payment.save()

            return Response(result)
        else:
            return Response(
                {"detail": "Failed to create refund"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"])
    def check_session_status(self, request):
        """
        Check the status of a checkout session
        """
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"detail": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        stripe_service = StripeService()
        result = stripe_service.retrieve_checkout_session(session_id)

        if result:
            return Response(result)
        else:
            return Response(
                {"detail": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    """
    Handle Stripe webhook events
    """

    permission_classes = []  # No authentication required for webhooks

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        if not sig_header:
            logger.error("No Stripe signature header found")
            return Response(
                {"detail": "No signature header"}, status=status.HTTP_400_BAD_REQUEST
            )

        stripe_service = StripeService()
        print("hit the webhook")
        result = stripe_service.handle_webhook_event(payload, sig_header)

        if result is None:
            return Response(
                {"detail": "Invalid webhook"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(result)


class StripeConfigView(APIView):
    """
    Return Stripe publishable key for frontend
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.conf import settings

        return Response(
            {
                "publishable_key": getattr(settings, "STRIPE_PUBLISHABLE_KEY", ""),
                "currency": getattr(settings, "STRIPE_CURRENCY", "usd"),
                "supported_currencies": getattr(
                    settings, "STRIPE_SUPPORTED_CURRENCIES", ["usd", "eur", "gbp"]
                ),
                "success_url": getattr(settings, "PAYMENT_SUCCESS_URL", ""),
                "cancel_url": getattr(settings, "PAYMENT_CANCEL_URL", ""),
            }
        )


# Legacy view for backward compatibility
@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Legacy webhook endpoint - redirects to new endpoint
    """
    return HttpResponse("Use /api/payments/webhook/ endpoint", status=410)
