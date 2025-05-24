from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.gis.db import models as gis_models

class CustomerProfile(models.Model):
    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='customer_profile',
        limit_choices_to={'user_type': 'customer'}
    )
    
    # Enhanced fields for logistics
    default_pickup_address = models.ForeignKey(
        'Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_pickup'
    )
    default_delivery_address = models.ForeignKey(
        'Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_delivery'
    )
    preferred_vehicle_types = models.JSONField(
        default=list,
        help_text=_("Preferred vehicle types for shipments")
    )
    fragile_items_handling = models.BooleanField(
        default=False,
        help_text=_("Requires special handling for fragile items")
    )
    insurance_preference = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text=_("Default insurance coverage amount")
    )
    
    loyalty_points = models.PositiveIntegerField(default=0)
    referral_code = models.CharField(max_length=20, unique=True, blank=True)
    communication_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Notification preferences settings"
    )
    marketing_opt_in = models.BooleanField(
        default=False,
        verbose_name="Marketing Communications"
    )

    # Logistics-specific methods
    def create_moving_request(self, request_data):
        """
        Create a new moving request
        {
            "pickup_address": Address,
            "delivery_address": Address,
            "items": [{"name": "Furniture", "volume": 3.5}],
            "preferred_date": datetime,
            "special_requirements": str
        }
        """
        from .models import MovingRequest
        return MovingRequest.objects.create(
            customer=self,
            pickup_location=request_data.get('pickup_address'),
            delivery_location=request_data.get('delivery_address'),
            items=request_data.get('items'),
            preferred_datetime=request_data.get('preferred_date'),
            special_requirements=request_data.get('special_requirements'),
            status='pending'
        )

    def get_active_quotes(self):
        """Get all active quotes for the customer"""
        return self.quotes.filter(status__in=['pending', 'negotiating'])

    def accept_quote(self, quote_id):
        """Accept a provider's quote"""
        quote = self.quotes.get(id=quote_id)
        if quote.status == 'accepted':
            raise ValueError("Quote already accepted")
        
        quote.status = 'accepted'
        quote.save()
        self._create_shipment_from_quote(quote)
        return quote

    def track_shipment(self, shipment_id):
        """Get real-time shipment tracking info"""
        shipment = self.shipments.get(id=shipment_id)
        return {
            'status': shipment.status,
            'current_location': shipment.current_location,
            'estimated_arrival': shipment.estimated_arrival,
            'driver_contact': shipment.driver_contact_info
        }

    def cancel_request(self, request_id):
        """Cancel a moving request"""
        request = self.moving_requests.get(id=request_id)
        if request.status not in ['pending', 'quoting']:
            raise PermissionError("Cannot cancel in-progress shipments")
        
        request.status = 'cancelled'
        request.save()
        return request

    def rate_shipment(self, shipment_id, rating, review):
        """Rate completed shipment"""
        shipment = self.shipments.get(id=shipment_id)
        if shipment.status != 'completed':
            raise ValueError("Can only rate completed shipments")
        
        return ShipmentRating.objects.create(
            shipment=shipment,
            rating=rating,
            review=review
        )

    # Loyalty program enhancements
    def calculate_loyalty_discount(self):
        """Calculate available discount based on loyalty points"""
        tiers = {
            1000: 0.10,   # 10% discount
            500: 0.05,    # 5% discount
            200: 0.02     # 2% discount
        }
        for points, discount in tiers.items():
            if self.loyalty_points >= points:
                return discount
        return 0.0

    def apply_referral_discount(self, referral_code):
        """Apply referral discount to account"""
        try:
            referral = CustomerProfile.objects.get(referral_code=referral_code)
            if referral != self:
                self.loyalty_points += 100  # Add referral bonus
                self.save()
                return True
        except CustomerProfile.DoesNotExist:
            return False

    # Payment integration
    def get_payment_history(self):
        """Retrieve complete payment history"""
        return self.payments.all().order_by('-payment_date')

    def make_payment(self, shipment_id, amount, payment_method):
        """Process payment for a shipment"""
        from payment.models import PaymentTransaction
        shipment = self.shipments.get(id=shipment_id)
        
        return PaymentTransaction.objects.create(
            customer=self,
            shipment=shipment,
            amount=amount,
            payment_method=payment_method,
            status='completed'
        )

    class Meta:
        verbose_name = _("Customer Profile")
        verbose_name_plural = _("Customer Profiles")

    def __str__(self):
        return f"{self.user.email} (Customer)"

# Related Models (in same file or separate)
class MovingRequest(models.Model):
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name='moving_requests'
    )
    pickup_location = gis_models.PointField()
    delivery_location = gis_models.PointField()
    items = models.JSONField()
    preferred_datetime = models.DateTimeField()
    special_requirements = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class Quote(models.Model):
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name='quotes'
    )
    provider = models.ForeignKey(
        'ServiceProviderProfile',
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    validity = models.DateTimeField()
    status = models.CharField(max_length=20, default='pending')

class Shipment(models.Model):
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name='shipments'
    )
    quote = models.OneToOneField(Quote, on_delete=models.PROTECT)
    current_location = gis_models.PointField()
    status = models.CharField(max_length=20, default='preparing')
    estimated_arrival = models.DateTimeField()
    driver_contact_info = models.JSONField()

class ShipmentRating(models.Model):
    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)