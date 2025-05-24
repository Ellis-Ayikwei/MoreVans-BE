from rest_framework import serializers
from .models import Location

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'address', 'postcode', 'latitude', 'longitude', 
                 'contact_name', 'contact_phone', 'special_instructions']