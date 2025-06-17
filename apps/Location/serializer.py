from rest_framework import serializers
from .models import Location
from decimal import Decimal, InvalidOperation

class LocationSerializer(serializers.ModelSerializer):
    latitude = serializers.DecimalField(
        max_digits=20,  # Increased to handle larger numbers
        decimal_places=16,  # Increased to handle more precise coordinates
        required=False,
        allow_null=True,
        coerce_to_string=False
    )
    longitude = serializers.DecimalField(
        max_digits=20,  # Increased to handle larger numbers
        decimal_places=16,  # Increased to handle more precise coordinates
        required=False,
        allow_null=True,
        coerce_to_string=False
    )

    class Meta:
        model = Location
        fields = ['id', 'address', 'postcode', 'latitude', 'longitude', 
                 'contact_name', 'contact_phone', 'special_instructions']
        extra_kwargs = {
            'address': {'required': False, 'allow_blank': True},
            'postcode': {'required': False, 'allow_blank': True},
            'contact_name': {'required': False, 'allow_blank': True},
            'contact_phone': {'required': False, 'allow_blank': True},
            'special_instructions': {'required': False, 'allow_blank': True}
        }

    def validate_latitude(self, value):
        if value is not None:
            try:
                # Convert to Decimal and round to 16 decimal places
                decimal_value = Decimal(str(value))
                # Ensure latitude is between -90 and 90
                if decimal_value < -90 or decimal_value > 90:
                    raise serializers.ValidationError("Latitude must be between -90 and 90 degrees")
                return round(decimal_value, 16)
            except (InvalidOperation, TypeError):
                raise serializers.ValidationError("Invalid latitude value")
        return value

    def validate_longitude(self, value):
        if value is not None:
            try:
                # Convert to Decimal and round to 16 decimal places
                decimal_value = Decimal(str(value))
                # Ensure longitude is between -180 and 180
                if decimal_value < -180 or decimal_value > 180:
                    raise serializers.ValidationError("Longitude must be between -180 and 180 degrees")
                return round(decimal_value, 16)
            except (InvalidOperation, TypeError):
                raise serializers.ValidationError("Invalid longitude value")
        return value

    def validate(self, data):
        # Ensure coordinates are properly formatted
        if 'latitude' in data and data['latitude'] is not None:
            data['latitude'] = self.validate_latitude(data['latitude'])
        if 'longitude' in data and data['longitude'] is not None:
            data['longitude'] = self.validate_longitude(data['longitude'])
        return data