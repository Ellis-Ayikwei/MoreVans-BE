from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import SystemSetting, PaymentGateway
from .serializers import (
    SystemSettingSerializer,
    PaymentGatewaySerializer,
    SystemSettingsSerializer,
)
import json


class SystemSettingsViewSet(viewsets.ModelViewSet):
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def get_all_settings(self, request):
        """Get all system settings organized by section"""
        settings = SystemSetting.objects.filter(is_active=True)
        payment_gateways = PaymentGateway.objects.all()

        # Organize settings by section
        organized_settings = {
            "general": {},
            "notifications": {},
            "payment": {},
            "appearance": {},
        }

        for setting in settings:
            organized_settings[setting.section][setting.key] = setting.get_value()

        # Add payment gateways to payment section
        organized_settings["payment"]["paymentGateways"] = PaymentGatewaySerializer(
            payment_gateways, many=True
        ).data

        return Response(organized_settings)

    @action(detail=False, methods=["post"])
    def update_settings(self, request):
        """Update multiple system settings"""
        try:
            with transaction.atomic():
                data = request.data

                # Update general settings
                if "general" in data:
                    self._update_section_settings("general", data["general"])

                # Update notification settings
                if "notifications" in data:
                    self._update_section_settings(
                        "notifications", data["notifications"]
                    )

                # Update payment settings
                if "payment" in data:
                    payment_data = data["payment"]

                    # Handle payment gateways separately
                    if "paymentGateways" in payment_data:
                        self._update_payment_gateways(payment_data["paymentGateways"])
                        payment_data.pop("paymentGateways")

                    self._update_section_settings("payment", payment_data)

                # Update appearance settings
                if "appearance" in data:
                    self._update_section_settings("appearance", data["appearance"])

                return Response({"message": "Settings updated successfully"})

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _update_section_settings(self, section, settings_data):
        """Update settings for a specific section"""
        for key, value in settings_data.items():
            # Determine data type
            data_type = "string"
            if isinstance(value, bool):
                data_type = "boolean"
            elif isinstance(value, int):
                data_type = "integer"
            elif isinstance(value, float):
                data_type = "float"
            elif isinstance(value, (dict, list)):
                data_type = "json"

            setting, created = SystemSetting.objects.get_or_create(
                section=section,
                key=key,
                defaults={"data_type": data_type, "is_active": True},
            )

            setting.data_type = data_type
            setting.set_value(value)
            setting.save()

    def _update_payment_gateways(self, gateways_data):
        """Update payment gateway configurations"""
        for gateway_data in gateways_data:
            gateway_id = gateway_data.get("id") or gateway_data.get("gateway_id")

            gateway, created = PaymentGateway.objects.get_or_create(
                gateway_id=gateway_id,
                defaults={
                    "name": gateway_data.get("name", gateway_id),
                    "is_active": False,
                    "test_mode": True,
                },
            )

            # Update gateway fields
            gateway.name = gateway_data.get("name", gateway.name)
            gateway.is_active = gateway_data.get("isActive", gateway.is_active)
            gateway.test_mode = gateway_data.get("testMode", gateway.test_mode)

            # Update credentials
            credentials = gateway_data.get("credentials", {})
            gateway.api_key = credentials.get("apiKey", gateway.api_key)
            gateway.secret_key = credentials.get("secretKey", gateway.secret_key)
            gateway.merchant_id = credentials.get("merchantId", gateway.merchant_id)

            gateway.save()


class PaymentGatewayViewSet(viewsets.ModelViewSet):
    queryset = PaymentGateway.objects.all()
    serializer_class = PaymentGatewaySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def toggle_status(self, request, pk=None):
        """Toggle payment gateway active status"""
        gateway = self.get_object()
        gateway.is_active = not gateway.is_active
        gateway.save()

        return Response(
            {
                "message": f'Gateway {gateway.name} {"activated" if gateway.is_active else "deactivated"}',
                "is_active": gateway.is_active,
            }
        )
