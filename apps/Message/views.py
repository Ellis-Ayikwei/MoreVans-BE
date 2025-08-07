from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import Message
from .serializer import MessageSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Prefetch, Count
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Message, ChatRoom, ChatMessage, ChatMessageRead
from .serializer import (
    MessageSerializer, 
    ChatRoomSerializer, 
    ChatRoomCreateSerializer,
    ChatMessageSerializer,
    ChatMessageReadSerializer,
    BulkMarkAsReadSerializer
)
from apps.User.models import User
from apps.Request.models import Request
from apps.Job.models import Job
from apps.Bidding.models import Bid


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Message instances.
    """

    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Support file uploads

    def get_queryset(self):
        user = self.request.user

        # Base queryset - users can only see messages they sent or received
        # unless they're admin
        if user.is_staff or user.is_superuser:
            queryset = Message.objects.all()
        else:
            queryset = Message.objects.filter(Q(sender=user) | Q(receiver=user))

        # Apply query parameter filters
        request_id = self.request.query_params.get("request", None)
        sender_id = self.request.query_params.get("sender", None)
        receiver_id = self.request.query_params.get("receiver", None)
        read = self.request.query_params.get("read", None)
        unread_only = self.request.query_params.get("unread_only", None)

        if request_id:
            queryset = queryset.filter(request_id=request_id)
        if sender_id:
            queryset = queryset.filter(sender_id=sender_id)
        if receiver_id:
            queryset = queryset.filter(receiver_id=receiver_id)
        if read is not None:
            read_bool = read.lower() == "true"
            queryset = queryset.filter(read=read_bool)
        if unread_only and unread_only.lower() == "true":
            queryset = queryset.filter(read=False, receiver=user)

        return queryset.select_related("sender", "receiver", "request").order_by(
            "-created_at"
        )

    def perform_create(self, serializer):
        """Set sender as current user when creating a message"""
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        """
        Mark a message as read.
        """
        message = self.get_object()
        if message.receiver != request.user:
            return Response(
                {"detail": "You can only mark messages sent to you as read."},
                status=status.HTTP_403_FORBIDDEN,
            )

        message.read = True
        message.read_at = timezone.now()
        message.save()
        serializer = self.get_serializer(message)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def conversation(self, request):
        """
        Get all messages for a specific request (conversation)
        Usage: /messages/conversation/?request_id=uuid
        """
        request_id = request.query_params.get("request_id")
        if not request_id:
            return Response(
                {"error": "request_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        messages = (
            Message.objects.filter(request_id=request_id)
            .filter(Q(sender=user) | Q(receiver=user))
            .select_related("sender", "receiver")
            .order_by("created_at")
        )

        serializer = MessageSerializer(
            messages, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """
        Get count of unread messages for current user
        Usage: /messages/unread_count/
        """
        user = request.user
        count = Message.objects.filter(receiver=user, read=False).count()
        return Response({"unread_count": count})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """
        Mark all messages as read for current user
        Optional: pass request_id to mark only messages in that conversation
        Usage: POST /messages/mark_all_read/
        Body: {"request_id": "uuid"} (optional)
        """
        user = request.user
        request_id = request.data.get("request_id")

        if request_id:
            # Mark messages in specific conversation as read
            updated = Message.objects.filter(
                request_id=request_id, receiver=user, read=False
            ).update(read=True, read_at=timezone.now())
        else:
            # Mark all user's messages as read
            updated = Message.objects.filter(receiver=user, read=False).update(
                read=True, read_at=timezone.now()
            )

        return Response(
            {"message": f"{updated} messages marked as read", "count": updated}
        )

    @action(detail=False, methods=["get"])
    def my_conversations(self, request):
        """
        Get list of conversations (unique requests) with latest message info
        Usage: /messages/my_conversations/
        """
        user = request.user

        # Get distinct request IDs where user has messages
        conversations = []
        request_ids = (
            Message.objects.filter(Q(sender=user) | Q(receiver=user))
            .values_list("request_id", flat=True)
            .distinct()
        )

        for request_id in request_ids:
            # Get latest message for this request
            latest_message = (
                Message.objects.filter(request_id=request_id)
                .filter(Q(sender=user) | Q(receiver=user))
                .select_related("sender", "receiver", "request")
                .order_by("-created_at")
                .first()
            )

            # Count unread messages in this conversation
            unread_count = Message.objects.filter(
                request_id=request_id, receiver=user, read=False
            ).count()

            if latest_message:
                conversations.append(
                    {
                        "request_id": str(request_id),
                        "request_tracking_number": (
                            latest_message.request.tracking_number
                            if latest_message.request
                            else None
                        ),
                        "latest_message": MessageSerializer(
                            latest_message, context={"request": request}
                        ).data,
                        "unread_count": unread_count,
                        "last_activity": latest_message.created_at,
                    }
                )

        # Sort by last activity
        conversations.sort(key=lambda x: x["last_activity"], reverse=True)

        return Response(conversations)

    @action(detail=False, methods=["post"])
    def send_file(self, request):
        """
        Send a message with file attachment
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sender=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def file_types(self, request):
        """
        Get allowed file types and size limits
        """
        return Response(
            {
                "allowed_types": {
                    "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
                    "documents": [".pdf", ".doc", ".docx", ".txt", ".rtf"],
                    "spreadsheets": [".xls", ".xlsx", ".csv"],
                    "presentations": [".ppt", ".pptx"],
                    "archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
                    "other": [".json", ".xml", ".log"],
                },
                "max_file_size": "10MB",
                "max_file_size_bytes": 10 * 1024 * 1024,
            }
        )


class ChatMessagePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsParticipantOrOwner(permissions.BasePermission):
    """
    Custom permission to only allow participants of a chat room to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # For ChatRoom objects
        if isinstance(obj, ChatRoom):
            return obj.participants.filter(id=request.user.id).exists()
        
        # For ChatMessage objects
        if isinstance(obj, ChatMessage):
            return obj.chat_room.participants.filter(id=request.user.id).exists()
        
        return False


class ChatRoomViewSet(ModelViewSet):
    queryset = ChatRoom.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsParticipantOrOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['room_type', 'is_active']
    search_fields = ['name']
    ordering_fields = ['created_at', 'last_message_at']
    ordering = ['-last_message_at', '-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ChatRoomCreateSerializer
        return ChatRoomSerializer

    def get_queryset(self):
        """Filter chat rooms to only show those where user is a participant"""
        user = self.request.user
        return ChatRoom.objects.filter(
            participants=user
        ).prefetch_related('participants', 'chat_messages').distinct()

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Add a participant to the chat room"""
        chat_room = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            chat_room.add_participant(user)
            return Response(
                {'message': f'User {user.username} added to chat room'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """Remove a participant from the chat room"""
        chat_room = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            chat_room.remove_participant(user)
            return Response(
                {'message': f'User {user.username} removed from chat room'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def by_context(self, request):
        """Get chat rooms by context (request, job, bid, etc.)"""
        context_type = request.query_params.get('type')
        context_id = request.query_params.get('id')
        
        if not context_type or not context_id:
            return Response(
                {'error': 'type and id parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Map context types to models
        context_models = {
            'request': Request,
            'job': Job,
            'bid': Bid,
        }
        
        if context_type not in context_models:
            return Response(
                {'error': f'Invalid context type. Must be one of: {list(context_models.keys())}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        model_class = context_models[context_type]
        content_type = ContentType.objects.get_for_model(model_class)
        
        chat_rooms = self.get_queryset().filter(
            content_type=content_type,
            object_id=context_id
        )
        
        serializer = self.get_serializer(chat_rooms, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_or_get(self, request):
        """Create a new chat room or get existing one for a context"""
        context_type = request.data.get('type')
        context_id = request.data.get('id')
        participants_ids = request.data.get('participants', [])
        
        if not context_type or not context_id:
            return Response(
                {'error': 'type and id are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if chat room already exists for this context
        context_models = {
            'request': Request,
            'job': Job,
            'bid': Bid,
        }
        
        if context_type not in context_models:
            return Response(
                {'error': f'Invalid context type. Must be one of: {list(context_models.keys())}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        model_class = context_models[context_type]
        content_type = ContentType.objects.get_for_model(model_class)
        
        # Try to find existing chat room
        existing_room = ChatRoom.objects.filter(
            content_type=content_type,
            object_id=context_id,
            participants=request.user
        ).first()
        
        if existing_room:
            serializer = self.get_serializer(existing_room)
            return Response(serializer.data)
        
        # Create new chat room
        create_data = {
            'related_model': context_type,
            'related_id': context_id,
            'room_type': context_type,
            'participants_ids': participants_ids,
        }
        
        serializer = ChatRoomCreateSerializer(data=create_data, context={'request': request})
        if serializer.is_valid():
            chat_room = serializer.save()
            response_serializer = ChatRoomSerializer(chat_room, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatMessageViewSet(ModelViewSet):
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsParticipantOrOwner]
    pagination_class = ChatMessagePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['message_type', 'chat_room']
    search_fields = ['content']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter messages to only show those from chat rooms where user is a participant"""
        user = self.request.user
        return ChatMessage.objects.filter(
            chat_room__participants=user
        ).select_related('sender', 'chat_room', 'reply_to__sender').prefetch_related('read_by')

    def perform_create(self, serializer):
        """Set sender to current user when creating a message"""
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a specific message as read"""
        message = self.get_object()
        message.mark_as_read(request.user)
        return Response({'message': 'Message marked as read'})

    @action(detail=False, methods=['post'])
    def bulk_mark_as_read(self, request):
        """Mark multiple messages as read"""
        serializer = BulkMarkAsReadSerializer(data=request.data)
        if serializer.is_valid():
            message_ids = serializer.validated_data['message_ids']
            messages = ChatMessage.objects.filter(
                id__in=message_ids,
                chat_room__participants=request.user
            )
            
            for message in messages:
                message.mark_as_read(request.user)
            
            return Response({'message': f'{len(messages)} messages marked as read'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_room(self, request):
        """Get messages for a specific chat room"""
        room_id = request.query_params.get('room_id')
        
        if not room_id:
            return Response(
                {'error': 'room_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            chat_room = ChatRoom.objects.get(id=room_id, participants=request.user)
        except ChatRoom.DoesNotExist:
            return Response(
                {'error': 'Chat room not found or you are not a participant'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        messages = self.get_queryset().filter(chat_room=chat_room)
        
        # Apply pagination
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get total unread message count for the user"""
        user = request.user
        unread_count = ChatMessage.objects.filter(
            chat_room__participants=user
        ).exclude(
            read_by=user
        ).exclude(sender=user).count()
        
        return Response({'unread_count': unread_count})


# Keep original Message views for backward compatibility
class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        request_id = self.request.query_params.get("request_id")

        if request_id:
            # Filter messages for specific request
            return Message.objects.filter(
                Q(sender=user) | Q(receiver=user), request_id=request_id
            ).order_by("-created_at")
        else:
            # Return all messages for the user
            return Message.objects.filter(
                Q(sender=user) | Q(receiver=user)
            ).order_by("-created_at")


class MessageCreateView(generics.CreateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class MessageDetailView(generics.RetrieveAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(Q(sender=user) | Q(receiver=user))


class MessageMarkReadView(generics.UpdateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(receiver=user)

    def perform_update(self, serializer):
        from django.utils import timezone

        serializer.save(read=True, read_at=timezone.now())


class ConversationView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        other_user_id = self.kwargs.get("user_id")
        request_id = self.request.query_params.get("request_id")

        queryset = Message.objects.filter(
            Q(sender=user, receiver_id=other_user_id)
            | Q(sender_id=other_user_id, receiver=user)
        )

        if request_id:
            queryset = queryset.filter(request_id=request_id)

        return queryset.order_by("-created_at")


class GetConversationsView(generics.ListAPIView):
    """Get list of all conversations for a user"""

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        request_id = self.request.query_params.get("request_id")

        # Get the latest message from each conversation
        base_query = Message.objects.filter(Q(sender=user) | Q(receiver=user))

        if request_id:
            base_query = base_query.filter(request_id=request_id)

        # Get distinct conversations based on sender-receiver pairs and request
        conversations = {}
        for message in base_query.order_by("-created_at"):
            # Create a unique key for the conversation
            if message.sender == user:
                other_user = message.receiver
            else:
                other_user = message.sender

            conv_key = f"{message.request_id}_{other_user.id}"

            if conv_key not in conversations:
                conversations[conv_key] = message

        return list(conversations.values())


# Chat utility views
class ChatSystemStatusView(generics.GenericAPIView):
    """Get overall chat system status for a user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Get counts
        total_rooms = ChatRoom.objects.filter(participants=user).count()
        active_rooms = ChatRoom.objects.filter(participants=user, is_active=True).count()
        total_unread = ChatMessage.objects.filter(
            chat_room__participants=user
        ).exclude(read_by=user).exclude(sender=user).count()
        
        # Get recent rooms
        recent_rooms = ChatRoom.objects.filter(
            participants=user
        ).order_by('-last_message_at')[:5]
        
        recent_rooms_data = ChatRoomSerializer(
            recent_rooms, 
            many=True, 
            context={'request': request}
        ).data
        
        return Response({
            'total_rooms': total_rooms,
            'active_rooms': active_rooms,
            'total_unread': total_unread,
            'recent_rooms': recent_rooms_data,
        })
