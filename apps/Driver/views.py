from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Driver, DriverLocation, DriverAvailability, DriverDocument, DriverInfringement
from .serializer import (
    DriverSerializer, 
    DriverDetailSerializer,
    DriverLocationSerializer, 
    DriverAvailabilitySerializer,
    DriverDocumentSerializer,
    DriverInfringementSerializer,
)

class DriverViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Driver instances.
    """
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Driver.objects.all()
        provider_id = self.request.query_params.get('provider', None)
        status_param = self.request.query_params.get('status', None)
        employment_type = self.request.query_params.get('employment_type', None)
        has_cpc = self.request.query_params.get('has_cpc', None)
        
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        if status_param:
            queryset = queryset.filter(status=status_param)
        if employment_type:
            queryset = queryset.filter(employment_type=employment_type)
        if has_cpc is not None:
            has_cpc_bool = has_cpc.lower() == 'true'
            queryset = queryset.filter(has_cpc=has_cpc_bool)
            
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DriverDetailSerializer
        return DriverSerializer
    
    @action(detail=True, methods=['get'])
    def vehicles(self, request, pk=None):
        """
        Get all vehicles assigned to this driver.
        """
        driver = self.get_object()
        vehicles = driver.primary_vehicles.all()
        
        from Vehicle.serializer import VehicleSerializer
        serializer = VehicleSerializer(vehicles, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """
        Get all documents for a driver.
        """
        driver = self.get_object()
        documents = driver.documents.all()
        serializer = DriverDocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def infringements(self, request, pk=None):
        """
        Get all infringements for a driver.
        """
        driver = self.get_object()
        infringements = driver.infringements.all()
        serializer = DriverInfringementSerializer(infringements, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update the status of a driver.
        """
        driver = self.get_object()
        new_status = request.data.get('status', None)
        
        if not new_status:
            return Response(
                {"detail": "Status is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if new_status not in dict(Driver.STATUS_CHOICES):
            return Response(
                {"detail": f"Invalid status. Must be one of: {', '.join(dict(Driver.STATUS_CHOICES).keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        driver.status = new_status
        driver.save()
        serializer = self.get_serializer(driver)
        return Response(serializer.data)

class DriverLocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing DriverLocation instances.
    """
    queryset = DriverLocation.objects.all()
    serializer_class = DriverLocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = DriverLocation.objects.all()
        driver_id = self.request.query_params.get('driver', None)
        since = self.request.query_params.get('since', None)
        
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
        if since:
            try:
                since_date = timezone.datetime.fromisoformat(since)
                queryset = queryset.filter(timestamp__gte=since_date)
            except (ValueError, TypeError):
                pass
            
        return queryset

class DriverAvailabilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing DriverAvailability instances.
    """
    queryset = DriverAvailability.objects.all()
    serializer_class = DriverAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = DriverAvailability.objects.all()
        driver_id = self.request.query_params.get('driver', None)
        date = self.request.query_params.get('date', None)
        
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
        if date:
            try:
                date_obj = timezone.datetime.strptime(date, '%Y-%m-%d').date()
                queryset = queryset.filter(date=date_obj)
            except ValueError:
                pass
            
        return queryset

class DriverDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing DriverDocument instances.
    """
    queryset = DriverDocument.objects.all()
    serializer_class = DriverDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = DriverDocument.objects.all()
        driver_id = self.request.query_params.get('driver', None)
        document_type = self.request.query_params.get('type', None)
        
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
        if document_type:
            queryset = queryset.filter(document_type=document_type)
            
        return queryset

class DriverInfringementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing DriverInfringement instances.
    """
    queryset = DriverInfringement.objects.all()
    serializer_class = DriverInfringementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = DriverInfringement.objects.all()
        driver_id = self.request.query_params.get('driver', None)
        infringement_type = self.request.query_params.get('type', None)
        is_resolved = self.request.query_params.get('resolved', None)
        
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
        if infringement_type:
            queryset = queryset.filter(infringement_type=infringement_type)
        if is_resolved is not None:
            is_resolved_bool = is_resolved.lower() == 'true'
            queryset = queryset.filter(is_resolved=is_resolved_bool)
            
        return queryset

# class ServiceAreaViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet for viewing and editing ServiceArea instances.
#     """
#     queryset = ServiceArea.objects.all()
#     serializer_class = ServiceAreaSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_queryset(self):
#         queryset = ServiceArea.objects.all()
#         is_active = self.request.query_params.get('is_active', None)
#         name = self.request.query_params.get('name', None)
        
#         if is_active is not None:
#             is_active_bool = is_active.lower() == 'true'
#             queryset = queryset.filter(is_active=is_active_bool)
#         if name:
#             queryset = queryset.filter(name__icontains=name)
            
#         return queryset
