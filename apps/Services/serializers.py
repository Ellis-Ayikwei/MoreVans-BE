from rest_framework import serializers
from .models import ServiceCategory


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ["id", "slug", "name", "description", "icon"]
        read_only_fields = ["id", "slug"]
