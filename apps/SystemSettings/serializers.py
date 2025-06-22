from rest_framework import serializers
from .models import SystemSetting, PaymentGateway


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = [
            "id",
            "section",
            "key",
            "value",
            "data_type",
            "description",
            "is_active",
        ]


class PaymentGatewaySerializer(serializers.ModelSerializer):
    credentials = serializers.SerializerMethodField()

    class Meta:
        model = PaymentGateway
        fields = ["id", "gateway_id", "name", "is_active", "test_mode", "credentials"]

    def get_credentials(self, obj):
        return {
            "api_key": obj.api_key,
            "secret_key": obj.secret_key,
            "merchant_id": obj.merchant_id,
        }


class SystemSettingsSerializer(serializers.Serializer):
    """Serializer for complete system settings structure"""

    general = serializers.DictField()
    notifications = serializers.DictField()
    payment = serializers.DictField()
    appearance = serializers.DictField()

    def validate(self, data):
        # Add validation logic here if needed
        return data
