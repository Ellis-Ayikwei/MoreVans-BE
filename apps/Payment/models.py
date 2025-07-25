from django.db import models
from apps.Basemodel.models import Basemodel
from apps.Request.models import Request
from apps.User.models import User


class PaymentMethod(Basemodel):
    """Model to store user payment methods for Stripe integration"""

    PAYMENT_TYPES = [
        ("card", "Credit/Debit Card"),
        ("bank", "Bank Transfer"),
        ("wallet", "Digital Wallet"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="payment_methods"
    )
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    is_default = models.BooleanField(default=False)
    last_used = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)

    # Stripe-specific fields
    stripe_payment_method_id = models.CharField(
        max_length=100, null=True, blank=True, unique=True
    )
    stripe_customer_id = models.CharField(max_length=100, null=True, blank=True)

    # For cards
    card_last_four = models.CharField(max_length=4, null=True, blank=True)
    card_brand = models.CharField(max_length=20, null=True, blank=True)
    card_expiry = models.DateField(null=True, blank=True)
    card_country = models.CharField(
        max_length=2, null=True, blank=True
    )  # ISO country code

    # For bank accounts
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    account_last_four = models.CharField(max_length=4, null=True, blank=True)

    class Meta:
        db_table = "payment_method"
        managed = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.payment_type}"


class Payment(Basemodel):
    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
        ("partially_refunded", "Partially Refunded"),
    ]

    PAYMENT_TYPE = [
        ("deposit", "Deposit"),
        ("full_payment", "Full Payment"),
        ("final_payment", "Final Payment"),
        ("additional_fee", "Additional Fee"),
        ("refund", "Refund"),
    ]

    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, related_name="payments"
    )
    payment_method = models.ForeignKey(
        PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=30, choices=PAYMENT_STATUS, default="pending")
    payment_type = models.CharField(
        max_length=20, choices=PAYMENT_TYPE, default="full_payment"
    )

    # Stripe-specific fields
    stripe_payment_intent_id = models.CharField(
        max_length=100, null=True, blank=True, unique=True
    )
    stripe_charge_id = models.CharField(max_length=100, null=True, blank=True)
    stripe_refund_id = models.CharField(max_length=100, null=True, blank=True)

    # Transaction ID (for checkout sessions, this will be the session ID)
    transaction_id = models.CharField(
        max_length=100, unique=True, null=True, blank=True
    )

    # Payment details
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    # Additional info
    description = models.TextField(blank=True)
    refund_reason = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)

    # Metadata for Stripe webhook handling
    metadata = models.JSONField(default=dict, blank=True)

    def mark_as_processing(self, payment_intent_id=None):
        """
        Mark payment as processing with optional Stripe payment intent ID.

        Args:
            payment_intent_id: Optional Stripe payment intent ID
        """
        if self.status not in ["pending"]:
            raise ValueError("Only pending payments can be marked as processing")

        self.status = "processing"
        if payment_intent_id:
            self.stripe_payment_intent_id = payment_intent_id
        self.save()

        self._create_payment_event("processing_started", "Payment processing started")

    def mark_as_succeeded(self, charge_id=None, transaction_details=None):
        """
        Mark payment as succeeded.

        Args:
            charge_id: Optional Stripe charge ID
            transaction_details: Optional dictionary with additional transaction details
        """
        if self.status not in ["processing", "pending"]:
            raise ValueError(
                "Only processing or pending payments can be marked as succeeded"
            )

        from django.utils import timezone

        self.status = "succeeded"
        self.completed_at = timezone.now()
        if charge_id:
            self.stripe_charge_id = charge_id
        if transaction_details:
            self.metadata.update(transaction_details)
        self.save()

        self._create_payment_event(
            "payment_succeeded", "Payment completed successfully"
        )

        # Trigger request payment completion
        if self.payment_type in ["full_payment", "final_payment"]:
            try:
                self.request.complete_payment()
                self.request.save()
            except Exception as e:
                # Log the error but don't prevent payment completion
                print(f"Error completing request payment: {str(e)}")

    def mark_as_failed(self, failure_reason=None, transaction_details=None):
        """
        Mark payment as failed.

        Args:
            failure_reason: Reason for payment failure
            transaction_details: Optional dictionary with additional transaction details
        """
        if self.status in ["succeeded", "refunded", "partially_refunded"]:
            raise ValueError("Cannot mark payment as failed in current state")

        from django.utils import timezone

        self.status = "failed"
        self.failed_at = timezone.now()
        if failure_reason:
            self.failure_reason = failure_reason
        if transaction_details:
            self.metadata.update(transaction_details)
        self.save()

        self._create_payment_event(
            "payment_failed", f"Payment failed: {failure_reason}"
        )

    def cancel_payment(self, reason=None):
        """
        Cancel a payment.

        Args:
            reason: Optional reason for cancellation
        """
        if self.status not in ["pending", "processing"]:
            raise ValueError("Only pending or processing payments can be cancelled")

        self.status = "cancelled"
        if reason:
            self.metadata["cancellation_reason"] = reason
        self.save()

        self._create_payment_event("payment_cancelled", f"Payment cancelled: {reason}")

    def process_refund(self, amount=None, reason=None, refund_id=None):
        """
        Process a refund for the payment.

        Args:
            amount: Amount to refund (if None, full refund)
            reason: Reason for refund
            refund_id: Optional Stripe refund ID
        """
        if self.status != "succeeded":
            raise ValueError("Only succeeded payments can be refunded")

        from django.utils import timezone

        # If amount is None or equals total amount, it's a full refund
        is_full_refund = amount is None or amount == self.amount

        self.status = "refunded" if is_full_refund else "partially_refunded"
        self.refunded_at = timezone.now()
        if refund_id:
            self.stripe_refund_id = refund_id
        if reason:
            self.refund_reason = reason

        # Store refund details in metadata
        refund_details = {
            "refund_amount": str(amount) if amount else str(self.amount),
            "refund_date": timezone.now().isoformat(),
            "refund_reason": reason,
        }
        self.metadata["refund_details"] = refund_details
        self.save()

        self._create_payment_event(
            "payment_refunded",
            f"{'Full' if is_full_refund else 'Partial'} refund processed: {reason}",
        )

    def _create_payment_event(self, event_type, description):
        """
        Create a payment event for tracking.

        Args:
            event_type: Type of payment event
            description: Description of the event
        """
        PaymentEvent.objects.create(
            payment=self,
            event_type=event_type,
            description=description,
            metadata={
                "payment_status": self.status,
                "payment_type": self.payment_type,
                "amount": str(self.amount),
                "currency": self.currency,
            },
        )

    @property
    def can_be_processed(self):
        """Check if payment can be processed"""
        return self.status == "pending"

    @property
    def can_be_cancelled(self):
        """Check if payment can be cancelled"""
        return self.status in ["pending", "processing"]

    @property
    def can_be_refunded(self):
        """Check if payment can be refunded"""
        return self.status == "succeeded"

    @property
    def is_complete(self):
        """Check if payment is complete"""
        return self.status == "succeeded"


class PaymentEvent(Basemodel):
    """Model to track payment events and status changes"""

    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="events"
    )
    event_type = models.CharField(max_length=50)
    description = models.TextField()
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = "payment_event"
        managed = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment Event {self.event_type} for Payment {self.payment.id}"


class StripeEvent(Basemodel):
    """Model to store Stripe webhook events to prevent duplicate processing"""

    stripe_event_id = models.CharField(max_length=100, unique=True)
    event_type = models.CharField(max_length=50)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "stripe_event"
        managed = True

    def __str__(self):
        return f"Stripe Event {self.stripe_event_id} - {self.event_type}"
