from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'request', 'sender', 'receiver', 'content', 'read', 'read_at', 'created_at']