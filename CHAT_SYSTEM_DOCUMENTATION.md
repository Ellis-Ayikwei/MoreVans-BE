# MoreVans Chat System Documentation

## Overview

The MoreVans chat system provides real-time messaging capabilities across the entire platform, enabling communication between users in various contexts including bidding negotiations, job discussions, support tickets, and dispute resolution.

## Features

- **Real-time messaging** using Django Channels and WebSockets
- **Multiple conversation types** (direct, job, bid, request, support, dispute)
- **File attachments** support (images, documents, etc.)
- **Message reactions** with emojis
- **Read receipts** and typing indicators
- **Message editing and deletion**
- **Reply to messages**
- **System messages** for automated notifications
- **Notification integration** for offline users
- **Role-based permissions** (admin, moderator, participant, observer)

## Architecture

### Models

1. **Conversation**
   - Central model for all chat conversations
   - Can be linked to any model using Generic Foreign Keys
   - Supports different conversation types
   - Manages participants and settings

2. **ConversationParticipant**
   - Links users to conversations with roles
   - Tracks read status and notification preferences
   - Manages join/leave timestamps

3. **ChatMessage**
   - Stores individual messages
   - Supports various message types (text, image, file, audio, video, location, system)
   - Handles attachments and metadata
   - Tracks edit/delete status

4. **MessageReaction**
   - Stores emoji reactions to messages

5. **MessageRead**
   - Tracks read receipts for messages

### API Endpoints

#### Conversations

- `GET /chat/conversations/` - List user's conversations
- `POST /chat/conversations/` - Create new conversation
- `GET /chat/conversations/{id}/` - Get conversation details
- `POST /chat/conversations/{id}/add_participant/` - Add participant
- `POST /chat/conversations/{id}/remove_participant/` - Remove participant
- `POST /chat/conversations/{id}/archive/` - Archive conversation
- `POST /chat/conversations/{id}/unarchive/` - Unarchive conversation
- `POST /chat/conversations/{id}/mark_read/` - Mark all messages as read
- `GET /chat/conversations/unread_counts/` - Get unread counts
- `POST /chat/conversations/create_support_conversation/` - Create support chat

#### Messages

- `GET /chat/messages/` - List messages (filterable by conversation)
- `POST /chat/messages/` - Send new message
- `GET /chat/messages/{id}/` - Get message details
- `POST /chat/messages/{id}/edit/` - Edit message
- `POST /chat/messages/{id}/delete/` - Delete message
- `POST /chat/messages/{id}/react/` - Add/remove reaction
- `POST /chat/messages/{id}/mark_read/` - Mark message as read
- `POST /chat/messages/mark_multiple_read/` - Mark multiple messages as read

#### Integration Endpoints

- `GET /bids/{id}/conversation/` - Get bid conversation
- `GET /jobs/{id}/conversation/` - Get job conversation
- `GET /disputes/{id}/conversation/` - Get dispute conversation

### WebSocket Endpoints

- `ws/chat/{conversation_id}/` - Real-time chat for specific conversation
- `ws/notifications/` - General notifications channel

### WebSocket Message Types

#### Outgoing (Client to Server)

```json
// Send message
{
  "type": "send_message",
  "content": "Hello!",
  "message_type": "text",
  "reply_to": "message_id",  // optional
  "metadata": {}  // optional
}

// Typing indicator
{
  "type": "typing",
  "is_typing": true
}

// Mark messages as read
{
  "type": "mark_read",
  "message_ids": ["id1", "id2"]
}

// Edit message
{
  "type": "edit_message",
  "message_id": "id",
  "content": "Updated content"
}

// Delete message
{
  "type": "delete_message",
  "message_id": "id"
}

// React to message
{
  "type": "react",
  "message_id": "id",
  "emoji": "👍"
}
```

#### Incoming (Server to Client)

```json
// New message
{
  "type": "new_message",
  "message": { /* message data */ }
}

// Typing indicator
{
  "type": "typing",
  "user_id": "id",
  "username": "username",
  "is_typing": true
}

// Messages read
{
  "type": "messages_read",
  "message_ids": ["id1", "id2"],
  "user_id": "id"
}

// Message edited
{
  "type": "message_edited",
  "message": { /* updated message data */ }
}

// Message deleted
{
  "type": "message_deleted",
  "message_id": "id"
}

// Reaction update
{
  "type": "reaction_update",
  "message_id": "id",
  "user_id": "id",
  "username": "username",
  "emoji": "👍",
  "action": "added|removed"
}
```

## Integration Examples

### Creating a Bid Conversation

```python
from apps.Chat.utils import create_bid_conversation

# When a bid is created
bid = Bid.objects.create(...)
conversation = create_bid_conversation(bid)
```

### Creating a Job Conversation

```python
from apps.Chat.utils import create_job_conversation

# When a job is assigned
job.assign_provider(provider)
conversation = create_job_conversation(job)
```

### Creating a Support Conversation

```python
from apps.Chat.utils import create_support_conversation

# When user needs support
conversation = create_support_conversation(
    user=request.user,
    support_type='technical',
    title='Login Issue'
)
```

### Adding System Messages

```python
from apps.Chat.utils import add_system_message

# Add automated notification
add_system_message(
    conversation,
    "Provider has been assigned to this job",
    metadata={'action': 'provider_assigned'}
)
```

## Frontend Integration Guide

### 1. Establish WebSocket Connection

```javascript
const conversationId = 'your-conversation-id';
const ws = new WebSocket(`ws://localhost:8000/ws/chat/${conversationId}/`);

ws.onopen = () => {
    console.log('Connected to chat');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleIncomingMessage(data);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = () => {
    console.log('Disconnected from chat');
};
```

### 2. Send Messages

```javascript
function sendMessage(content) {
    ws.send(JSON.stringify({
        type: 'send_message',
        content: content,
        message_type: 'text'
    }));
}
```

### 3. Handle Typing Indicators

```javascript
let typingTimer;

function handleTyping() {
    ws.send(JSON.stringify({
        type: 'typing',
        is_typing: true
    }));
    
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => {
        ws.send(JSON.stringify({
            type: 'typing',
            is_typing: false
        }));
    }, 3000);
}
```

### 4. Mark Messages as Read

```javascript
function markMessagesRead(messageIds) {
    ws.send(JSON.stringify({
        type: 'mark_read',
        message_ids: messageIds
    }));
}
```

## Security Considerations

1. **Authentication**: All WebSocket connections require authenticated users
2. **Authorization**: Users can only access conversations they're participants in
3. **Permissions**: Role-based permissions for actions (admin, moderator, participant)
4. **Input Validation**: All inputs are validated and sanitized
5. **File Upload**: File size and type restrictions are enforced

## Performance Optimizations

1. **Database Queries**: Optimized with select_related and prefetch_related
2. **Pagination**: API responses are paginated
3. **Caching**: Consider implementing Redis caching for frequently accessed data
4. **WebSocket Groups**: Efficient message broadcasting using channel groups

## Testing

Run the chat system tests:

```bash
python manage.py test apps.Chat
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Ensure Django Channels is properly configured
   - Check ASGI server is running
   - Verify WebSocket URL is correct

2. **Messages Not Delivering**
   - Check user is authenticated
   - Verify user is participant in conversation
   - Check channel layer configuration

3. **Notifications Not Working**
   - Ensure notification app signals are connected
   - Check user notification preferences
   - Verify email/push notification services

### Debug Mode

Enable debug logging for chat system:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps.Chat': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Future Enhancements

1. **Voice/Video Calls**: WebRTC integration for real-time calls
2. **Message Translation**: Auto-translate messages between languages
3. **Advanced Search**: Full-text search across conversations
4. **Message Encryption**: End-to-end encryption for sensitive conversations
5. **Bot Integration**: Chatbot support for automated responses
6. **Analytics**: Chat usage statistics and insights