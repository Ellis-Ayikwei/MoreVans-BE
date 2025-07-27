"""
Filters for WasteWise Bins API

Django filters for filtering waste bins and zones based on various criteria.
"""

import django_filters
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from .models import Zone, WasteBin, BinMaintenanceLog, BinCollectionHistory


class ZoneFilter(django_filters.FilterSet):
    """Filter set for Zone model"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.CharFilter(lookup_expr='iexact')
    supervisor = django_filters.UUIDFilter(field_name='supervisor__id')
    population_min = django_filters.NumberFilter(field_name='population', lookup_expr='gte')
    population_max = django_filters.NumberFilter(field_name='population', lookup_expr='lte')
    area_min = django_filters.NumberFilter(field_name='area_sq_km', lookup_expr='gte')
    area_max = django_filters.NumberFilter(field_name='area_sq_km', lookup_expr='lte')
    
    class Meta:
        model = Zone
        fields = ['is_active']


class WasteBinFilter(django_filters.FilterSet):
    """Filter set for WasteBin model"""
    
    # Basic filters
    bin_id = django_filters.CharFilter(lookup_expr='icontains')
    bin_type = django_filters.ChoiceFilter(choices=WasteBin.BIN_TYPES)
    bin_size = django_filters.ChoiceFilter(choices=WasteBin.BIN_SIZES)
    status = django_filters.ChoiceFilter(choices=WasteBin.STATUS_CHOICES)
    zone = django_filters.UUIDFilter(field_name='zone__id')
    zone_code = django_filters.CharFilter(field_name='zone__code', lookup_expr='iexact')
    
    # Capacity filters
    capacity_min = django_filters.NumberFilter(field_name='capacity_liters', lookup_expr='gte')
    capacity_max = django_filters.NumberFilter(field_name='capacity_liters', lookup_expr='lte')
    
    # Date filters
    installation_date_after = django_filters.DateFilter(field_name='installation_date', lookup_expr='gte')
    installation_date_before = django_filters.DateFilter(field_name='installation_date', lookup_expr='lte')
    last_emptied_after = django_filters.DateTimeFilter(field_name='last_emptied', lookup_expr='gte')
    last_emptied_before = django_filters.DateTimeFilter(field_name='last_emptied', lookup_expr='lte')
    
    # Smart bin filters
    is_smart_bin = django_filters.BooleanFilter()
    has_sensor = django_filters.BooleanFilter(field_name='sensor_id', lookup_expr='isnull', exclude=True)
    
    # Priority and collection filters
    priority_min = django_filters.NumberFilter(field_name='priority_level', lookup_expr='gte')
    priority_max = django_filters.NumberFilter(field_name='priority_level', lookup_expr='lte')
    collection_frequency_min = django_filters.NumberFilter(field_name='collection_frequency_days', lookup_expr='gte')
    collection_frequency_max = django_filters.NumberFilter(field_name='collection_frequency_days', lookup_expr='lte')
    
    # Special filters
    needs_collection = django_filters.BooleanFilter(method='filter_needs_collection')
    is_full = django_filters.BooleanFilter(method='filter_is_full')
    is_overflowing = django_filters.BooleanFilter(method='filter_is_overflowing')
    
    # Location-based filters
    near_point = django_filters.CharFilter(method='filter_near_point')
    within_radius = django_filters.NumberFilter(method='filter_within_radius')
    
    class Meta:
        model = WasteBin
        fields = ['is_active']
    
    def filter_needs_collection(self, queryset, name, value):
        """Filter bins that need collection"""
        if value:
            return queryset.filter(needs_collection=True)
        return queryset
    
    def filter_is_full(self, queryset, name, value):
        """Filter bins that are full (>85% capacity)"""
        if value:
            return queryset.filter(current_fill_level__gte=85)
        return queryset
    
    def filter_is_overflowing(self, queryset, name, value):
        """Filter bins that are overflowing (>95% capacity)"""
        if value:
            return queryset.filter(current_fill_level__gte=95)
        return queryset
    
    def filter_near_point(self, queryset, name, value):
        """Filter bins near a specific point (longitude,latitude format)"""
        try:
            longitude, latitude = map(float, value.split(','))
            point = Point(longitude, latitude)
            # Store point for use with radius filter
            self.request.point = point
            return queryset
        except (ValueError, AttributeError):
            return queryset
    
    def filter_within_radius(self, queryset, name, value):
        """Filter bins within a radius (in km) of the point set by near_point"""
        if hasattr(self.request, 'point') and value:
            try:
                radius_km = float(value)
                return queryset.filter(
                    location__distance_lte=(self.request.point, Distance(km=radius_km))
                )
            except ValueError:
                pass
        return queryset


class BinMaintenanceLogFilter(django_filters.FilterSet):
    """Filter set for BinMaintenanceLog model"""
    
    bin = django_filters.UUIDFilter(field_name='bin__id')
    bin_id = django_filters.CharFilter(field_name='bin__bin_id', lookup_expr='icontains')
    maintenance_type = django_filters.ChoiceFilter(choices=BinMaintenanceLog.MAINTENANCE_TYPES)
    technician = django_filters.UUIDFilter(field_name='technician__id')
    
    # Date filters
    scheduled_date_after = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='gte')
    scheduled_date_before = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='lte')
    completed_after = django_filters.DateTimeFilter(field_name='completed_at', lookup_expr='gte')
    completed_before = django_filters.DateTimeFilter(field_name='completed_at', lookup_expr='lte')
    
    # Cost filters
    cost_min = django_filters.NumberFilter(field_name='cost', lookup_expr='gte')
    cost_max = django_filters.NumberFilter(field_name='cost', lookup_expr='lte')
    
    class Meta:
        model = BinMaintenanceLog
        fields = ['is_completed']


class BinCollectionHistoryFilter(django_filters.FilterSet):
    """Filter set for BinCollectionHistory model"""
    
    bin = django_filters.UUIDFilter(field_name='bin__id')
    bin_id = django_filters.CharFilter(field_name='bin__bin_id', lookup_expr='icontains')
    collected_by = django_filters.UUIDFilter(field_name='collected_by__id')
    vehicle = django_filters.UUIDFilter(field_name='vehicle__id')
    route = django_filters.UUIDFilter(field_name='route__id')
    
    # Date filters
    collected_after = django_filters.DateTimeFilter(field_name='collected_at', lookup_expr='gte')
    collected_before = django_filters.DateTimeFilter(field_name='collected_at', lookup_expr='lte')
    
    # Fill level filters
    fill_level_min = django_filters.NumberFilter(field_name='fill_level_before', lookup_expr='gte')
    fill_level_max = django_filters.NumberFilter(field_name='fill_level_before', lookup_expr='lte')
    
    # Weight filters
    weight_min = django_filters.NumberFilter(field_name='estimated_weight_kg', lookup_expr='gte')
    weight_max = django_filters.NumberFilter(field_name='estimated_weight_kg', lookup_expr='lte')
    
    # Duration filters
    duration_min = django_filters.NumberFilter(field_name='collection_duration_minutes', lookup_expr='gte')
    duration_max = django_filters.NumberFilter(field_name='collection_duration_minutes', lookup_expr='lte')
    
    bin_condition = django_filters.ChoiceFilter(choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
    ])
    
    class Meta:
        model = BinCollectionHistory
        fields = []