from rest_framework import serializers
from .models import ServiceReview

class ServiceReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceReview
        fields = ['id', 'contract', 'overall_rating', 'punctuality_rating', 
                 'service_quality_rating', 'review_text', 'created_at']