from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import TrackingUpdate
from .serializer import TrackingUpdateSerializer

class TrackingUpdateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing TrackingUpdate instances.
    """
    queryset = TrackingUpdate.objects.all()
    serializer_class = TrackingUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = TrackingUpdate.objects.all()
        request_id = self.request.query_params.get('request', None)
        update_type = self.request.query_params.get('type', None)
        
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        if update_type:
            queryset = queryset.filter(update_type=update_type)
            
        return queryset
