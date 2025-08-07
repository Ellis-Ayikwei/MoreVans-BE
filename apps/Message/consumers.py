import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs
import logging

from .models import ChatRoom, ChatMessage, ChatMessageRead
from .serializer import ChatMessageSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat functionality
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Authenticate user
        self.user = await self.get_user_from_scope()
        
        if self.user is None or isinstance(self.user, AnonymousUser):
            await self.close(code=4001)
            return
        
        # Check if user is participant in the chat room
        is_participant = await self.check_room_participant()
        if not is_participant:
            await self.close(code=4003)
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send user join notification to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user': self.user.username,
                'user_id': str(self.user.id)
            }
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            # Send user leave notification to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user': self.user.username if self.user else 'Unknown',
                    'user_id': str(self.user.id) if self.user else None
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'typing':
                await self.handle_typing(text_data_json)
            elif message_type == 'mark_read':
                await self.handle_mark_read(text_data_json)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))

    async def handle_chat_message(self, data):
        """Handle new chat message"""
        content = data.get('content', '').strip()
        reply_to_id = data.get('reply_to')
        
        if not content:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message content cannot be empty'
            }))
            return
        
        # Save message to database
        message = await self.save_message(content, reply_to_id)
        
        if message:
            # Serialize message
            message_data = await self.serialize_message(message)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_data
                }
            )

    async def handle_typing(self, data):
        """Handle typing indicator"""
        is_typing = data.get('is_typing', False)
        
        # Send typing indicator to room group (excluding sender)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user': self.user.username,
                'user_id': str(self.user.id),
                'is_typing': is_typing,
                'sender_channel': self.channel_name
            }
        )

    async def handle_mark_read(self, data):
        """Handle mark message as read"""
        message_ids = data.get('message_ids', [])
        
        if message_ids:
            await self.mark_messages_read(message_ids)
            
            # Notify room about read status
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'messages_read',
                    'user_id': str(self.user.id),
                    'message_ids': message_ids
                }
            )

    # WebSocket message handlers
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket (excluding sender)"""
        if event.get('sender_channel') != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user': event['user'],
                'user_id': event['user_id'],
                'is_typing': event['is_typing']
            }))

    async def messages_read(self, event):
        """Send read status update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'messages_read',
            'user_id': event['user_id'],
            'message_ids': event['message_ids']
        }))

    async def user_joined(self, event):
        """Send user joined notification to WebSocket"""
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user': event['user'],
                'user_id': event['user_id']
            }))

    async def user_left(self, event):
        """Send user left notification to WebSocket"""
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user': event['user'],
                'user_id': event['user_id']
            }))

    async def system_message(self, event):
        """Send system message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'system_message',
            'message': event['message']
        }))

    # Database operations
    @database_sync_to_async
    def get_user_from_scope(self):
        """Extract and validate user from WebSocket scope"""
        try:
            # Try to get token from query string
            query_string = self.scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]
            
            if not token:
                # Try to get from headers
                headers = dict(self.scope.get('headers', []))
                auth_header = headers.get(b'authorization', b'').decode()
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
            
            if not token:
                return None
            
            # Validate JWT token
            try:
                validated_token = UntypedToken(token)
                user_id = validated_token['user_id']
                user = User.objects.get(id=user_id)
                return user
            except (InvalidToken, TokenError, User.DoesNotExist):
                return None
                
        except Exception as e:
            logger.error(f"Error authenticating WebSocket user: {e}")
            return None

    @database_sync_to_async
    def check_room_participant(self):
        """Check if user is a participant in the chat room"""
        try:
            chat_room = ChatRoom.objects.get(id=self.room_id)
            return chat_room.participants.filter(id=self.user.id).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content, reply_to_id=None):
        """Save chat message to database"""
        try:
            chat_room = ChatRoom.objects.get(id=self.room_id)
            
            reply_to = None
            if reply_to_id:
                try:
                    reply_to = ChatMessage.objects.get(id=reply_to_id, chat_room=chat_room)
                except ChatMessage.DoesNotExist:
                    pass
            
            message = ChatMessage.objects.create(
                chat_room=chat_room,
                sender=self.user,
                content=content,
                reply_to=reply_to
            )
            return message
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize message for WebSocket transmission"""
        from django.http import HttpRequest
        
        # Create a mock request for serializer context
        request = HttpRequest()
        request.user = self.user
        
        serializer = ChatMessageSerializer(message, context={'request': request})
        return serializer.data

    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        """Mark messages as read by current user"""
        try:
            messages = ChatMessage.objects.filter(
                id__in=message_ids,
                chat_room__id=self.room_id,
                chat_room__participants=self.user
            ).exclude(sender=self.user)
            
            for message in messages:
                ChatMessageRead.objects.get_or_create(
                    message=message,
                    user=self.user
                )
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications
    """
    
    async def connect(self):
        """Handle WebSocket connection for notifications"""
        # Authenticate user
        self.user = await self.get_user_from_scope()
        
        if self.user is None or isinstance(self.user, AnonymousUser):
            await self.close(code=4001)
            return
        
        self.user_group_name = f'user_{self.user.id}'
        
        # Join user-specific group
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

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
                
        except json.JSONDecodeError:
            pass

    async def chat_notification(self, event):
        """Send chat notification to user"""
        await self.send(text_data=json.dumps({
            'type': 'chat_notification',
            'chat_room_id': event['chat_room_id'],
            'message': event['message'],
            'sender': event['sender']
        }))

    async def system_notification(self, event):
        """Send system notification to user"""
        await self.send(text_data=json.dumps({
            'type': 'system_notification',
            'message': event['message'],
            'data': event.get('data', {})
        }))

    @database_sync_to_async
    def get_user_from_scope(self):
        """Extract and validate user from WebSocket scope"""
        try:
            # Try to get token from query string
            query_string = self.scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]
            
            if not token:
                # Try to get from headers
                headers = dict(self.scope.get('headers', []))
                auth_header = headers.get(b'authorization', b'').decode()
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
            
            if not token:
                return None
            
            # Validate JWT token
            try:
                validated_token = UntypedToken(token)
                user_id = validated_token['user_id']
                user = User.objects.get(id=user_id)
                return user
            except (InvalidToken, TokenError, User.DoesNotExist):
                return None
                
        except Exception as e:
            logger.error(f"Error authenticating WebSocket user: {e}")
            return None