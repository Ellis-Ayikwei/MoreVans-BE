from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from decimal import Decimal
from django.conf import settings
from apps.pricing.services import PricingService


def send_booking_confirmation_email(request_data):
    """
    Send a booking confirmation email to the customer
    """
    try:
        # Prepare email data
        subject = f"Booking Confirmation - {request_data.tracking_number}"

        # Prepare context for email template
        context = {
            "tracking_number": request_data.tracking_number,
            "customer_name": request_data.contact_name,
            "price": request_data.price,
            "pickup_location": (
                request_data.journey_stops.filter(type="pickup").first().location
                if request_data.journey_stops.filter(type="pickup").exists()
                else None
            ),
            "dropoff_location": (
                request_data.journey_stops.filter(type="dropoff").first().location
                if request_data.journey_stops.filter(type="dropoff").exists()
                else None
            ),
            "staff_count": request_data.staff_required,
            "contact_email": request_data.contact_email,
            "contact_phone": request_data.contact_phone,
        }

        # Render email template
        html_message = render_to_string("emails/booking_confirmation.html", context)
        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request_data.contact_email],
            html_message=html_message,
            fail_silently=False,
        )

        return True
    except Exception as e:
        print(f"Error sending confirmation email: {str(e)}")
        return False


class RequestPricingService:
    """
    Service for calculating pricing for requests, including base job price from final price
    """

    @staticmethod
    def calculate_base_job_price_from_final_price(request_obj, final_price=None):
        """
        Calculate the base job price (what providers get paid) from the final customer price
        while ensuring profitability for both platform and provider.
        """
        if final_price is None:
            final_price = request_obj.final_price or request_obj.base_price or 0

        # Convert to Decimal for precise calculations
        final_price = Decimal(str(final_price))

        if final_price == 0:
            return Decimal("0")

        active_config = PricingService.get_active_configuration()

        # Fallback logic - ensure providers get at least 80% of the final price
        default_platform_fee_percentage = Decimal("10.0")  # Reduced platform fee to 10%
        default_min_profit_margin = Decimal("0.05")  # 5% minimum for platform
        default_provider_margin = Decimal("0.15")  # 15% margin for providers

        if not active_config:
            # Provider gets 90% (100% - 10% platform fee)
            return final_price * Decimal("0.90")

        # Calculate job complexity score (0.0 to 1.0)
        complexity_score = RequestPricingService._calculate_job_complexity(request_obj)

        # Calculate total deduction percentage based on complexity
        total_deduction_percentage = (
            RequestPricingService._calculate_deduction_percentage(
                complexity_score, active_config
            )
        )

        platform_fee_percentage = Decimal(
            str(
                active_config.platform_fee_percentage or default_platform_fee_percentage
            )
        )
        raw_platform_profit = final_price * (platform_fee_percentage / Decimal("100"))

        # Try to calculate what’s left after profit and costs
        # Calculate provider percentage (100% - total deductions)
        provider_percentage = Decimal("100") - total_deduction_percentage

        # Calculate base job price
        base_job_price = final_price * (provider_percentage / Decimal("100"))

        # Ensure minimum provider percentage (never below 70%)
        min_provider_percentage = Decimal("70")
        if provider_percentage < min_provider_percentage:
            provider_percentage = min_provider_percentage
            base_job_price = final_price * (provider_percentage / Decimal("100"))

        # Ensure base job price doesn't fall below platform minimum
        min_job_price = Decimal(str(active_config.base_price or "30.00"))
        base_job_price = max(base_job_price, min_job_price)

        return round(base_job_price, 2)

    @staticmethod
    def _calculate_detailed_costs(request_obj, final_price, active_config):
        """
        Calculate detailed costs based on request characteristics

        Returns a dictionary of cost components:
        - staff_costs: Based on number of staff required
        - route_costs: Based on distance and route complexity
        - tax_costs: VAT and other taxes
        - value_costs: Percentage of item value or constant
        - time_costs: Based on time factors from pricing config
        - special_handling_costs: For fragile/special items
        - fuel_costs: Based on distance and fuel rates
        - insurance_costs: If insurance is required
        """
        costs = {
            "staff_costs": Decimal("0"),
            "route_costs": Decimal("0"),
            "tax_costs": Decimal("0"),
            "value_costs": Decimal("0"),
            "time_costs": Decimal("0"),
            "special_handling_costs": Decimal("0"),
            "fuel_costs": Decimal("0"),
            "insurance_costs": Decimal("0"),
        }

        # 1. STAFF COSTS - Based on number of staff required
        staff_required = request_obj.staff_required or 1
        hourly_rate = Decimal("15.00")  # £15 per hour per staff member (more realistic)
        estimated_hours = Decimal("2.00")  # Default 2 hours (more realistic)

        # Get time factors from pricing config if available
        time_factors = active_config.time_factors.filter(is_active=True).first()
        if time_factors:
            # Adjust based on time of day, weekend, etc.
            if hasattr(time_factors, "peak_hour_multiplier"):
                hourly_rate *= time_factors.peak_hour_multiplier

        costs["staff_costs"] = (
            Decimal(str(staff_required)) * hourly_rate * estimated_hours
        )

        # 2. ROUTE COSTS - Based on distance and complexity
        if request_obj.estimated_distance:
            distance_km = Decimal(str(request_obj.estimated_distance))

            # Base rate per km
            base_rate_per_km = Decimal("0.25")  # £0.25 per km (more realistic)

            # Get distance factors from pricing config
            distance_factors = active_config.distance_factors.filter(
                is_active=True
            ).first()
            if distance_factors:
                base_rate_per_km = distance_factors.base_rate_per_km

            # Calculate route complexity multiplier
            complexity_multiplier = Decimal("1.0")
            if request_obj.stops.count() > 2:
                # Multiple stops increase complexity
                complexity_multiplier = Decimal("1.2")

            costs["route_costs"] = (
                distance_km * base_rate_per_km * complexity_multiplier
            )

            # 3. FUEL COSTS - Based on distance
            fuel_rate_per_km = Decimal("0.15")  # £0.15 per km for fuel
            costs["fuel_costs"] = distance_km * fuel_rate_per_km

        # 4. TAX COSTS - VAT and other taxes (minimal to not hurt providers)
        vat_rate = Decimal("0.02")  # 2% tax rate (very minimal)
        costs["tax_costs"] = final_price * vat_rate

        # 5. VALUE COSTS - Percentage of item value or constant (minimal)
        if request_obj.insurance_value:
            # Use 1% of insured value (reduced)
            value_percentage = Decimal("0.01")
            costs["value_costs"] = (
                Decimal(str(request_obj.insurance_value)) * value_percentage
            )
        else:
            # Use constant value cost (reduced)
            costs["value_costs"] = Decimal("20.00")  # £20 constant value cost

        # 6. TIME COSTS - Based on time factors from pricing config
        time_factors = active_config.time_factors.filter(is_active=True).first()
        if time_factors:
            time_multiplier = Decimal("1.0")

            # Check if it's weekend (you'd need to implement this logic)
            # For now, use base multiplier
            if hasattr(time_factors, "weekend_multiplier"):
                time_multiplier = time_factors.weekend_multiplier

            costs["time_costs"] = final_price * (time_multiplier - Decimal("1.0"))

        # 7. SPECIAL HANDLING COSTS - For fragile/special items (reduced)
        if request_obj.requires_special_handling:
            special_handling_rate = Decimal(
                "25.00"
            )  # £25 for special handling (reduced)

            # Get special requirements factors from pricing config
            special_factors = active_config.special_requirement_factors.filter(
                is_active=True
            ).first()
            if special_factors:
                special_handling_rate = special_factors.special_equipment_rate

            costs["special_handling_costs"] = special_handling_rate

        # 8. INSURANCE COSTS - If insurance is required (minimal)
        if request_obj.insurance_required:
            insurance_value = request_obj.insurance_value or final_price
            insurance_rate = Decimal("0.01")  # 1% of insured value (reduced)

            # Get insurance factors from pricing config
            insurance_factors = active_config.insurance_factors.filter(
                is_active=True
            ).first()
            if insurance_factors:
                insurance_rate = insurance_factors.value_percentage

            costs["insurance_costs"] = Decimal(str(insurance_value)) * insurance_rate

        return costs

    @staticmethod
    def _calculate_job_complexity(request_obj):
        """
        Calculate job complexity score from 0.0 (simple) to 1.0 (very complex)

        Complexity factors:
        - Distance (longer = more complex)
        - Number of stops (more stops = more complex)
        - Staff required (more staff = more complex)
        - Special handling requirements
        - Insurance value
        - Time sensitivity (instant jobs)
        - Weight/volume
        """
        complexity_score = Decimal("0.0")

        # Distance complexity (0-0.3 points)
        if request_obj.estimated_distance:
            distance = Decimal(str(request_obj.estimated_distance))
            if distance <= 10:
                complexity_score += Decimal("0.05")  # Short distance
            elif distance <= 50:
                complexity_score += Decimal("0.15")  # Medium distance
            else:
                complexity_score += Decimal("0.30")  # Long distance

        # Number of stops complexity (0-0.2 points)
        stops_count = request_obj.stops.count() if hasattr(request_obj, "stops") else 1
        if stops_count <= 2:
            complexity_score += Decimal("0.05")  # Simple pickup/dropoff
        elif stops_count <= 4:
            complexity_score += Decimal("0.10")  # Multiple stops
        else:
            complexity_score += Decimal("0.20")  # Many stops

        # Staff requirement complexity (0-0.2 points)
        staff_required = request_obj.staff_required or 1
        if staff_required == 1:
            complexity_score += Decimal("0.05")  # Single person job
        elif staff_required <= 3:
            complexity_score += Decimal("0.10")  # Small team
        else:
            complexity_score += Decimal("0.20")  # Large team

        # Special handling complexity (0-0.15 points)
        if request_obj.requires_special_handling:
            complexity_score += Decimal("0.15")

        # Insurance/value complexity (0-0.1 points)
        if request_obj.insurance_required and request_obj.insurance_value:
            value = Decimal(str(request_obj.insurance_value))
            if value > 5000:
                complexity_score += Decimal("0.10")  # High value items
            elif value > 1000:
                complexity_score += Decimal("0.05")  # Medium value items

        # Time sensitivity complexity (0-0.05 points)
        if request_obj.request_type == "instant":
            complexity_score += Decimal("0.05")

        # Cap complexity at 1.0
        return min(complexity_score, Decimal("1.0"))

    @staticmethod
    def _calculate_deduction_percentage(complexity_score, active_config):
        """
        Calculate total deduction percentage based on complexity score

        Returns percentage to deduct from final price for:
        - Platform fee
        - Taxes
        - Operational costs
        - Risk margin
        """
        # Base platform fee
        platform_fee = Decimal(str(active_config.platform_fee_percentage or 10))

        # Taxes (fixed 3%)
        tax_percentage = Decimal("3.0")

        # Operational costs based on complexity (2% - 8%)
        operational_percentage = Decimal("2.0") + (complexity_score * Decimal("6.0"))

        # Risk margin based on complexity (1% - 4%)
        risk_percentage = Decimal("1.0") + (complexity_score * Decimal("3.0"))

        # Total deductions
        total_deduction = (
            platform_fee + tax_percentage + operational_percentage + risk_percentage
        )

        # Cap total deductions at 30% (provider always gets at least 70%)
        return min(total_deduction, Decimal("30.0"))

    @staticmethod
    def get_pricing_breakdown(request_obj, final_price=None):
        """
        Get detailed pricing breakdown for transparency
        """
        if final_price is None:
            final_price = request_obj.final_price or request_obj.base_price or 0

        if final_price is None:
            final_price = request_obj.final_price or request_obj.base_price or 0

        # Convert to Decimal for precise calculations
        final_price = Decimal(str(final_price))

        # Calculate base job price
        base_job_price = (
            RequestPricingService.calculate_base_job_price_from_final_price(
                request_obj, final_price
            )
        )

        # Get active pricing configuration
        active_config = PricingService.get_active_configuration()

        # Calculate platform profit
        platform_fee_percentage = (
            Decimal(str(active_config.platform_fee_percentage or 15))
            if active_config
            else Decimal("15")
        )
        platform_profit = final_price * (platform_fee_percentage / Decimal("100"))

        # Get detailed cost breakdown
        cost_components = (
            RequestPricingService._calculate_detailed_costs(
                request_obj, final_price, active_config
            )
            if active_config
            else {}
        )

        total_costs = sum(cost_components.values()) if cost_components else Decimal("0")

        return {
            "final_price": final_price,
            "base_job_price": base_job_price,
            "platform_profit": platform_profit,
            "platform_fee_percentage": platform_fee_percentage,
            "total_costs": total_costs,
            "cost_breakdown": cost_components,
            "provider_percentage": (
                (base_job_price / final_price * 100) if final_price > 0 else 0
            ),
            "platform_percentage": (
                (platform_profit / final_price * 100) if final_price > 0 else 0
            ),
            "costs_percentage": (
                (total_costs / final_price * 100) if final_price > 0 else 0
            ),
        }
