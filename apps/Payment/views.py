from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import PaymentMethod, Payment
from .serializer import PaymentMethodSerializer, PaymentSerializer

class PaymentMethodViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing PaymentMethod instances.
    """
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = PaymentMethod.objects.all()
        user_id = self.request.query_params.get('user', None)
        payment_type = self.request.query_params.get('type', None)
        is_active = self.request.query_params.get('active', None)
        is_default = self.request.query_params.get('default', None)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if payment_type:
            queryset = queryset.filter(payment_type=payment_type)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        if is_default is not None:
            is_default_bool = is_default.lower() == 'true'
            queryset = queryset.filter(is_default=is_default_bool)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def set_as_default(self, request, pk=None):
        """
        Set a payment method as the default for a user.
        """
        payment_method = self.get_object()
        if payment_method.user != request.user:
            return Response(
                {"detail": "You can only modify your own payment methods."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # First, reset all payment methods for this user
        PaymentMethod.objects.filter(user=payment_method.user, is_default=True).update(is_default=False)
        
        # Set this one as default
        payment_method.is_default = True
        payment_method.save()
        
        serializer = self.get_serializer(payment_method)
        return Response(serializer.data)

class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Payment instances.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Payment.objects.all()
        request_id = self.request.query_params.get('request', None)
        payment_method_id = self.request.query_params.get('payment_method', None)
        status_param = self.request.query_params.get('status', None)
        
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        if payment_method_id:
            queryset = queryset.filter(payment_method_id=payment_method_id)
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        return queryset
