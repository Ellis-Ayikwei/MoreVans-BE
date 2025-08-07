from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Dispute
from .serializer import DisputeSerializer
from apps.Chat.utils import create_dispute_conversation, get_or_create_conversation_for_object, add_system_message

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
    
    def perform_create(self, serializer):
        """Create dispute and associated chat conversation"""
        dispute = serializer.save(raised_by=self.request.user)
        
        # Create chat conversation for dispute
        try:
            conversation = create_dispute_conversation(dispute)
            # Add initial system message
            add_system_message(
                conversation,
                f"Dispute created - Type: {dispute.get_dispute_type_display()}",
                metadata={'dispute_id': str(dispute.id), 'action': 'dispute_created'}
            )
        except Exception as e:
            print(f"Error creating dispute conversation: {e}")
    
    @action(detail=True, methods=['get'])
    def conversation(self, request, pk=None):
        """Get the chat conversation for a dispute"""
        dispute = self.get_object()
        user = request.user
        
        # Check if user has access
        is_admin = user.is_staff or user.is_superuser
        is_dispute_raiser = dispute.raised_by == user
        is_involved_party = (
            dispute.request and 
            (dispute.request.user == user or 
             (hasattr(dispute.request, 'job') and 
              dispute.request.job and 
              dispute.request.job.assigned_provider and
              hasattr(dispute.request.job.assigned_provider, 'user') and
              dispute.request.job.assigned_provider.user == user))
        )
        
        if not (is_admin or is_dispute_raiser or is_involved_party):
            return Response(
                {"error": "You don't have permission to view this conversation"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        # Get or create conversation
        conversation, created = get_or_create_conversation_for_object(dispute, 'dispute')
        
        if created:
            # Add initial message
            add_system_message(
                conversation,
                f"Dispute conversation started - Type: {dispute.get_dispute_type_display()}",
                metadata={'dispute_id': str(dispute.id), 'action': 'dispute_conversation_created'}
            )
        
        return Response({
            "conversation_id": str(conversation.id),
            "conversation_type": conversation.conversation_type,
            "title": conversation.title,
            "created": created
        })
    
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
        
        # Add system message to dispute conversation
        try:
            conversation, _ = get_or_create_conversation_for_object(dispute, 'dispute')
            compensation_msg = f" Compensation: ${compensation_amount}" if compensation_amount else ""
            add_system_message(
                conversation,
                f"Dispute has been resolved.{compensation_msg}",
                metadata={
                    'dispute_id': str(dispute.id), 
                    'action': 'dispute_resolved',
                    'compensation_amount': str(compensation_amount) if compensation_amount else None
                }
            )
        except Exception as e:
            print(f"Error updating dispute conversation: {e}")
        
        serializer = self.get_serializer(dispute)
        return Response(serializer.data)
