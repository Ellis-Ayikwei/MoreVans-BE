from rest_framework import serializers
from apps.Driver.models import Driver, DriverLocation, DriverAvailability, DriverDocument, DriverInfringement

class DriverSerializer(serializers.ModelSerializer):
    is_license_valid = serializers.BooleanField(read_only=True)
    is_cpc_valid = serializers.BooleanField(read_only=True)
    needs_license_renewal = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Driver
        fields = [
            'id', 'user', 'name', 'email', 'phone_number', 'date_of_birth', 
            'national_insurance_number', 'address', 'postcode', 'location', 
            'last_location_update', 'provider', 'employment_type', 'date_started', 
            'license_number', 'license_country_of_issue', 'license_categories', 
            'license_expiry_date', 'digital_tachograph_card_number', 'tacho_card_expiry_date', 
            'has_cpc', 'cpc_expiry_date', 'has_adr', 'adr_expiry_date', 
            'induction_completed', 'induction_date', 'max_weekly_hours', 
            'opted_out_of_working_time_directive', 'status', 'penalty_points', 
            'preferred_vehicle_types', 'notes', 'is_license_valid', 'is_cpc_valid', 
            'needs_license_renewal', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class DriverLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverLocation
        fields = ['id', 'driver', 'location', 'timestamp', 'speed', 'heading', 'accuracy']
        read_only_fields = ['timestamp']

class DriverAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverAvailability
        fields = ['id', 'driver', 'date', 'time_slots', 'service_areas', 'max_jobs', 'notes', 
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class DriverDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverDocument
        fields = ['id', 'driver', 'document_type', 'document_file', 'issue_date', 
                 'expiry_date', 'reference_number', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class DriverInfringementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverInfringement
        fields = ['id', 'driver', 'infringement_type', 'infringement_date', 'description', 
                 'penalty_points_added', 'fine_amount', 'reported_by', 'is_resolved', 
                 'resolution_date', 'resolution_notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

# Extended serializer that includes related data
class DriverDetailSerializer(DriverSerializer):
    documents = DriverDocumentSerializer(many=True, read_only=True)
    infringements = DriverInfringementSerializer(many=True, read_only=True)
    availability_slots = DriverAvailabilitySerializer(many=True, read_only=True)
    
    class Meta(DriverSerializer.Meta):
        fields = DriverSerializer.Meta.fields + ['documents', 'infringements', 'availability_slots']

