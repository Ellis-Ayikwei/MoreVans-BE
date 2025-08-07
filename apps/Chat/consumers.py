import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, ConversationParticipant, ChatMessage
from .serializers import ChatMessageSerializer, ConversationSerializer

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat functionality
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Get conversation ID from URL
        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        self.conversation_group_name = f'chat_{self.conversation_id}'
        
        # Check if user is participant
        is_participant = await self.check_participant()
        if not is_participant:
            await self.close()
            return
        
        # Join conversation group
        await self.channel_layer.group_add(
            self.conversation_group_name,
            self.channel_name
        )
        
        # Also join user's personal notification group
        self.user_group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial connection message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to chat'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'conversation_group_name'):
            # Leave conversation group
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name
            )
        
        if hasattr(self, 'user_group_name'):
            # Leave user group
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'send_message':
                await self.handle_send_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'mark_read':
                await self.handle_mark_read(data)
            elif message_type == 'edit_message':
                await self.handle_edit_message(data)
            elif message_type == 'delete_message':
                await self.handle_delete_message(data)
            elif message_type == 'react':
                await self.handle_reaction(data)
            else:
                await self.send_error('Unknown message type')
        
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON')
        except Exception as e:
            await self.send_error(str(e))
    
    async def handle_send_message(self, data):
        """Handle sending a new message"""
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        reply_to_id = data.get('reply_to')
        metadata = data.get('metadata', {})
        
        if not content and message_type == 'text':
            await self.send_error('Message content is required')
            return
        
        # Create message
        message = await self.create_message(
            content=content,
            message_type=message_type,
            reply_to_id=reply_to_id,
            metadata=metadata
        )
        
        # Serialize message
        message_data = await self.serialize_message(message)
        
        # Send message to conversation group
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'chat_message',
                'message': message_data,
                'sender_id': str(self.user.id)
            }
        )
        
        # Send notifications to offline users
        await self.send_notifications(message)
    
    async def handle_typing(self, data):
        """Handle typing indicator"""
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'is_typing': is_typing
            }
        )
    
    async def handle_mark_read(self, data):
        """Handle marking messages as read"""
        message_ids = data.get('message_ids', [])
        
        if message_ids:
            await self.mark_messages_read(message_ids)
            
            # Notify sender that messages were read
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'messages_read',
                    'message_ids': message_ids,
                    'user_id': str(self.user.id)
                }
            )
    
    async def handle_edit_message(self, data):
        """Handle editing a message"""
        message_id = data.get('message_id')
        new_content = data.get('content', '').strip()
        
        if not message_id or not new_content:
            await self.send_error('Message ID and content are required')
            return
        
        # Edit message
        success, message = await self.edit_message(message_id, new_content)
        
        if success:
            message_data = await self.serialize_message(message)
            
            # Send updated message to group
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'message_edited',
                    'message': message_data
                }
            )
        else:
            await self.send_error('Could not edit message')
    
    async def handle_delete_message(self, data):
        """Handle deleting a message"""
        message_id = data.get('message_id')
        
        if not message_id:
            await self.send_error('Message ID is required')
            return
        
        # Delete message
        success = await self.delete_message(message_id)
        
        if success:
            # Send deletion notification to group
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'message_deleted',
                    'message_id': message_id
                }
            )
        else:
            await self.send_error('Could not delete message')
    
    async def handle_reaction(self, data):
        """Handle message reactions"""
        message_id = data.get('message_id')
        emoji = data.get('emoji')
        
        if not message_id or not emoji:
            await self.send_error('Message ID and emoji are required')
            return
        
        # Toggle reaction
        action, reaction = await self.toggle_reaction(message_id, emoji)
        
        # Send reaction update to group
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'reaction_update',
                'message_id': message_id,
                'user_id': str(self.user.id),
                'username': self.user.username,
                'emoji': emoji,
                'action': action
            }
        )
    
    # Event handlers for group messages
    
    async def chat_message(self, event):
        """Handle chat message event"""
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Handle typing indicator event"""
        # Don't send typing indicator to the user who's typing
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    async def messages_read(self, event):
        """Handle messages read event"""
        await self.send(text_data=json.dumps({
            'type': 'messages_read',
            'message_ids': event['message_ids'],
            'user_id': event['user_id']
        }))
    
    async def message_edited(self, event):
        """Handle message edited event"""
        await self.send(text_data=json.dumps({
            'type': 'message_edited',
            'message': event['message']
        }))
    
    async def message_deleted(self, event):
        """Handle message deleted event"""
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id']
        }))
    
    async def reaction_update(self, event):
        """Handle reaction update event"""
        await self.send(text_data=json.dumps({
            'type': 'reaction_update',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'username': event['username'],
            'emoji': event['emoji'],
            'action': event['action']
        }))
    
    async def send_error(self, error_message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message
        }))
    
    # Database operations
    
    @database_sync_to_async
    def check_participant(self):
        """Check if user is a participant in the conversation"""
        try:
            return ConversationParticipant.objects.filter(
                conversation_id=self.conversation_id,
                user=self.user,
                is_active=True
            ).exists()
        except:
            return False
    
    @database_sync_to_async
    def create_message(self, content, message_type, reply_to_id, metadata):
        """Create a new message in the database"""
        message = ChatMessage.objects.create(
            conversation_id=self.conversation_id,
            sender=self.user,
            content=content,
            message_type=message_type,
            reply_to_id=reply_to_id,
            metadata=metadata
        )
        
        # Mark conversation as read for sender
        ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id,
            user=self.user
        ).update(last_read_at=message.created_at)
        
        return message
    
    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize a message for sending"""
        # Refresh from DB to get all relations
        message = ChatMessage.objects.select_related(
            'sender', 'reply_to', 'conversation'
        ).prefetch_related(
            'reactions__user',
            'read_receipts__user'
        ).get(id=message.id)
        
        serializer = ChatMessageSerializer(message)
        return serializer.data
    
    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        """Mark messages as read"""
        from .models import MessageRead
        
        # Create read receipts
        read_receipts = []
        for msg_id in message_ids:
            read_receipts.append(
                MessageRead(message_id=msg_id, user=self.user)
            )
        
        MessageRead.objects.bulk_create(
            read_receipts,
            ignore_conflicts=True
        )
        
        # Update last read time
        latest_message = ChatMessage.objects.filter(
            id__in=message_ids
        ).order_by('-created_at').first()
        
        if latest_message:
            ConversationParticipant.objects.filter(
                conversation_id=self.conversation_id,
                user=self.user
            ).update(last_read_at=latest_message.created_at)
    
    @database_sync_to_async
    def edit_message(self, message_id, new_content):
        """Edit a message"""
        try:
            message = ChatMessage.objects.get(
                id=message_id,
                conversation_id=self.conversation_id,
                sender=self.user,
                is_deleted=False
            )
            
            from django.utils import timezone
            message.content = new_content
            message.is_edited = True
            message.edited_at = timezone.now()
            message.save()
            
            return True, message
        except ChatMessage.DoesNotExist:
            return False, None
    
    @database_sync_to_async
    def delete_message(self, message_id):
        """Delete a message"""
        try:
            message = ChatMessage.objects.get(
                id=message_id,
                conversation_id=self.conversation_id
            )
            
            # Check permission
            participant = ConversationParticipant.objects.filter(
                conversation_id=self.conversation_id,
                user=self.user
            ).first()
            
            if message.sender == self.user or (participant and participant.role == 'admin'):
                from django.utils import timezone
                message.is_deleted = True
                message.deleted_at = timezone.now()
                message.content = "[Message deleted]"
                message.save()
                return True
            
            return False
        except ChatMessage.DoesNotExist:
            return False
    
    @database_sync_to_async
    def toggle_reaction(self, message_id, emoji):
        """Toggle a reaction on a message"""
        from .models import MessageReaction
        
        try:
            message = ChatMessage.objects.get(
                id=message_id,
                conversation_id=self.conversation_id
            )
            
            # Check if reaction exists
            reaction = MessageReaction.objects.filter(
                message=message,
                user=self.user,
                emoji=emoji
            ).first()
            
            if reaction:
                reaction.delete()
                return 'removed', None
            else:
                reaction = MessageReaction.objects.create(
                    message=message,
                    user=self.user,
                    emoji=emoji
                )
                return 'added', reaction
        
        except ChatMessage.DoesNotExist:
            return None, None
    
    @database_sync_to_async
    def send_notifications(self, message):
        """Send notifications to offline users"""
        # Get all participants except sender
        participants = ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id,
            is_active=True,
            notify_on_message=True
        ).exclude(user=self.user).select_related('user')
        
        for participant in participants:
            # Send to user's personal channel for notifications
            user_group = f'user_{participant.user.id}'
            
            # This will be received by any other connections the user has
            self.channel_layer.group_send(
                user_group,
                {
                    'type': 'notification',
                    'notification': {
                        'type': 'new_message',
                        'conversation_id': str(self.conversation_id),
                        'message': f"New message from {self.user.username}",
                        'sender': self.user.username
                    }
                }
            )


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for general notifications
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Join user's personal notification group
        self.user_group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def notification(self, event):
        """Handle notification event"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))