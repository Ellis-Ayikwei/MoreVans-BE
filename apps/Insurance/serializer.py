from rest_framework import serializers
from .models import InsuranceProfile

class InsuranceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceProfile
        fields = ['id', 'user', 'coverage_level', 'max_coverage_amount', 
                 'policy_number', 'insurance_provider', 'valid_from', 
                 'valid_until', 'additional_coverages']