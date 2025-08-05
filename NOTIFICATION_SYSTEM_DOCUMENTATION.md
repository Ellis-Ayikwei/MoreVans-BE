# MoreVans Notification System Documentation

## Overview

This document describes the comprehensive notification system implemented for the MoreVans platform. The system handles in-app notifications, email notifications, SMS (future), and push notifications (future) across various business events.

## 🎯 Features Implemented

### ✅ Core Components

1. **Enhanced Notification Model** - Extended with 25+ notification types covering all business events
2. **Notification Service** - Centralized service for creating and sending notifications
3. **Email Templates** - Beautiful HTML and text templates for all notification types
4. **Automatic Triggers** - Django signals for automatic notification sending
5. **User Preferences** - Configurable notification preferences per user
6. **Admin Interface** - Comprehensive admin panel for notification management
7. **Utility Functions** - Helper functions for formatting and processing
8. **Management Commands** - CLI tools for notification management

### 📧 Notification Types Supported

#### Booking/Request Related
- `booking_created` - When a new booking is created
- `booking_confirmed` - When booking is confirmed by provider
- `booking_cancelled` - When booking is cancelled
- `request_update` - General request status updates

#### Provider/Job Related
- `provider_accepted` - Provider accepts a job
- `provider_assigned` - Provider assigned to job
- `job_started` - Job has started
- `job_in_transit` - Items are in transit
- `job_completed` - Job completed successfully
- `job_cancelled` - Job was cancelled

#### Account/Verification Related
- `account_verified` - User account verified
- `provider_verified` - Provider account verified
- `account_suspended` - Account suspended
- `account_reactivated` - Account reactivated

#### Payment Related
- `payment_pending` - Payment is pending
- `payment_confirmed` - Payment successful
- `payment_failed` - Payment failed
- `payment_refunded` - Payment refunded
- `deposit_received` - Deposit received

#### Bidding Related
- `bid_received` - New bid on job
- `bid_accepted` - Bid was accepted
- `bid_rejected` - Bid was rejected
- `bid_counter_offer` - Counter offer made

#### Communication Related
- `message_received` - New message received
- `support_ticket_created` - Support ticket created
- `support_ticket_updated` - Support ticket updated

#### Rating/Review Related
- `review_received` - New review received
- `rating_reminder` - Reminder to rate experience

#### System/Admin Related
- `system_maintenance` - System maintenance notices
- `policy_update` - Policy updates
- `feature_announcement` - New feature announcements
- `account_warning` - Account warnings

## 🚀 Quick Start

### 1. Basic Usage

```python
from apps.Notification.services import NotificationService

# Create a simple notification
notification = NotificationService.create_notification(
    user=user,
    notification_type='payment_confirmed',
    related_object_type='payment',
    related_object_id=payment.id,
    payment=payment,
    amount=payment.amount
)
```

### 2. Using Convenience Methods

```python
# Notify booking created
NotificationService.notify_booking_created(user=user, request_obj=request)

# Notify payment confirmed
NotificationService.notify_payment_confirmed(user=user, payment_obj=payment)

# Notify provider verified
NotificationService.notify_provider_verified(user=user, provider_obj=provider)

# Notify bid received
NotificationService.notify_bid_received(user=user, bid_obj=bid)
```

### 3. Custom Notifications

```python
# Custom notification with all options
notification = NotificationService.create_notification(
    user=user,
    notification_type='system',
    title='Custom Title',
    message='Custom message content',
    data={'custom_data': 'value'},
    priority='high',
    channels=['in_app', 'email', 'push'],
    action_url='/dashboard',
    action_text='View Dashboard',
    expires_at=timezone.now() + timedelta(days=7)
)
```

## 📋 File Structure

```
apps/Notification/
├── models.py              # Enhanced notification model
├── services.py            # NotificationService and preferences
├── views.py               # API endpoints
├── serializer.py          # API serializers
├── admin.py               # Django admin interface
├── signals.py             # Automatic notification triggers
├── utils.py               # Utility functions
├── urls.py                # URL configuration
├── apps.py                # App configuration
├── management/commands/
│   └── send_notifications.py  # Management commands
└── migrations/
    └── 0003_enhanced_notifications.py

templates/emails/notifications/
├── booking_created.html          # Booking created email template
├── booking_created.txt
├── booking_confirmed.html        # Booking confirmed email template
├── booking_confirmed.txt
├── payment_confirmed.html        # Payment confirmed email template
├── payment_confirmed.txt
├── provider_verified.html        # Provider verification email template
├── provider_verified.txt
├── bid_received.html             # Bid received email template
├── bid_received.txt
├── generic_notification.html     # Fallback template
└── generic_notification.txt
```

## 🔧 API Endpoints

The notification system provides comprehensive REST API endpoints:

### Core Endpoints
- `GET /api/notifications/` - List user's notifications
- `GET /api/notifications/{id}/` - Get specific notification
- `POST /api/notifications/{id}/mark_as_read/` - Mark as read
- `POST /api/notifications/mark_all_as_read/` - Mark all as read

### Utility Endpoints
- `GET /api/notifications/unread_count/` - Get unread count
- `GET /api/notifications/summary/` - Get notification summary
- `DELETE /api/notifications/clear_read/` - Delete read notifications

### Preferences
- `GET /api/notifications/preferences/` - Get user preferences
- `POST /api/notifications/preferences/` - Update preferences

### Admin/Testing
- `POST /api/notifications/test_notification/` - Send test notification (staff only)

### Query Parameters
- `?type=booking_created` - Filter by notification type
- `?read=false` - Filter by read status
- `?priority=high` - Filter by priority
- `?unread_only=true` - Show only unread
- `?urgent_only=true` - Show only urgent

## 🎨 Email Templates

### Template Features
- **Responsive Design** - Works on all devices
- **Beautiful Styling** - Professional gradient designs
- **Dynamic Content** - Context-aware content
- **Action Buttons** - Call-to-action buttons
- **Branding** - Consistent MoreVans branding
- **Fallback Support** - Text versions for all templates

### Template Context Variables
All templates have access to:
- `user` - User object
- `user_name` - User's display name
- `notification` - Notification object
- `title` - Notification title
- `message` - Notification message
- `action_url` - Action URL
- `action_text` - Action button text
- `app_name` - Application name
- `current_year` - Current year
- `notification_data` - Additional data

Plus type-specific variables like `request`, `payment`, `provider`, `bid`, etc.

## 🔔 Automatic Triggers

The system automatically sends notifications for:

### Request/Booking Events
- New request created → `booking_created`
- Request status changes → Various types
- Request cancelled → `booking_cancelled`

### Payment Events
- Payment completed → `payment_confirmed`
- Payment failed → `payment_failed`

### Provider Events
- Provider verified → `provider_verified`

### Bidding Events
- New bid placed → `bid_received`
- Bid accepted/rejected → `bid_accepted`/`bid_rejected`

### Job Events
- Job status changes → Various job status types

### Message Events
- New message sent → `message_received`

### User Events
- Account activated → `account_verified`

## ⚙️ Configuration

### Notification Preferences
Users can control:
- Email notifications on/off
- SMS notifications on/off (future)
- Push notifications on/off (future)
- Notification type categories:
  - Booking updates
  - Payment updates
  - Job updates
  - Messages
  - Bids
  - Marketing

### Priority Levels
- `low` - Non-urgent informational notifications
- `normal` - Standard notifications (default)
- `high` - Important notifications
- `urgent` - Critical notifications requiring immediate attention

### Delivery Channels
- `in_app` - In-application notifications (always enabled)
- `email` - Email notifications
- `sms` - SMS notifications (future implementation)
- `push` - Push notifications (future implementation)

## 🛠️ Management Commands

### Send Scheduled Notifications
```bash
python manage.py send_notifications --send-scheduled
```

### Send Test Notification
```bash
python manage.py send_notifications --test-email user@example.com
```

### Cleanup Old Notifications
```bash
python manage.py send_notifications --cleanup-old 30
```

### Show Statistics
```bash
python manage.py send_notifications --stats
```

### Send Maintenance Notification
```bash
python manage.py send_notifications --maintenance --maintenance-date "2024-01-15 02:00" --maintenance-duration "2 hours"
```

## 📊 Admin Interface

The Django admin provides:

### Dashboard Features
- Notification statistics
- Recent activity
- Delivery status overview
- Error tracking

### Management Actions
- Mark as read/unread
- Resend notifications
- Delete read notifications
- Send test notifications

### Filtering & Search
- Filter by type, priority, status
- Search by user, title, content
- Date-based filtering
- Advanced queries

## 🔍 Utility Functions

### Template Rendering
```python
from apps.Notification.utils import NotificationTemplateRenderer

rendered = NotificationTemplateRenderer.render_notification_email(notification)
# Returns: {'html': '...', 'text': '...', 'subject': '...'}
```

### Content Formatting
```python
from apps.Notification.utils import NotificationFormatter

title = NotificationFormatter.format_notification_title('payment_confirmed', context)
message = NotificationFormatter.format_notification_message('payment_confirmed', context)
```

### Batch Processing
```python
from apps.Notification.utils import NotificationBatchProcessor

# Send bulk notifications
results = NotificationBatchProcessor.send_bulk_notifications(notification_data)

# Cleanup old notifications
deleted_count = NotificationBatchProcessor.cleanup_old_notifications(days_old=30)
```

## 🚨 Error Handling

The system includes comprehensive error handling:
- Failed email sends are logged
- Retry mechanisms for transient failures
- Graceful degradation when templates are missing
- Detailed error tracking in admin interface

## 🔮 Future Enhancements

### Planned Features
1. **SMS Integration** - Twilio integration for SMS notifications
2. **Push Notifications** - Firebase integration for mobile push notifications
3. **Notification Scheduling** - Advanced scheduling capabilities
4. **A/B Testing** - Template and content testing
5. **Analytics** - Notification engagement analytics
6. **Webhooks** - External webhook integrations
7. **Rate Limiting** - Advanced rate limiting per user
8. **Internationalization** - Multi-language support

## 📝 Development Notes

### Adding New Notification Types
1. Add to `NOTIFICATION_TYPES` in `models.py`
2. Create templates in `templates/emails/notifications/`
3. Add to `NOTIFICATION_TEMPLATES` in `services.py`
4. Create convenience method in `NotificationService`
5. Add signal handlers if needed
6. Update documentation

### Template Development
- Follow existing template structure
- Use consistent styling variables
- Include both HTML and text versions
- Test with various content lengths
- Ensure mobile responsiveness

### Testing
- Test all notification types
- Verify email templates render correctly
- Test user preferences
- Verify signal triggers
- Test error handling

## 🤝 Integration Examples

### In Views
```python
from apps.Notification.services import NotificationService

def create_booking(request):
    # ... create booking logic ...
    
    # Send notification
    NotificationService.notify_booking_created(
        user=request.user,
        request_obj=booking_request
    )
```

### In Signals
```python
@receiver(post_save, sender=Payment)
def handle_payment_completion(sender, instance, created, **kwargs):
    if instance.status == 'completed':
        NotificationService.notify_payment_confirmed(
            user=instance.request.user,
            payment_obj=instance
        )
```

### Frontend Integration
```javascript
// Get unread count
fetch('/api/notifications/unread_count/')
  .then(response => response.json())
  .then(data => {
    document.getElementById('notification-badge').textContent = data.unread_count;
  });

// Mark notification as read
fetch('/api/notifications/123/mark_as_read/', {
  method: 'POST',
  headers: {
    'X-CSRFToken': getCookie('csrftoken'),
  }
});
```

## 📞 Support

For questions or issues with the notification system:
1. Check this documentation
2. Review the admin interface for errors
3. Check Django logs for detailed error messages
4. Use management commands for testing
5. Contact the development team

---

**Last Updated**: January 2025  
**Version**: 1.0  
**Maintainer**: MoreVans Development Team