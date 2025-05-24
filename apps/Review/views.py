from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import ServiceReview
from .serializer import ServiceReviewSerializer

class ServiceReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing ServiceReview instances.
    """
    queryset = ServiceReview.objects.all()
    serializer_class = ServiceReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ServiceReview.objects.all()
        contract_id = self.request.query_params.get('contract', None)
        min_rating = self.request.query_params.get('min_rating', None)
        
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        if min_rating:
            queryset = queryset.filter(overall_rating__gte=min_rating)
            
        return queryset
