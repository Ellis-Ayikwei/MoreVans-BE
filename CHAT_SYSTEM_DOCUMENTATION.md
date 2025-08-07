# MoreVans Chat System Documentation

## Overview

The MoreVans chat system is a comprehensive real-time messaging solution that enables communication across different contexts within the platform. Users can chat about requests, jobs, bids, support tickets, and in general chat rooms.

## Features

### Multi-Context Chat Support
- **Request Chat**: Communication around specific delivery/transport requests
- **Job Chat**: Discussion about ongoing jobs
- **Bidding Chat**: Communication during the bidding process
- **Support Chat**: Customer support interactions
- **Provider-Customer Chat**: Direct communication between service providers and customers
- **General Chat**: Open communication channels

### Real-Time Messaging
- WebSocket-based real-time messaging using Django Channels
- Live typing indicators
- Real-time message delivery and read receipts
- Online/offline status tracking

### Rich Message Types
- Text messages
- Image attachments
- File attachments
- System messages
- Status update messages
- Reply functionality

### Advanced Features
- Message read tracking
- Participant management
- Chat room permissions
- Automatic notifications
- Admin management interface
- Analytics and reporting

## Architecture

### Models

#### ChatRoom
The main chat room model that can be associated with different objects:

```python
class ChatRoom(Basemodel):
    ROOM_TYPES = [
        ("request", "Request Chat"),
        ("job", "Job Chat"),
        ("bidding", "Bidding Chat"),
        ("support", "Support Chat"),
        ("general", "General Chat"),
        ("provider_customer", "Provider-Customer Chat"),
    ]
    
    name = models.CharField(max_length=255, blank=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    content_type = models.ForeignKey(ContentType, ...)  # Generic relation
    object_id = models.PositiveIntegerField(...)
    participants = models.ManyToManyField(User, ...)
    is_active = models.BooleanField(default=True)
    is_private = models.BooleanField(default=True)
    last_message_at = models.DateTimeField(...)
```

#### ChatMessage
Individual messages within chat rooms:

```python
class ChatMessage(Basemodel):
    MESSAGE_TYPES = [
        ("text", "Text"),
        ("image", "Image"),
        ("file", "File"),
        ("system", "System Message"),
        ("bid_update", "Bid Update"),
        ("status_update", "Status Update"),
    ]
    
    chat_room = models.ForeignKey(ChatRoom, ...)
    sender = models.ForeignKey(User, ...)
    content = models.TextField(blank=True)
    message_type = models.CharField(...)
    attachment = models.FileField(...)
    read_by = models.ManyToManyField(User, through='ChatMessageRead')
    reply_to = models.ForeignKey('self', ...)  # Reply functionality
    system_data = models.JSONField(...)  # Additional data for system messages
```

#### ChatMessageRead
Tracks message read status:

```python
class ChatMessageRead(Basemodel):
    message = models.ForeignKey(ChatMessage, ...)
    user = models.ForeignKey(User, ...)
    read_at = models.DateTimeField(auto_now_add=True)
```

### API Endpoints

#### Chat Rooms
- `GET /api/v1/chat-rooms/` - List user's chat rooms
- `POST /api/v1/chat-rooms/` - Create new chat room
- `GET /api/v1/chat-rooms/{id}/` - Get specific chat room
- `POST /api/v1/chat-rooms/{id}/add_participant/` - Add participant
- `POST /api/v1/chat-rooms/{id}/remove_participant/` - Remove participant
- `GET /api/v1/chat-rooms/by_context/?type=request&id=123` - Get rooms by context
- `POST /api/v1/chat-rooms/create_or_get/` - Create or get existing room

#### Chat Messages
- `GET /api/v1/chat-messages/` - List messages
- `POST /api/v1/chat-messages/` - Send new message
- `GET /api/v1/chat-messages/by_room/?room_id=123` - Get messages for room
- `POST /api/v1/chat-messages/{id}/mark_as_read/` - Mark message as read
- `POST /api/v1/chat-messages/bulk_mark_as_read/` - Mark multiple messages as read
- `GET /api/v1/chat-messages/unread_count/` - Get total unread count

#### Chat System Status
- `GET /api/v1/chat/status/` - Get overall chat system status

### WebSocket Connections

#### Chat Room WebSocket
Connect to: `ws://localhost:8000/ws/chat/{room_id}/?token={jwt_token}`

**Supported message types:**
```json
// Send message
{
  "type": "chat_message",
  "content": "Hello world!",
  "reply_to": null
}

// Typing indicator
{
  "type": "typing",
  "is_typing": true
}

// Mark messages as read
{
  "type": "mark_read",
  "message_ids": [1, 2, 3]
}

// Ping for connection health
{
  "type": "ping",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Received message types:**
```json
// New message
{
  "type": "chat_message",
  "message": {
    "id": 123,
    "content": "Hello!",
    "sender_data": {...},
    "created_at": "..."
  }
}

// Typing indicator
{
  "type": "typing_indicator",
  "user": "username",
  "user_id": "123",
  "is_typing": true
}

// User joined/left
{
  "type": "user_joined",
  "user": "username",
  "user_id": "123"
}

// Messages marked as read
{
  "type": "messages_read",
  "user_id": "123",
  "message_ids": [1, 2, 3]
}
```

#### Notifications WebSocket
Connect to: `ws://localhost:8000/ws/notifications/?token={jwt_token}`

Receives real-time notifications about new chat messages and system events.

## Usage Examples

### Creating a Chat Room for a Request

```python
# API call
POST /api/v1/chat-rooms/
{
  "room_type": "request",
  "related_model": "request",
  "related_id": 123,
  "participants_ids": [456, 789]
}
```

### Sending a Message

```python
# API call
POST /api/v1/chat-messages/
{
  "chat_room": 1,
  "content": "Hello, how is the delivery going?",
  "message_type": "text"
}
```

### WebSocket Message Sending

```javascript
// Connect to WebSocket
const socket = new WebSocket('ws://localhost:8000/ws/chat/1/?token=' + jwtToken);

// Send message
socket.send(JSON.stringify({
  type: 'chat_message',
  content: 'Hello world!'
}));

// Listen for messages
socket.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.type === 'chat_message') {
    displayMessage(data.message);
  }
};
```

## Integration with Business Logic

### Automatic Chat Room Creation
Chat rooms are automatically created when:
- A new request is submitted
- A job is created
- A bid is placed
- A support ticket is opened

### Automatic Notifications
System automatically sends notifications for:
- Bid status changes (submitted, accepted, rejected)
- Job status updates
- Request status changes
- New messages in chat rooms

### Example: Bid Update Notification

```python
# When a bid is accepted, this is automatically triggered:
ChatNotificationService.notify_bid_update(
    bid=bid_instance,
    action='accepted',
    user=current_user
)
```

## Permissions and Security

### Access Control
- Users can only access chat rooms they are participants in
- Private rooms are invitation-only
- Support staff have access to support chat rooms

### Authentication
- JWT token-based authentication for WebSocket connections
- Standard Django REST framework authentication for API endpoints

### Data Validation
- Message content validation
- Participant verification
- File upload restrictions

## Admin Interface

The admin interface provides:
- Chat room management
- Message moderation
- Participant management
- Analytics dashboard
- Bulk operations

Access at: `/admin/Message/`

## Configuration

### Settings Requirements

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'channels',
    'channels_redis',
    'django_filters',
    'apps.Message',
]

# Channels configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis://127.0.0.1:6379/0")],
        },
    },
}

# WebSocket routing
ASGI_APPLICATION = 'backend.asgi.application'
```

### Dependencies

```txt
Django>=4.2
djangorestframework
channels
channels-redis
django-filter
redis
```

## Management Commands

### Create Chat Rooms for Existing Objects
```bash
python manage.py create_chat_rooms
```

### Cleanup Old Chat Rooms
```bash
python manage.py cleanup_chat_rooms --days=30
```

## Testing

### Unit Tests
Run the test suite:
```bash
python manage.py test apps.Message
```

### WebSocket Testing
Use the provided test clients for WebSocket functionality testing.

## Performance Considerations

### Database Optimization
- Indexes on frequently queried fields
- Efficient queryset usage with select_related and prefetch_related
- Pagination for large message lists

### Redis Configuration
- Configure Redis for optimal WebSocket performance
- Use Redis for session storage and caching

### File Storage
- Configure appropriate file storage backend for attachments
- Implement file size and type restrictions

## Monitoring and Analytics

### Built-in Analytics
```python
from apps.Message.chat_services import ChatAutomationService

analytics = ChatAutomationService.generate_chat_analytics()
print(analytics)
```

### Metrics Tracked
- Total chat rooms
- Active chat rooms
- Message volume (daily, weekly, monthly)
- User engagement metrics
- Room type distribution

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check Redis connection
   - Verify JWT token validity
   - Check CORS settings

2. **Messages Not Delivering**
   - Verify user is participant in chat room
   - Check WebSocket connection status
   - Verify Redis is running

3. **Circular Import Errors**
   - Signals are configured with lazy imports
   - Models use string references where needed

### Debugging

Enable debug logging:
```python
LOGGING = {
    'loggers': {
        'channels': {
            'level': 'DEBUG',
        },
        'apps.Message': {
            'level': 'DEBUG',
        }
    }
}
```

## Future Enhancements

### Planned Features
- Message encryption
- Voice messages
- Video chat integration
- Message search functionality
- Advanced moderation tools
- Message templates
- Auto-translation
- Bot integration

### Scalability
- Message archiving
- Sharding for large deployments
- CDN integration for file attachments
- Multiple Redis instances

## Support

For technical support or questions about the chat system implementation, please refer to:
- API documentation at `/api/docs/`
- Admin interface at `/admin/`
- Django logs for error tracking

---

*This documentation covers the comprehensive chat system implementation for the MoreVans platform. The system is designed to be scalable, secure, and user-friendly while providing real-time communication capabilities across all platform contexts.*