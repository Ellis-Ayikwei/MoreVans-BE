from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import ContractAgreement
from .serializer import ContractAgreementSerializer

class ContractAgreementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing ContractAgreement instances.
    """
    queryset = ContractAgreement.objects.all()
    serializer_class = ContractAgreementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Optionally restricts the returned contracts to those related 
        to specific requests or bids.
        """
        queryset = ContractAgreement.objects.all()
        request_id = self.request.query_params.get('request', None)
        bid_id = self.request.query_params.get('bid', None)
        
        if request_id:
            queryset = queryset.filter(logistics_request_id=request_id)
        if bid_id:
            queryset = queryset.filter(selected_bid_id=bid_id)
            
        return queryset
