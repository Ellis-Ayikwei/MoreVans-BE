from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Vehicle, VehicleDocument, VehicleInspection, MaintenanceRecord
from .serializer import (
    VehicleSerializer, 
    VehicleDetailSerializer,
    VehicleDocumentSerializer, 
    VehicleInspectionSerializer, 
    MaintenanceRecordSerializer
)

class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Vehicle instances.
    """
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Vehicle.objects.all()
        provider_id = self.request.query_params.get('provider', None)
        vehicle_type = self.request.query_params.get('type', None)
        is_active = self.request.query_params.get('active', None)
        registration = self.request.query_params.get('registration', None)
        driver_id = self.request.query_params.get('driver', None)
        
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        if registration:
            queryset = queryset.filter(registration__icontains=registration)
        if driver_id:
            queryset = queryset.filter(primary_driver_id=driver_id)
            
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VehicleDetailSerializer
        return VehicleSerializer
    
    @action(detail=True, methods=['post'])
    def update_mileage(self, request, pk=None):
        """
        Update the current mileage of a vehicle.
        """
        vehicle = self.get_object()
        new_mileage = request.data.get('mileage', None)
        
        if new_mileage is None:
            return Response(
                {"detail": "Mileage value is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            new_mileage = int(new_mileage)
            if new_mileage < vehicle.current_mileage:
                return Response(
                    {"detail": "New mileage cannot be less than the current mileage."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            vehicle.current_mileage = new_mileage
            vehicle.save()
            serializer = self.get_serializer(vehicle)
            return Response(serializer.data)
            
        except ValueError:
            return Response(
                {"detail": "Mileage must be a valid integer."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """
        Get all documents for a vehicle.
        """
        vehicle = self.get_object()
        documents = vehicle.documents.all()
        serializer = VehicleDocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def inspections(self, request, pk=None):
        """
        Get all inspections for a vehicle.
        """
        vehicle = self.get_object()
        inspections = vehicle.inspections.all()
        serializer = VehicleInspectionSerializer(inspections, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def maintenance(self, request, pk=None):
        """
        Get all maintenance records for a vehicle.
        """
        vehicle = self.get_object()
        records = vehicle.maintenance_records.all()
        serializer = MaintenanceRecordSerializer(records, many=True)
        return Response(serializer.data)

class VehicleDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing VehicleDocument instances.
    """
    queryset = VehicleDocument.objects.all()
    serializer_class = VehicleDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = VehicleDocument.objects.all()
        vehicle_id = self.request.query_params.get('vehicle', None)
        document_type = self.request.query_params.get('type', None)
        
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        if document_type:
            queryset = queryset.filter(document_type=document_type)
            
        return queryset

class VehicleInspectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing VehicleInspection instances.
    """
    queryset = VehicleInspection.objects.all()
    serializer_class = VehicleInspectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = VehicleInspection.objects.all()
        vehicle_id = self.request.query_params.get('vehicle', None)
        inspection_type = self.request.query_params.get('type', None)
        is_roadworthy = self.request.query_params.get('roadworthy', None)
        
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        if inspection_type:
            queryset = queryset.filter(inspection_type=inspection_type)
        if is_roadworthy is not None:
            is_roadworthy_bool = is_roadworthy.lower() == 'true'
            queryset = queryset.filter(is_roadworthy=is_roadworthy_bool)
            
        return queryset

class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing MaintenanceRecord instances.
    """
    queryset = MaintenanceRecord.objects.all()
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = MaintenanceRecord.objects.all()
        vehicle_id = self.request.query_params.get('vehicle', None)
        maintenance_type = self.request.query_params.get('type', None)
        
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        if maintenance_type:
            queryset = queryset.filter(maintenance_type=maintenance_type)
            
        return queryset
