# Notifications App

The notifications app provides a comprehensive notification system for the UniLib library management system, supporting both in-app notifications and email notifications.

## Features

### In-App Notifications
- Real-time notification display
- Notification history tracking
- Mark as read/unread functionality
- Notification type categorization
- URL linking for quick navigation
- Notification counter in navigation

### Email Notifications
- Overdue book alerts
- Fine payment confirmations
- Reservation availability alerts
- System announcements
- HTML email template support

### Notification Types
- **BORROW**: Book borrowing confirmations
- **RETURN**: Book return confirmations
- **FINE**: Fine creation and payment notifications
- **RESERVATION**: Reservation status updates
- **SYSTEM**: System-wide announcements

## Models

### Notification
Main notification model with the following fields:
- `recipient`: Foreign key to User (notification receiver)
- `message`: Notification message text
- `notification_type`: Type of notification (BORROW, RETURN, FINE, RESERVATION, SYSTEM)
- `is_read`: Read status flag
- `created_at`: Notification timestamp
- `url`: Optional URL for notification action
- `email_sent`: Track if email was sent

## Key Functions

### Notification Utility Functions
Located in `notifications/utils.py`:

- `notify(user, message, type, url)`: Create and send notification
- `notification_count(request)`: Context processor for notification counter
- `send_email_notification(user, subject, message, html_content)`: Send email notification

## Views

### Notification Views
- `notification_list`: List all notifications for current user
- `notification_detail`: View notification details
- `mark_as_read`: Mark notification as read
- `mark_all_as_read`: Mark all notifications as read
- `delete_notification`: Delete a notification

## URL Patterns

```
/notifications/
    ''                    # Notification list
    <int:pk>/            # Notification detail
    <int:pk>/read/       # Mark as read
    read-all/            # Mark all as read
    <int:pk>/delete/     # Delete notification
```

## Templates

- `notifications/notification_list.html`: Notification listing page
- `notifications/notification_detail.html`: Notification details
- `notifications/notification_item.html`: Single notification item (for inclusion)
- `emails/overdue_book.html`: Email template for overdue books
- `emails/base.html`: Base email template

## Context Processor

### notification_count
Context processor that adds notification count to all templates:
- Automatically included in settings.py
- Provides `notification_count` variable in templates
- Shows count of unread notifications
- Used in navigation bar for notification badge

## Usage Examples

### Creating a Notification
```python
from notifications.utils import notify

# Simple notification
notify(
    user=user,
    message='Your book is due tomorrow',
    type='BORROW',
    url='/books/1/'
)

# Notification with custom type
notify(
    user=user,
    message='A fine of $50 has been applied',
    type='FINE',
    url='/fines/1/'
)
```

### Sending Email Notifications
```python
from notifications.utils import send_email_notification
from django.template.loader import render_to_string

subject = 'UniLib - Book Due Reminder'
message = 'Your book is due tomorrow'
html_content = render_to_string('emails/overdue_book.html', {
    'user': user,
    'book': book,
    'due_date': due_date
})

send_email_notification(
    user=user,
    subject=subject,
    message=message,
    html_content=html_content
)
```

### Checking Notification Count in Templates
```html
{% if notification_count > 0 %}
    <span class="badge">{{ notification_count }}</span>
{% endif %}
```

### Listing Notifications
```python
from notifications.models import Notification

# Get unread notifications
unread_notifications = Notification.objects.filter(
    recipient=request.user,
    is_read=False
).order_by('-created_at')

# Get all notifications
all_notifications = Notification.objects.filter(
    recipient=request.user
).order_by('-created_at')
```

## Notification Workflow

### Creating Notifications
1. Event occurs (e.g., book becomes overdue)
2. System calls `notify()` function
3. Notification is created in database
4. Email notification is sent (if applicable)
5. Real-time counter updates

### User Notification Flow
1. User sees notification counter in navigation
2. User clicks on notifications
3. Notification list is displayed
4. User can click individual notifications
5. User is redirected to relevant URL
6. Notification is marked as read

### Email Notification Flow
1. Event triggers email notification
2. System renders email template
3. Email is sent via SMTP
4. Delivery status is tracked
5. In-app notification is also created

## Email Templates

### Overdue Book Email
Includes:
- User name
- Book details
- Due date
- Days overdue
- Fine amount
- Link to book details

### Email Template Structure
- Base template with styling
- Responsive design
- Professional formatting
- Call-to-action links
- Plain text fallback

## Integration with Other Apps

- **Accounts**: User notifications for account events
- **Books**: Book availability notifications
- **Transactions**: Borrow, return, fine, and reservation notifications
- **Dashboard**: Notification display in dashboard

## Configuration

### Email Settings
Configured in `UniLib/settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = env('EMAIL')
EMAIL_HOST_PASSWORD = env('EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = f"UniLib <{env('EMAIL')}>"
```

### Context Processor
Registered in settings.py:
```python
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                'notifications.utils.notification_count',
            ],
        },
    },
]
```

## Security and Privacy

- Notifications are user-specific
- Users can only see their own notifications
- Email addresses are not exposed to other users
- Sensitive information is protected
- Email content is sanitized

## Performance Considerations

- Notifications are indexed by recipient and created_at
- Email sending is asynchronous where possible
- Old notifications can be archived (future feature)
- Database queries optimized with proper indexing

## Future Enhancements

- Push notifications for mobile devices
- SMS notifications for critical alerts
- Notification preferences per user
- Notification grouping
- Scheduled notifications
- Notification templates management
- Email digest options (daily/weekly)
- Notification analytics and tracking
- WebSocket support for real-time updates
- Rich notification content (images, attachments)