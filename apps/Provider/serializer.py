from rest_framework import serializers
from .models import ServiceProvider, ServiceArea, InsurancePolicy, ProviderVehicle

class ServiceAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceArea
        fields = ['id', 'provider', 'name', 'area', 'is_primary', 'price_multiplier']

class InsurancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsurancePolicy
        fields = ['id', 'provider', 'policy_type', 'coverage_amount', 
                 'policy_number', 'expiry_date']

class ProviderVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderVehicle
        fields = ['id', 'provider', 'vehicle_type', 'registration', 
                 'make_model', 'year', 'max_load_kg']

class ServiceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProvider
        fields = ['id', 'user', 'business_type', 'company_name', 
                 'company_reg_number', 'vat_registered', 'vat_number', 
                 'business_description', 'service_categories', 
                 'specializations', 'service_image', 'base_location', 
                 'hourly_rate', 'accepts_instant_bookings', 
                 'service_radius_km', 'minimum_job_value', 
                 'verification_status', 'last_verified']