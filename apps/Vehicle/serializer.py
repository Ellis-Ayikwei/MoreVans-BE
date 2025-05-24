from rest_framework import serializers
from .models import Vehicle, VehicleDocument, VehicleInspection, MaintenanceRecord

class VehicleDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleDocument
        fields = ['id', 'vehicle', 'document_type', 'document_file', 'issue_date', 
                 'expiry_date', 'reference_number', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class VehicleInspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleInspection
        fields = ['id', 'vehicle', 'inspection_type', 'inspection_date', 'inspector_name',
                 'mileage_at_inspection', 'overall_condition', 'inspection_items',
                 'defects_found', 'actions_required', 'is_roadworthy', 'notes',
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class MaintenanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRecord
        fields = ['id', 'vehicle', 'maintenance_type', 'maintenance_date', 'mileage',
                 'work_performed', 'parts_replaced', 'performed_by', 'cost',
                 'invoice_reference', 'next_maintenance_date', 'next_maintenance_mileage',
                 'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class VehicleSerializer(serializers.ModelSerializer):
    is_mot_valid = serializers.BooleanField(read_only=True)
    is_road_tax_valid = serializers.BooleanField(read_only=True)
    is_service_due = serializers.BooleanField(read_only=True)
    load_dimensions = serializers.CharField(read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'registration', 'vin', 'make', 'model', 'year', 'vehicle_type',
            'fuel_type', 'transmission', 'color', 'payload_capacity_kg',
            'gross_vehicle_weight_kg', 'load_length_mm', 'load_width_mm',
            'load_height_mm', 'load_volume_m3', 'mot_expiry_date',
            'road_tax_expiry_date', 'has_tachograph', 'ulez_compliant',
            'clean_air_zone_status', 'insurance_policy_number', 'insurance_expiry_date',
            'fleet_number', 'last_service_date', 'next_service_date',
            'last_service_mileage', 'current_mileage', 'service_interval_months',
            'service_interval_miles', 'has_tail_lift', 'has_refrigeration',
            'has_tracking_device', 'has_dash_cam', 'additional_features',
            'provider', 'primary_driver', 'is_active', 'location',
            'last_location_update', 'is_available', 'is_mot_valid',
            'is_road_tax_valid', 'is_service_due', 'load_dimensions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

# Extended serializer that includes related data
class VehicleDetailSerializer(VehicleSerializer):
    documents = VehicleDocumentSerializer(many=True, read_only=True)
    inspections = VehicleInspectionSerializer(many=True, read_only=True)
    maintenance_records = MaintenanceRecordSerializer(many=True, read_only=True)
    
    class Meta(VehicleSerializer.Meta):
        fields = VehicleSerializer.Meta.fields + ['documents', 'inspections', 'maintenance_records']