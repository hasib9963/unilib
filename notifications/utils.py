# your_app/utils.py
from notifications.models import Notification
from django.urls import reverse
from books.models import Book  

def notify(user, message, type='GEN', url=None):
    Notification.objects.create(
        user=user,
        message=message,
        notification_type=type,
        related_url=url
    )

# context_processors.py (create if doesn't exist)
from notifications.models import Notification

def notification_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_notification_count': count}
    return {}
