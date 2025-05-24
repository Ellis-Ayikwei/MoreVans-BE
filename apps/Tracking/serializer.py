from rest_framework import serializers
from .models import TrackingUpdate

class TrackingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingUpdate
        fields = ['id', 'request', 'update_type', 'location', 'status_message',
                 'created_at', 'estimated_delay']