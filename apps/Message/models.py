from django.db import models

from apps.Basemodel.models import Basemodel
from apps.Request.models import Request
from apps.User.models import User

class Message(Basemodel):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True) 

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"
        
    class Meta:
        db_table = 'message'
        managed = True