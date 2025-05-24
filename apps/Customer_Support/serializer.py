from rest_framework import serializers
from .models import Dispute

class DisputeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispute
        fields = ['id', 'request', 'raised_by', 'dispute_type', 'description', 
                 'evidence', 'status', 'created_at', 'resolved_at', 
                 'resolution_notes', 'compensation_amount']