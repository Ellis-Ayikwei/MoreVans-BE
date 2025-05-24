from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Message
from .serializer import MessageSerializer

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Message instances.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Message.objects.all()
        request_id = self.request.query_params.get('request', None)
        sender_id = self.request.query_params.get('sender', None)
        receiver_id = self.request.query_params.get('receiver', None)
        read = self.request.query_params.get('read', None)
        
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        if sender_id:
            queryset = queryset.filter(sender_id=sender_id)
        if receiver_id:
            queryset = queryset.filter(receiver_id=receiver_id)
        if read is not None:
            read_bool = read.lower() == 'true'
            queryset = queryset.filter(read=read_bool)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark a message as read.
        """
        message = self.get_object()
        if message.receiver != request.user:
            return Response(
                {"detail": "You can only mark messages sent to you as read."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        message.read = True
        message.read_at = timezone.now()
        message.save()
        serializer = self.get_serializer(message)
        return Response(serializer.data)
