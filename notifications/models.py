# notifications/models.py
from django.urls import reverse
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User

class Notification(models.Model):
    class NotificationType(models.TextChoices):
        DUE_DATE = 'DUE', _('Due Date Reminder')
        RESERVATION = 'RES', _('Reservation Available')
        FINE = 'FINE', _('Fine Issued')
        GENERAL = 'GEN', _('General Notification')
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=103, choices=NotificationType.choices, default=NotificationType.GENERAL)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user}"

    class Meta:
        ordering = ['-created_at']