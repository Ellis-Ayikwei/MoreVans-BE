from django.db import models
from apps.Basemodel.models import Basemodel
from apps.Request.models import Request
from apps.User.models import User

class PaymentMethod(Basemodel):
    PAYMENT_TYPES = [
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Transfer'),
        ('wallet', 'Digital Wallet'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    is_default = models.BooleanField(default=False)
    last_used = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
    
    # For cards
    card_last_four = models.CharField(max_length=4, null=True, blank=True)
    card_brand = models.CharField(max_length=20, null=True, blank=True)
    card_expiry = models.DateField(null=True, blank=True)
    
    # For bank accounts
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    account_last_four = models.CharField(max_length=4, null=True, blank=True)
    
    class Meta:
        db_table = 'payment_method'
        managed = True

class Payment(Basemodel):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    transaction_id = models.CharField(max_length=100, unique=True)
    completed_at = models.DateTimeField(null=True)
    refund_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'payment'
        managed = True
