from django.shortcuts import render
from rest_framework import viewsets, permissions

from .models import RequestItem
from .serializers import RequestItemSerializer


class RequestItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing RequestItem instances.
    """

    queryset = RequestItem.objects.all()
    serializer_class = RequestItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = RequestItem.objects.all()
        request_id = self.request.query_params.get("request", None)
        category_id = self.request.query_params.get("category", None)

        if request_id:
            queryset = queryset.filter(request_id=request_id)
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset
