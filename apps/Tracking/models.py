from django.db import models



class TrackingUpdate(models.Model):
    UPDATE_TYPES = [
        ('location', 'Location Update'),
        ('status', 'Status Update'),
        ('delay', 'Delay Notification'),
        ('completion', 'Completion Update'),
    ]

    request = models.ForeignKey("Request.Request", on_delete=models.CASCADE, related_name='tracking_updates')
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPES)
    location = models.JSONField(null=True)  # lat/long
    status_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    estimated_delay = models.DurationField(null=True)
    
    class Meta:
        db_table = 'tracking_update'
        managed = True
