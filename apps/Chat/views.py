from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q, Count, Max, Prefetch
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import (
    Conversation, ConversationParticipant, 
    ChatMessage, MessageReaction, MessageRead
)
from .serializers import (
    ConversationSerializer, ConversationCreateSerializer,
    ConversationParticipantSerializer, ChatMessageSerializer,
    MessageCreateSerializer, MessageReactionSerializer
)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat conversations
    """
    queryset = Conversation.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Conversation.objects.filter(
            participants__user=user,
            participants__is_active=True
        ).distinct()
        
        # Filter by conversation type
        conv_type = self.request.query_params.get('type')
        if conv_type:
            queryset = queryset.filter(conversation_type=conv_type)
        
        # Filter by active/archived status
        is_archived = self.request.query_params.get('archived')
        if is_archived is not None:
            queryset = queryset.filter(is_archived=is_archived.lower() == 'true')
        else:
            queryset = queryset.filter(is_archived=False)
        
        # Prefetch related data for performance
        queryset = queryset.prefetch_related(
            Prefetch(
                'participants',
                queryset=ConversationParticipant.objects.select_related('user')
            ),
            'messages'
        ).annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Add a participant to the conversation"""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'participant')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if requester has permission (must be admin or moderator)
        requester_participant = conversation.participants.filter(
            user=request.user
        ).first()
        
        if not requester_participant or requester_participant.role not in ['admin', 'moderator']:
            return Response(
                {'error': 'You do not have permission to add participants'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from apps.User.models import User
        try:
            user = User.objects.get(id=user_id)
            participant = conversation.add_participant(user, role)
            serializer = ConversationParticipantSerializer(participant)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """Remove a participant from the conversation"""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check permissions
        requester_participant = conversation.participants.filter(
            user=request.user
        ).first()
        
        # Users can remove themselves, admins/moderators can remove others
        if str(request.user.id) != user_id:
            if not requester_participant or requester_participant.role not in ['admin', 'moderator']:
                return Response(
                    {'error': 'You do not have permission to remove participants'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        from apps.User.models import User
        try:
            user = User.objects.get(id=user_id)
            if conversation.remove_participant(user):
                return Response({'success': True})
            return Response(
                {'error': 'Participant not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a conversation"""
        conversation = self.get_object()
        conversation.is_archived = True
        conversation.save()
        return Response({'success': True})
    
    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """Unarchive a conversation"""
        conversation = self.get_object()
        conversation.is_archived = False
        conversation.save()
        return Response({'success': True})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark all messages in conversation as read"""
        conversation = self.get_object()
        participant = conversation.participants.filter(
            user=request.user
        ).first()
        
        if participant:
            participant.mark_as_read()
            return Response({'success': True})
        
        return Response(
            {'error': 'You are not a participant'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    @action(detail=False, methods=['get'])
    def unread_counts(self, request):
        """Get unread counts for all conversations"""
        user = request.user
        conversations = self.get_queryset()
        
        counts = {}
        for conv in conversations:
            count = conv.get_unread_count(user)
            if count > 0:
                counts[str(conv.id)] = count
        
        return Response({
            'counts': counts,
            'total': sum(counts.values())
        })
    
    @action(detail=False, methods=['post'])
    def create_support_conversation(self, request):
        """Create a support conversation"""
        from apps.Chat.utils import create_support_conversation
        
        support_type = request.data.get('support_type', 'general')
        title = request.data.get('title')
        initial_message = request.data.get('message')
        
        if not initial_message:
            return Response(
                {'error': 'Initial message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create support conversation
        conversation = create_support_conversation(
            user=request.user,
            support_type=support_type,
            title=title
        )
        
        # Add user's initial message
        from .models import ChatMessage
        ChatMessage.objects.create(
            conversation=conversation,
            sender=request.user,
            content=initial_message,
            message_type='text'
        )
        
        # Add system message
        from apps.Chat.utils import add_system_message
        add_system_message(
            conversation,
            f"Support ticket created. Type: {support_type}. A support agent will respond shortly.",
            metadata={'support_type': support_type}
        )
        
        serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat messages
    """
    queryset = ChatMessage.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return ChatMessageSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Get messages from conversations where user is a participant
        queryset = ChatMessage.objects.filter(
            conversation__participants__user=user,
            conversation__participants__is_active=True
        ).distinct()
        
        # Filter by conversation
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        
        # Filter deleted messages
        show_deleted = self.request.query_params.get('show_deleted', 'false')
        if show_deleted.lower() != 'true':
            queryset = queryset.filter(is_deleted=False)
        
        # Prefetch related data
        queryset = queryset.select_related(
            'sender', 'conversation', 'reply_to'
        ).prefetch_related(
            'reactions__user',
            'read_receipts__user'
        ).order_by('created_at')
        
        return queryset
    
    def perform_create(self, serializer):
        """Create a new message and mark conversation as read"""
        message = serializer.save()
        
        # Mark conversation as read for sender
        participant = message.conversation.participants.filter(
            user=self.request.user
        ).first()
        if participant:
            participant.mark_as_read()
        
        # TODO: Send WebSocket notification to other participants
        
    @action(detail=True, methods=['post'])
    def edit(self, request, pk=None):
        """Edit a message"""
        message = self.get_object()
        
        # Only sender can edit their message
        if message.sender != request.user:
            return Response(
                {'error': 'You can only edit your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Can't edit deleted messages
        if message.is_deleted:
            return Response(
                {'error': 'Cannot edit deleted messages'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        content = request.data.get('content')
        if not content:
            return Response(
                {'error': 'Content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.content = content
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save()
        
        serializer = ChatMessageSerializer(message, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def delete(self, request, pk=None):
        """Soft delete a message"""
        message = self.get_object()
        
        # Only sender or conversation admin can delete
        participant = message.conversation.participants.filter(
            user=request.user
        ).first()
        
        if message.sender != request.user and (not participant or participant.role != 'admin'):
            return Response(
                {'error': 'You do not have permission to delete this message'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.content = "[Message deleted]"
        message.save()
        
        return Response({'success': True})
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Add or remove a reaction to a message"""
        message = self.get_object()
        emoji = request.data.get('emoji')
        
        if not emoji:
            return Response(
                {'error': 'Emoji is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already reacted with this emoji
        reaction = message.reactions.filter(
            user=request.user,
            emoji=emoji
        ).first()
        
        if reaction:
            # Remove reaction
            reaction.delete()
            return Response({'action': 'removed'})
        else:
            # Add reaction
            reaction = MessageReaction.objects.create(
                message=message,
                user=request.user,
                emoji=emoji
            )
            serializer = MessageReactionSerializer(reaction)
            return Response({
                'action': 'added',
                'reaction': serializer.data
            })
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a message as read"""
        message = self.get_object()
        
        # Create or update read receipt
        read_receipt, created = MessageRead.objects.get_or_create(
            message=message,
            user=request.user
        )
        
        # Update participant's last read time
        participant = message.conversation.participants.filter(
            user=request.user
        ).first()
        if participant and message.created_at > participant.last_read_at:
            participant.last_read_at = message.created_at
            participant.save()
        
        return Response({'success': True})
    
    @action(detail=False, methods=['post'])
    def mark_multiple_read(self, request):
        """Mark multiple messages as read"""
        message_ids = request.data.get('message_ids', [])
        
        if not message_ids:
            return Response(
                {'error': 'message_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        messages = self.get_queryset().filter(id__in=message_ids)
        
        # Create read receipts
        read_receipts = []
        for message in messages:
            read_receipts.append(
                MessageRead(message=message, user=request.user)
            )
        
        MessageRead.objects.bulk_create(
            read_receipts,
            ignore_conflicts=True
        )
        
        # Update participant's last read time
        latest_message = messages.order_by('-created_at').first()
        if latest_message:
            participant = latest_message.conversation.participants.filter(
                user=request.user
            ).first()
            if participant:
                participant.last_read_at = latest_message.created_at
                participant.save()
        
        return Response({'success': True, 'count': len(messages)})