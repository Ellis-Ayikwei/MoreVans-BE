from rest_framework import serializers
from .models import PaymentMethod, Payment, StripeEvent

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'user', 'payment_type', 'is_default', 'created_at', 
            'last_used', 'is_active', 'stripe_payment_method_id', 'stripe_customer_id',
            'card_last_four', 'card_brand', 'card_expiry', 'card_country',
            'bank_name', 'account_last_four'
        ]
        read_only_fields = ['created_at', 'stripe_payment_method_id', 'stripe_customer_id']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'request', 'payment_method', 'amount', 'currency', 'status', 
            'payment_type', 'stripe_payment_intent_id', 'stripe_charge_id', 
            'stripe_refund_id', 'transaction_id', 'created_at', 'completed_at', 
            'failed_at', 'refunded_at', 'description', 'refund_reason', 
            'failure_reason', 'metadata'
        ]
        read_only_fields = [
            'created_at', 'stripe_payment_intent_id', 'stripe_charge_id', 
            'stripe_refund_id', 'completed_at', 'failed_at', 'refunded_at'
        ]

class StripeEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = StripeEvent
        fields = [
            'id', 'stripe_event_id', 'event_type', 'processed', 
            'processed_at', 'created_at'
        ]
        read_only_fields = ['created_at', 'processed_at']

class CreateCheckoutSessionSerializer(serializers.Serializer):
    """Serializer for creating Stripe checkout sessions"""
    request_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3, default='USD')
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()
    description = serializers.CharField(max_length=500, required=False)
    
    def validate_currency(self, value):
        """Validate currency code"""
        valid_currencies = ['USD', 'EUR', 'GBP', 'GHS']  # Add more as needed
        if value.upper() not in valid_currencies:
            raise serializers.ValidationError(f"Currency {value} is not supported")
        return value.upper()

    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value

class CreateRefundSerializer(serializers.Serializer):
    """Serializer for creating refunds"""
    payment_intent_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    reason = serializers.CharField(max_length=500, required=False)

    def validate_amount(self, value):
        """Validate refund amount is positive if provided"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Refund amount must be greater than 0")
        return value