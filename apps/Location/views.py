from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Location
from .serializer import LocationSerializer

class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Location instances.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Location.objects.all()
        postcode = self.request.query_params.get('postcode', None)
        contact_name = self.request.query_params.get('contact_name', None)
        
        if postcode:
            queryset = queryset.filter(postcode__icontains=postcode)
        if contact_name:
            queryset = queryset.filter(contact_name__icontains=contact_name)
            
        return queryset
