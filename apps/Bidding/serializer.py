from rest_framework import serializers
from .models import Bid


class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bid
        fields = ['id', 'request', 'driver', 'amount', 'created_at']
