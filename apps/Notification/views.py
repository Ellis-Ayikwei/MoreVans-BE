from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Notification
from .serializer import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Notification instances.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Notification.objects.all()
        user_id = self.request.query_params.get('user', None)
        notification_type = self.request.query_params.get('type', None)
        read = self.request.query_params.get('read', None)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        if read is not None:
            read_bool = read.lower() == 'true'
            queryset = queryset.filter(read=read_bool)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark a notification as read.
        """
        notification = self.get_object()
        if notification.user != request.user:
            return Response(
                {"detail": "You can only mark your own notifications as read."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        notification.read = True
        notification.read_at = timezone.now()
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
        
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        Mark all notifications for the current user as read.
        """
        notifications = Notification.objects.filter(user=request.user, read=False)
        now = timezone.now()
        
        for notification in notifications:
            notification.read = True
            notification.read_at = now
            notification.save()
            
        return Response({"detail": f"Marked {notifications.count()} notifications as read."})
