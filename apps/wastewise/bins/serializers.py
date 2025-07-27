"""
Serializers for WasteWise Bins API

These serializers handle the conversion between Django models and JSON
for the REST API endpoints.
"""

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import Point
from .models import Zone, WasteBin, BinMaintenanceLog, BinCollectionHistory


class ZoneSerializer(GeoFeatureModelSerializer):
    """Serializer for Zone model with GeoJSON support"""
    
    bin_count = serializers.ReadOnlyField()
    average_fill_level = serializers.ReadOnlyField()
    
    class Meta:
        model = Zone
        geo_field = "boundary"
        fields = [
            'id', 'name', 'code', 'description', 'population', 'area_sq_km',
            'supervisor', 'is_active', 'created_at', 'updated_at',
            'bin_count', 'average_fill_level'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'bin_count', 'average_fill_level']


class ZoneListSerializer(serializers.ModelSerializer):
    """Simplified serializer for zone listings"""
    
    bin_count = serializers.ReadOnlyField()
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    
    class Meta:
        model = Zone
        fields = ['id', 'name', 'code', 'population', 'bin_count', 'supervisor_name', 'is_active']


class WasteBinSerializer(GeoFeatureModelSerializer):
    """Serializer for WasteBin model with GeoJSON support"""
    
    # Computed fields
    current_fill_level = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    is_overflowing = serializers.ReadOnlyField()
    days_since_emptied = serializers.ReadOnlyField()
    needs_collection = serializers.ReadOnlyField()
    latitude = serializers.ReadOnlyField()
    longitude = serializers.ReadOnlyField()
    
    # Nested fields
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    zone_code = serializers.CharField(source='zone.code', read_only=True)
    
    # Custom coordinate fields for easier frontend handling
    coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = WasteBin
        geo_field = "location"
        fields = [
            'id', 'bin_id', 'address', 'zone', 'zone_name', 'zone_code',
            'bin_type', 'bin_size', 'capacity_liters', 'status',
            'installation_date', 'last_emptied', 'last_maintenance',
            'sensor_id', 'is_smart_bin', 'collection_frequency_days',
            'priority_level', 'is_active', 'notes',
            'current_fill_level', 'is_full', 'is_overflowing',
            'days_since_emptied', 'needs_collection',
            'latitude', 'longitude', 'coordinates',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'current_fill_level', 'is_full', 'is_overflowing',
            'days_since_emptied', 'needs_collection', 'latitude', 'longitude',
            'coordinates', 'created_at', 'updated_at'
        ]
    
    def get_coordinates(self, obj):
        """Return coordinates as [longitude, latitude] array"""
        if obj.location:
            return [obj.location.x, obj.location.y]
        return None
    
    def validate_location(self, value):
        """Validate that location is within acceptable bounds for Accra"""
        if value:
            # Rough bounds for Accra, Ghana
            accra_bounds = {
                'min_lat': 5.5,
                'max_lat': 5.7,
                'min_lng': -0.3,
                'max_lng': 0.0
            }
            
            if not (accra_bounds['min_lat'] <= value.y <= accra_bounds['max_lat']):
                raise serializers.ValidationError("Location must be within Accra bounds")
            if not (accra_bounds['min_lng'] <= value.x <= accra_bounds['max_lng']):
                raise serializers.ValidationError("Location must be within Accra bounds")
        
        return value


class WasteBinListSerializer(serializers.ModelSerializer):
    """Simplified serializer for bin listings"""
    
    current_fill_level = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = WasteBin
        fields = [
            'id', 'bin_id', 'bin_type', 'status', 'status_display',
            'current_fill_level', 'zone_name', 'coordinates', 'needs_collection'
        ]
    
    def get_coordinates(self, obj):
        if obj.location:
            return [obj.location.x, obj.location.y]
        return None


class WasteBinCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new waste bins"""
    
    # Accept coordinates as separate fields for easier frontend handling
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)
    
    class Meta:
        model = WasteBin
        fields = [
            'bin_id', 'address', 'zone', 'bin_type', 'bin_size',
            'capacity_liters', 'installation_date', 'sensor_id',
            'is_smart_bin', 'collection_frequency_days', 'priority_level',
            'notes', 'latitude', 'longitude'
        ]
    
    def create(self, validated_data):
        """Create bin with Point geometry from coordinates"""
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        
        validated_data['location'] = Point(longitude, latitude)
        
        return super().create(validated_data)


class BinMaintenanceLogSerializer(serializers.ModelSerializer):
    """Serializer for bin maintenance logs"""
    
    maintenance_type_display = serializers.CharField(source='get_maintenance_type_display', read_only=True)
    technician_name = serializers.CharField(source='technician.get_full_name', read_only=True)
    bin_id = serializers.CharField(source='bin.bin_id', read_only=True)
    duration_hours = serializers.ReadOnlyField()
    
    class Meta:
        model = BinMaintenanceLog
        fields = [
            'id', 'bin', 'bin_id', 'maintenance_type', 'maintenance_type_display',
            'description', 'cost', 'technician', 'technician_name',
            'scheduled_date', 'started_at', 'completed_at', 'duration_hours',
            'is_completed', 'notes', 'photos', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'duration_hours', 'created_at', 'updated_at']


class BinCollectionHistorySerializer(serializers.ModelSerializer):
    """Serializer for bin collection history"""
    
    collected_by_name = serializers.CharField(source='collected_by.get_full_name', read_only=True)
    vehicle_id = serializers.CharField(source='vehicle.vehicle_id', read_only=True)
    route_name = serializers.CharField(source='route.name', read_only=True)
    bin_id = serializers.CharField(source='bin.bin_id', read_only=True)
    bin_condition_display = serializers.CharField(source='get_bin_condition_display', read_only=True)
    
    class Meta:
        model = BinCollectionHistory
        fields = [
            'id', 'bin', 'bin_id', 'collected_at', 'collected_by', 'collected_by_name',
            'vehicle', 'vehicle_id', 'route', 'route_name', 'fill_level_before',
            'estimated_weight_kg', 'collection_duration_minutes', 'bin_condition',
            'bin_condition_display', 'notes', 'photos', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BinStatisticsSerializer(serializers.Serializer):
    """Serializer for bin statistics"""
    
    total_bins = serializers.IntegerField()
    active_bins = serializers.IntegerField()
    full_bins = serializers.IntegerField()
    overflowing_bins = serializers.IntegerField()
    offline_bins = serializers.IntegerField()
    average_fill_level = serializers.FloatField()
    bins_needing_collection = serializers.IntegerField()
    
    # By bin type
    bins_by_type = serializers.DictField()
    
    # By zone
    bins_by_zone = serializers.DictField()


class NearbyBinsSerializer(serializers.Serializer):
    """Serializer for nearby bins search"""
    
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    radius_km = serializers.FloatField(default=1.0, min_value=0.1, max_value=10.0)
    bin_type = serializers.CharField(required=False)
    only_available = serializers.BooleanField(default=True)


class BinAlertSerializer(serializers.Serializer):
    """Serializer for bin alerts"""
    
    bin_id = serializers.CharField()
    alert_type = serializers.ChoiceField(choices=[
        ('full', 'Bin Full'),
        ('overflow', 'Bin Overflow'),
        ('damage', 'Bin Damaged'),
        ('missing', 'Bin Missing'),
        ('blocked', 'Access Blocked'),
    ])
    description = serializers.CharField()
    priority = serializers.ChoiceField(
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )
    reporter_location = serializers.CharField(required=False)
    photos = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of photo URLs"
    )


class BinCollectionRequestSerializer(serializers.Serializer):
    """Serializer for requesting bin collection"""
    
    bin_ids = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        help_text="List of bin IDs to collect"
    )
    priority = serializers.ChoiceField(
        choices=[('normal', 'Normal'), ('urgent', 'Urgent'), ('emergency', 'Emergency')],
        default='normal'
    )
    requested_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False)


class BinStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating bin status"""
    
    status = serializers.ChoiceField(choices=WasteBin.STATUS_CHOICES)
    notes = serializers.CharField(required=False)
    
    def validate_status(self, value):
        """Validate status transition"""
        instance = self.instance
        if instance:
            # Define valid status transitions
            valid_transitions = {
                'active': ['maintenance', 'damaged', 'full', 'offline'],
                'maintenance': ['active', 'damaged'],
                'damaged': ['maintenance', 'active'],
                'full': ['active'],
                'offline': ['active', 'maintenance'],
            }
            
            current_status = instance.status
            if current_status in valid_transitions:
                if value not in valid_transitions[current_status]:
                    raise serializers.ValidationError(
                        f"Cannot change status from {current_status} to {value}"
                    )
        
        return value