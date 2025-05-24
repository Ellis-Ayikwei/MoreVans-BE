from rest_framework import serializers
from .models import ContractAgreement

class ContractAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractAgreement
        fields = ['id', 'logistics_request', 'selected_bid', 'insurance_coverage', 
                 'cancellation_policy', 'customer_signed', 'provider_signed', 
                 'status', 'created_at', 'agreement_start_date', 'agreement_end_date']