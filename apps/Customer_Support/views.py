from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Dispute
from .serializer import DisputeSerializer

class DisputeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Dispute instances.
    """
    queryset = Dispute.objects.all()
    serializer_class = DisputeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Dispute.objects.all()
        request_id = self.request.query_params.get('request', None)
        user_id = self.request.query_params.get('user', None)
        status_param = self.request.query_params.get('status', None)
        dispute_type = self.request.query_params.get('type', None)
        
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        if user_id:
            queryset = queryset.filter(raised_by_id=user_id)
        if status_param:
            queryset = queryset.filter(status=status_param)
        if dispute_type:
            queryset = queryset.filter(dispute_type=dispute_type)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Mark a dispute as resolved.
        """
        dispute = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        compensation_amount = request.data.get('compensation_amount', None)
        
        dispute.status = 'resolved'
        dispute.resolved_at = timezone.now()
        dispute.resolution_notes = resolution_notes
        
        if compensation_amount is not None:
            dispute.compensation_amount = compensation_amount
            
        dispute.save()
        serializer = self.get_serializer(dispute)
        return Response(serializer.data)
