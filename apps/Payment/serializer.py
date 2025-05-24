from rest_framework import serializers
from .models import PaymentMethod, Payment

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'user', 'payment_type', 'is_default', 'created_at', 
                 'last_used', 'is_active', 'card_last_four', 'card_brand', 
                 'card_expiry', 'bank_name', 'account_last_four']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'request', 'payment_method', 'amount', 'status', 
                 'transaction_id', 'created_at', 'completed_at', 'refund_reason']