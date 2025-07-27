"""
API Views for WasteWise Bins

These views provide REST API endpoints for managing waste bins, zones,
and related operations.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.db.models import Count, Avg, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Zone, WasteBin, BinMaintenanceLog, BinCollectionHistory
from .serializers import (
    ZoneSerializer, ZoneListSerializer, WasteBinSerializer, WasteBinListSerializer,
    WasteBinCreateSerializer, BinMaintenanceLogSerializer, BinCollectionHistorySerializer,
    BinStatisticsSerializer, NearbyBinsSerializer, BinAlertSerializer,
    BinCollectionRequestSerializer, BinStatusUpdateSerializer
)
from .filters import WasteBinFilter, ZoneFilter


class ZoneViewSet(ModelViewSet):
    """
    ViewSet for managing geographic zones
    
    Provides CRUD operations for waste collection zones including
    zone statistics and bin management.
    """
    queryset = Zone.objects.select_related('supervisor').prefetch_related('bins')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ZoneFilter
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ZoneListSerializer
        return ZoneSerializer
    
    def get_queryset(self):
        """Filter zones based on user permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role == 'supervisor':
            # Zone supervisors can only see their assigned zones
            queryset = queryset.filter(supervisor=user)
        elif user.role == 'citizen':
            # Citizens can only see basic zone info
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    @extend_schema(
        summary="Get zone statistics",
        description="Retrieve detailed statistics for a specific zone",
        responses={200: BinStatisticsSerializer}
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get detailed statistics for a zone"""
        zone = self.get_object()
        bins = zone.bins.filter(is_active=True)
        
        # Calculate statistics
        total_bins = bins.count()
        full_bins = bins.filter(current_fill_level__gte=85).count()
        overflowing_bins = bins.filter(current_fill_level__gte=95).count()
        offline_bins = bins.filter(status='offline').count()
        
        # Get bins by type
        bins_by_type = dict(bins.values('bin_type').annotate(count=Count('id')).values_list('bin_type', 'count'))
        
        stats = {
            'total_bins': total_bins,
            'active_bins': bins.filter(status='active').count(),
            'full_bins': full_bins,
            'overflowing_bins': overflowing_bins,
            'offline_bins': offline_bins,
            'average_fill_level': bins.aggregate(avg=Avg('current_fill_level'))['avg'] or 0,
            'bins_needing_collection': bins.filter(needs_collection=True).count(),
            'bins_by_type': bins_by_type,
            'bins_by_zone': {zone.name: total_bins}
        }
        
        serializer = BinStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get bins in zone",
        description="List all waste bins within this zone",
        responses={200: WasteBinListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def bins(self, request, pk=None):
        """Get all bins in this zone"""
        zone = self.get_object()
        bins = zone.bins.filter(is_active=True)
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            bins = bins.filter(status=status_filter)
        
        bin_type_filter = request.query_params.get('bin_type')
        if bin_type_filter:
            bins = bins.filter(bin_type=bin_type_filter)
        
        needs_collection = request.query_params.get('needs_collection')
        if needs_collection and needs_collection.lower() == 'true':
            bins = bins.filter(needs_collection=True)
        
        serializer = WasteBinListSerializer(bins, many=True)
        return Response(serializer.data)


class WasteBinViewSet(ModelViewSet):
    """
    ViewSet for managing waste bins
    
    Provides comprehensive CRUD operations for waste bins including
    location-based searches, status updates, and collection management.
    """
    queryset = WasteBin.objects.select_related('zone').prefetch_related('sensor_readings')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = WasteBinFilter
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WasteBinCreateSerializer
        elif self.action == 'list':
            return WasteBinListSerializer
        elif self.action == 'update_status':
            return BinStatusUpdateSerializer
        return WasteBinSerializer
    
    def get_queryset(self):
        """Filter bins based on user permissions and location"""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role == 'supervisor':
            # Zone supervisors see bins in their zones
            queryset = queryset.filter(zone__supervisor=user)
        elif user.role == 'citizen':
            # Citizens see only active bins
            queryset = queryset.filter(is_active=True, status='active')
        
        return queryset
    
    @extend_schema(
        summary="Find nearby bins",
        description="Find waste bins near a specific location",
        parameters=[
            OpenApiParameter('latitude', float, description='Latitude coordinate'),
            OpenApiParameter('longitude', float, description='Longitude coordinate'),
            OpenApiParameter('radius_km', float, description='Search radius in kilometers'),
            OpenApiParameter('bin_type', str, description='Filter by bin type'),
        ],
        responses={200: WasteBinListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Find bins near a specific location"""
        serializer = NearbyBinsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        latitude = serializer.validated_data['latitude']
        longitude = serializer.validated_data['longitude']
        radius_km = serializer.validated_data.get('radius_km', 1.0)
        bin_type = serializer.validated_data.get('bin_type')
        only_available = serializer.validated_data.get('only_available', True)
        
        # Create point and find nearby bins
        user_location = Point(longitude, latitude)
        queryset = self.get_queryset().filter(
            location__distance_lte=(user_location, Distance(km=radius_km))
        )
        
        if bin_type:
            queryset = queryset.filter(bin_type=bin_type)
        
        if only_available:
            queryset = queryset.filter(status='active', current_fill_level__lt=85)
        
        # Order by distance
        queryset = queryset.extra(
            select={
                'distance': 'ST_Distance(location, ST_GeomFromText(%s, 4326))'
            },
            select_params=[user_location.wkt]
        ).order_by('distance')
        
        serializer = WasteBinListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Update bin status",
        description="Update the status of a waste bin",
        request=BinStatusUpdateSerializer,
        responses={200: WasteBinSerializer}
    )
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update bin status with validation"""
        bin_obj = self.get_object()
        serializer = BinStatusUpdateSerializer(bin_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Update bin status
        bin_obj.status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        if notes:
            bin_obj.notes = f"{bin_obj.notes}\n{timezone.now()}: {notes}" if bin_obj.notes else notes
        
        bin_obj.save()
        
        # Log the activity
        from apps.wastewise.users.models import UserActivity
        UserActivity.objects.create(
            user=request.user,
            activity_type='bin_update',
            description=f"Updated bin {bin_obj.bin_id} status to {bin_obj.status}",
            object_type='WasteBin',
            object_id=str(bin_obj.id)
        )
        
        response_serializer = WasteBinSerializer(bin_obj)
        return Response(response_serializer.data)
    
    @extend_schema(
        summary="Request bin collection",
        description="Submit a request for bin collection",
        request=BinCollectionRequestSerializer,
        responses={201: {'description': 'Collection request created'}}
    )
    @action(detail=False, methods=['post'])
    def request_collection(self, request):
        """Submit a collection request for multiple bins"""
        serializer = BinCollectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        bin_ids = serializer.validated_data['bin_ids']
        priority = serializer.validated_data.get('priority', 'normal')
        requested_date = serializer.validated_data.get('requested_date')
        notes = serializer.validated_data.get('notes', '')
        
        # Validate bins exist and are accessible
        bins = self.get_queryset().filter(bin_id__in=bin_ids)
        if bins.count() != len(bin_ids):
            return Response(
                {'error': 'Some bins were not found or are not accessible'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create collection alerts/requests
        from apps.wastewise.alerts.models import CollectionRequest
        collection_request = CollectionRequest.objects.create(
            requested_by=request.user,
            priority=priority,
            requested_date=requested_date or timezone.now().date(),
            notes=notes
        )
        collection_request.bins.set(bins)
        
        return Response(
            {'message': f'Collection request created for {bins.count()} bins'},
            status=status.HTTP_201_CREATED
        )
    
    @extend_schema(
        summary="Report bin issue",
        description="Report an issue with a waste bin",
        request=BinAlertSerializer,
        responses={201: {'description': 'Alert created'}}
    )
    @action(detail=False, methods=['post'])
    def report_issue(self, request):
        """Report an issue with a bin"""
        serializer = BinAlertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        bin_id = serializer.validated_data['bin_id']
        alert_type = serializer.validated_data['alert_type']
        description = serializer.validated_data['description']
        priority = serializer.validated_data.get('priority', 'medium')
        
        # Find the bin
        try:
            bin_obj = self.get_queryset().get(bin_id=bin_id)
        except WasteBin.DoesNotExist:
            return Response(
                {'error': 'Bin not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create alert
        from apps.wastewise.alerts.models import BinAlert
        alert = BinAlert.objects.create(
            bin=bin_obj,
            alert_type=alert_type,
            description=description,
            priority=priority,
            reported_by=request.user,
            photos=serializer.validated_data.get('photos', [])
        )
        
        return Response(
            {'message': 'Issue reported successfully', 'alert_id': str(alert.id)},
            status=status.HTTP_201_CREATED
        )
    
    @extend_schema(
        summary="Get bin maintenance logs",
        description="Retrieve maintenance history for a bin",
        responses={200: BinMaintenanceLogSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def maintenance_logs(self, request, pk=None):
        """Get maintenance logs for a bin"""
        bin_obj = self.get_object()
        logs = bin_obj.maintenance_logs.all()
        serializer = BinMaintenanceLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get bin collection history",
        description="Retrieve collection history for a bin",
        responses={200: BinCollectionHistorySerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def collection_history(self, request, pk=None):
        """Get collection history for a bin"""
        bin_obj = self.get_object()
        history = bin_obj.collection_history.all()[:20]  # Last 20 collections
        serializer = BinCollectionHistorySerializer(history, many=True)
        return Response(serializer.data)


class BinMaintenanceLogViewSet(ModelViewSet):
    """ViewSet for managing bin maintenance logs"""
    
    queryset = BinMaintenanceLog.objects.select_related('bin', 'technician')
    serializer_class = BinMaintenanceLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bin', 'maintenance_type', 'is_completed', 'technician']
    
    def get_queryset(self):
        """Filter logs based on user permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role == 'supervisor':
            queryset = queryset.filter(bin__zone__supervisor=user)
        elif user.role == 'technician':
            queryset = queryset.filter(technician=user)
        elif user.role == 'citizen':
            # Citizens cannot access maintenance logs
            queryset = queryset.none()
        
        return queryset


class BinCollectionHistoryViewSet(ModelViewSet):
    """ViewSet for managing bin collection history"""
    
    queryset = BinCollectionHistory.objects.select_related('bin', 'collected_by', 'vehicle', 'route')
    serializer_class = BinCollectionHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bin', 'collected_by', 'vehicle', 'route']
    
    def get_queryset(self):
        """Filter history based on user permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role == 'supervisor':
            queryset = queryset.filter(bin__zone__supervisor=user)
        elif user.role == 'operator':
            queryset = queryset.filter(collected_by=user)
        elif user.role == 'citizen':
            # Citizens have limited access to collection history
            queryset = queryset.filter(bin__zone__is_active=True).only(
                'bin', 'collected_at', 'bin_condition'
            )
        
        return queryset


# Statistics and Analytics Views
@extend_schema(
    summary="Get system-wide bin statistics",
    description="Retrieve overall statistics for the waste management system",
    responses={200: BinStatisticsSerializer}
)
class BinStatisticsView(generics.GenericAPIView):
    """Get overall bin statistics for the system"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BinStatisticsSerializer
    
    def get(self, request):
        """Calculate and return system statistics"""
        user = request.user
        
        # Get bins based on user permissions
        if user.role == 'supervisor':
            bins = WasteBin.objects.filter(zone__supervisor=user, is_active=True)
        else:
            bins = WasteBin.objects.filter(is_active=True)
        
        # Calculate statistics
        total_bins = bins.count()
        active_bins = bins.filter(status='active').count()
        full_bins = bins.filter(current_fill_level__gte=85).count()
        overflowing_bins = bins.filter(current_fill_level__gte=95).count()
        offline_bins = bins.filter(status='offline').count()
        
        # Average fill level
        avg_fill = bins.aggregate(avg=Avg('current_fill_level'))['avg'] or 0
        
        # Bins needing collection
        bins_needing_collection = bins.filter(needs_collection=True).count()
        
        # Bins by type
        bins_by_type = dict(
            bins.values('bin_type').annotate(count=Count('id')).values_list('bin_type', 'count')
        )
        
        # Bins by zone
        bins_by_zone = dict(
            bins.values('zone__name').annotate(count=Count('id')).values_list('zone__name', 'count')
        )
        
        stats = {
            'total_bins': total_bins,
            'active_bins': active_bins,
            'full_bins': full_bins,
            'overflowing_bins': overflowing_bins,
            'offline_bins': offline_bins,
            'average_fill_level': round(avg_fill, 2),
            'bins_needing_collection': bins_needing_collection,
            'bins_by_type': bins_by_type,
            'bins_by_zone': bins_by_zone,
        }
        
        serializer = self.get_serializer(stats)
        return Response(serializer.data)