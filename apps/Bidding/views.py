from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Bid
from .serializer import BidSerializer

class BidViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Bid instances.
    """
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_provider:
            return Bid.objects.filter(provider=user.provider)
        else:
            return Bid.objects.filter(job__request__customer=user)

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user.provider)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        bid = self.get_object()
        job = bid.job

        if job.request.customer != request.user:
            return Response(
                {'error': 'Only the job owner can accept bids'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update job and bid status
        job.status = 'assigned'
        job.save()
        
        bid.status = 'accepted'
        bid.save()

        # Reject all other bids
        Bid.objects.filter(
            job=job,
            status='pending'
        ).exclude(id=bid.id).update(status='rejected')

        return Response(
            {'message': 'Bid accepted successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        bid = self.get_object()
        job = bid.job

        if job.request.customer != request.user:
            return Response(
                {'error': 'Only the job owner can reject bids'},
                status=status.HTTP_403_FORBIDDEN
            )

        bid.status = 'rejected'
        bid.save()

        return Response(
            {'message': 'Bid rejected successfully'},
            status=status.HTTP_200_OK
        )
