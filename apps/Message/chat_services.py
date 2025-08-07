"""
Chat notification services for integrating with the existing notification system
"""
from typing import List, Optional, Dict, Any
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from .models import ChatRoom, ChatMessage

User = get_user_model()
channel_layer = get_channel_layer()


class ChatNotificationService:
    """Service for handling chat-related notifications"""
    
    @staticmethod
    def send_chat_notification(
        chat_room: ChatRoom,
        message: ChatMessage,
        exclude_user: Optional[User] = None
    ) -> None:
        """
        Send chat notification to all participants except the sender
        """
        participants = chat_room.participants.all()
        if exclude_user:
            participants = participants.exclude(id=exclude_user.id)
        
        for participant in participants:
            # Create database notification
            notification_data = {
                'title': f'New message in {chat_room.name or chat_room.get_room_type_display()}',
                'message': message.content[:100] + ('...' if len(message.content) > 100 else ''),
                'sender': message.sender,
                'notification_type': 'chat_message',
                'data': {
                    'chat_room_id': str(chat_room.id),
                    'message_id': str(message.id),
                    'sender_username': message.sender.username,
                    'room_type': chat_room.room_type,
                }
            }
            
            # Create notification in database
            ChatNotificationService._create_notification(participant, notification_data)
            
            # Send real-time notification via WebSocket
            ChatNotificationService._send_realtime_notification(participant, {
                'type': 'chat_notification',
                'chat_room_id': str(chat_room.id),
                'message': notification_data['message'],
                'sender': message.sender.username,
                'room_name': chat_room.name or chat_room.get_room_type_display(),
                'room_type': chat_room.room_type,
            })
    
    @staticmethod
    def send_system_message_notification(
        chat_room: ChatRoom,
        system_message: str,
        notification_type: str = 'system',
        exclude_user: Optional[User] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send system message notification to chat room participants
        """
        participants = chat_room.participants.all()
        if exclude_user:
            participants = participants.exclude(id=exclude_user.id)
        
        # Create system message in chat
        system_chat_message = ChatMessage.objects.create(
            chat_room=chat_room,
            sender=chat_room.participants.first(),  # Use first participant as sender for system messages
            content=system_message,
            message_type='system',
            system_data=extra_data or {}
        )
        
        for participant in participants:
            notification_data = {
                'title': f'System notification - {chat_room.name or chat_room.get_room_type_display()}',
                'message': system_message,
                'notification_type': notification_type,
                'data': {
                    'chat_room_id': str(chat_room.id),
                    'message_id': str(system_chat_message.id),
                    'room_type': chat_room.room_type,
                    **(extra_data or {})
                }
            }
            
            # Create notification in database
            ChatNotificationService._create_notification(participant, notification_data)
            
            # Send real-time notification
            ChatNotificationService._send_realtime_notification(participant, {
                'type': 'system_notification',
                'message': system_message,
                'chat_room_id': str(chat_room.id),
                'data': extra_data or {}
            })
    
    @staticmethod
    def notify_bid_update(bid, action: str, user: User) -> None:
        """
        Send notifications when bid status changes
        """
        # Find or create chat room for the bid
        content_type = ContentType.objects.get_for_model(bid)
        chat_room, created = ChatRoom.objects.get_or_create(
            content_type=content_type,
            object_id=bid.id,
            defaults={
                'room_type': 'bidding',
                'name': f'Bid Discussion - {bid.job.title if hasattr(bid.job, "title") else bid.job.job_number}',
            }
        )
        
        # Add relevant participants if room was just created
        if created:
            if bid.provider and hasattr(bid.provider, 'user'):
                chat_room.add_participant(bid.provider.user)
            if bid.job and bid.job.request and bid.job.request.user:
                chat_room.add_participant(bid.job.request.user)
        
        # Send system message
        action_messages = {
            'submitted': f'A new bid of ${bid.amount} has been submitted.',
            'accepted': f'Bid of ${bid.amount} has been accepted!',
            'rejected': f'Bid of ${bid.amount} has been rejected.',
            'counter_offered': f'A counter offer of ${bid.counter_offer} has been made.',
        }
        
        message = action_messages.get(action, f'Bid status updated: {action}')
        
        ChatNotificationService.send_system_message_notification(
            chat_room=chat_room,
            system_message=message,
            notification_type='bid_update',
            exclude_user=user,
            extra_data={
                'bid_id': str(bid.id),
                'bid_amount': str(bid.amount),
                'bid_status': bid.status,
                'action': action,
            }
        )
    
    @staticmethod
    def notify_job_status_change(job, old_status: str, new_status: str, user: User) -> None:
        """
        Send notifications when job status changes
        """
        # Find or create chat room for the job
        content_type = ContentType.objects.get_for_model(job)
        chat_room, created = ChatRoom.objects.get_or_create(
            content_type=content_type,
            object_id=job.id,
            defaults={
                'room_type': 'job',
                'name': f'Job Discussion - {job.title or job.job_number}',
            }
        )
        
        # Add relevant participants if room was just created
        if created:
            if job.request and job.request.user:
                chat_room.add_participant(job.request.user)
            if job.assigned_provider and hasattr(job.assigned_provider, 'user'):
                chat_room.add_participant(job.assigned_provider.user)
        
        # Send system message
        message = f'Job status changed from {old_status.replace("_", " ").title()} to {new_status.replace("_", " ").title()}'
        
        ChatNotificationService.send_system_message_notification(
            chat_room=chat_room,
            system_message=message,
            notification_type='status_update',
            exclude_user=user,
            extra_data={
                'job_id': str(job.id),
                'old_status': old_status,
                'new_status': new_status,
                'job_number': job.job_number,
            }
        )
    
    @staticmethod
    def notify_request_status_change(request, old_status: str, new_status: str, user: User) -> None:
        """
        Send notifications when request status changes
        """
        # Find or create chat room for the request
        content_type = ContentType.objects.get_for_model(request)
        chat_room, created = ChatRoom.objects.get_or_create(
            content_type=content_type,
            object_id=request.id,
            defaults={
                'room_type': 'request',
                'name': f'Request Discussion - {getattr(request, "title", f"Request {request.id}")}',
            }
        )
        
        # Add relevant participants if room was just created
        if created:
            if request.user:
                chat_room.add_participant(request.user)
            if request.provider and hasattr(request.provider, 'user'):
                chat_room.add_participant(request.provider.user)
            if request.driver and hasattr(request.driver, 'user'):
                chat_room.add_participant(request.driver.user)
        
        # Send system message
        message = f'Request status changed from {old_status.replace("_", " ").title()} to {new_status.replace("_", " ").title()}'
        
        ChatNotificationService.send_system_message_notification(
            chat_room=chat_room,
            system_message=message,
            notification_type='status_update',
            exclude_user=user,
            extra_data={
                'request_id': str(request.id),
                'old_status': old_status,
                'new_status': new_status,
            }
        )
    
    @staticmethod
    def create_support_chat_room(user: User, subject: str = "Support Request") -> ChatRoom:
        """
        Create a support chat room for customer support
        """
        chat_room = ChatRoom.objects.create(
            name=f'Support - {subject}',
            room_type='support',
            is_private=True,
        )
        
        # Add user to the chat room
        chat_room.add_participant(user)
        
        # Add support staff (users with is_staff=True)
        support_staff = User.objects.filter(is_staff=True, is_active=True)[:3]  # Limit to 3 support staff
        for staff in support_staff:
            chat_room.add_participant(staff)
        
        # Send initial system message
        ChatMessage.objects.create(
            chat_room=chat_room,
            sender=user,
            content=f'Support request created: {subject}',
            message_type='system',
            system_data={'action': 'support_created', 'subject': subject}
        )
        
        return chat_room
    
    @staticmethod
    def _create_notification(user: User, notification_data: Dict[str, Any]) -> None:
        """
        Create a notification in the database using the existing notification system
        """
        try:
            from apps.Notification.models import Notification
            Notification.objects.create(
                user=user,
                title=notification_data['title'],
                message=notification_data['message'],
                notification_type=notification_data.get('notification_type', 'info'),
                data=notification_data.get('data', {}),
                sender=notification_data.get('sender'),
            )
        except Exception as e:
            print(f"Error creating notification: {e}")
    
    @staticmethod
    def _send_realtime_notification(user: User, notification_data: Dict[str, Any]) -> None:
        """
        Send real-time notification via WebSocket
        """
        if not channel_layer:
            return
        
        user_group_name = f'user_{user.id}'
        
        try:
            async_to_sync(channel_layer.group_send)(
                user_group_name,
                notification_data
            )
        except Exception as e:
            print(f"Error sending real-time notification: {e}")


class ChatAutomationService:
    """Service for automated chat actions and responses"""
    
    @staticmethod
    def auto_create_chat_rooms():
        """
        Automatically create chat rooms for existing objects that don't have them
        """
        from apps.Request.models import Request
        from apps.Job.models import Job
        
        # Auto-create for active requests
        active_requests = Request.objects.filter(
            status__in=['pending', 'accepted', 'in_transit']
        ).exclude(
            id__in=ChatRoom.objects.filter(
                content_type=ContentType.objects.get_for_model(Request)
            ).values_list('object_id', flat=True)
        )
        
        for request in active_requests:
            content_type = ContentType.objects.get_for_model(request)
            chat_room = ChatRoom.objects.create(
                content_type=content_type,
                object_id=request.id,
                room_type='request',
                name=f'Request Discussion - {getattr(request, "title", f"Request {request.id}")}',
            )
            
            # Add participants
            if request.user:
                chat_room.add_participant(request.user)
            if request.provider and hasattr(request.provider, 'user'):
                chat_room.add_participant(request.provider.user)
        
        # Auto-create for active jobs
        active_jobs = Job.objects.filter(
            status__in=['pending', 'accepted', 'in_transit']
        ).exclude(
            id__in=ChatRoom.objects.filter(
                content_type=ContentType.objects.get_for_model(Job)
            ).values_list('object_id', flat=True)
        )
        
        for job in active_jobs:
            content_type = ContentType.objects.get_for_model(job)
            chat_room = ChatRoom.objects.create(
                content_type=content_type,
                object_id=job.id,
                room_type='job',
                name=f'Job Discussion - {job.title or job.job_number}',
            )
            
            # Add participants
            if job.request and job.request.user:
                chat_room.add_participant(job.request.user)
            if job.assigned_provider and hasattr(job.assigned_provider, 'user'):
                chat_room.add_participant(job.assigned_provider.user)
    
    @staticmethod
    def cleanup_old_chat_rooms(days: int = 30):
        """
        Clean up old inactive chat rooms
        """
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Mark old rooms as inactive
        old_rooms = ChatRoom.objects.filter(
            last_message_at__lt=cutoff_date,
            is_active=True
        )
        
        old_rooms.update(is_active=False)
        
        return old_rooms.count()
    
    @staticmethod
    def generate_chat_analytics():
        """
        Generate basic chat analytics
        """
        from django.db.models import Count, Avg
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)
        
        analytics = {
            'total_rooms': ChatRoom.objects.count(),
            'active_rooms': ChatRoom.objects.filter(is_active=True).count(),
            'total_messages': ChatMessage.objects.count(),
            'messages_last_week': ChatMessage.objects.filter(created_at__gte=last_week).count(),
            'messages_last_month': ChatMessage.objects.filter(created_at__gte=last_month).count(),
            'rooms_by_type': dict(
                ChatRoom.objects.values('room_type').annotate(
                    count=Count('id')
                ).values_list('room_type', 'count')
            ),
            'avg_messages_per_room': ChatRoom.objects.annotate(
                message_count=Count('chat_messages')
            ).aggregate(avg=Avg('message_count'))['avg'] or 0,
        }
        
        return analytics