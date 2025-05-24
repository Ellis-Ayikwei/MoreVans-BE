from django.db import models
from apps.Basemodel.models import Basemodel
from apps.User.models import User

class Notification(Basemodel):
    NOTIFICATION_TYPES = [
        ('request_update', 'Request Update'),
        ('payment', 'Payment Notification'),
        ('bid', 'Bid Notification'),
        ('message', 'New Message'),
        ('system', 'System Notification'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(null=True)  # Additional data
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'notification'
        managed = True
        ordering = ['-created_at']

    def mark_as_read(self):
        self.read = True
        self.save()
