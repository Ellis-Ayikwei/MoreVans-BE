"""
URL patterns for WasteWise Bins API

Defines the REST API endpoints for waste bin management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ZoneViewSet, WasteBinViewSet, BinMaintenanceLogViewSet,
    BinCollectionHistoryViewSet, BinStatisticsView
)

app_name = 'bins'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'zones', ZoneViewSet, basename='zone')
router.register(r'bins', WasteBinViewSet, basename='wastebin')
router.register(r'maintenance-logs', BinMaintenanceLogViewSet, basename='maintenance-log')
router.register(r'collection-history', BinCollectionHistoryViewSet, basename='collection-history')

urlpatterns = [
    # API endpoints from router
    path('', include(router.urls)),
    
    # Additional endpoints
    path('statistics/', BinStatisticsView.as_view(), name='statistics'),
]

# The router automatically creates these endpoints:
# 
# Zones:
# GET    /zones/                     - List all zones
# POST   /zones/                     - Create new zone
# GET    /zones/{id}/               - Retrieve specific zone
# PUT    /zones/{id}/               - Update zone
# PATCH  /zones/{id}/               - Partial update zone
# DELETE /zones/{id}/               - Delete zone
# GET    /zones/{id}/statistics/    - Zone statistics
# GET    /zones/{id}/bins/          - Bins in zone
#
# Waste Bins:
# GET    /bins/                     - List all bins
# POST   /bins/                     - Create new bin
# GET    /bins/{id}/               - Retrieve specific bin
# PUT    /bins/{id}/               - Update bin
# PATCH  /bins/{id}/               - Partial update bin
# DELETE /bins/{id}/               - Delete bin
# GET    /bins/nearby/             - Find nearby bins
# PATCH  /bins/{id}/update_status/ - Update bin status
# POST   /bins/request_collection/ - Request collection
# POST   /bins/report_issue/       - Report issue
# GET    /bins/{id}/maintenance_logs/ - Bin maintenance logs
# GET    /bins/{id}/collection_history/ - Bin collection history
#
# Maintenance Logs:
# GET    /maintenance-logs/         - List maintenance logs
# POST   /maintenance-logs/         - Create maintenance log
# GET    /maintenance-logs/{id}/   - Retrieve maintenance log
# PUT    /maintenance-logs/{id}/   - Update maintenance log
# DELETE /maintenance-logs/{id}/   - Delete maintenance log
#
# Collection History:
# GET    /collection-history/       - List collection history
# POST   /collection-history/       - Create collection record
# GET    /collection-history/{id}/ - Retrieve collection record
# PUT    /collection-history/{id}/ - Update collection record
# DELETE /collection-history/{id}/ - Delete collection record
#
# Statistics:
# GET    /statistics/               - System-wide statistics