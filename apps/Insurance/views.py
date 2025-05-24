from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import InsuranceProfile
from .serializer import InsuranceProfileSerializer

class InsuranceProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing InsuranceProfile instances.
    """
    queryset = InsuranceProfile.objects.all()
    serializer_class = InsuranceProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = InsuranceProfile.objects.all()
        user_id = self.request.query_params.get('user', None)
        policy_number = self.request.query_params.get('policy_number', None)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if policy_number:
            queryset = queryset.filter(policy_number=policy_number)
            
        return queryset
