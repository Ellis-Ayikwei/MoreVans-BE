from decimal import Decimal
from enum import Enum


class JobComplexity(Enum):
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"
    PREMIUM = "premium"


class DriverCompensationService:
    """
    Balanced driver compensation calculator ensuring platform profitability

    Formula: Customer Price → Platform Commission → Driver Payment with Fair Margins
    """

    @staticmethod
    def calculate_driver_compensation(request_obj, customer_price):
        """
        Calculate driver compensation ensuring platform profitability

        Platform-First Approach:
        - Platform needs 20-30% minimum to cover operations, marketing, support
        - Drivers get 65-80% depending on job characteristics
        - Clear cost deductions for taxes, insurance, processing
        """
        customer_price = Decimal(str(customer_price))

        if customer_price == 0:
            return {
                "customer_price": Decimal("0"),
                "driver_payment": Decimal("0"),
                "platform_commission": Decimal("0"),
                "breakdown": {},
            }

        # Step 1: Calculate base platform commission (ensures profitability)
        base_commission_rate = DriverCompensationService._get_base_commission_rate(
            customer_price
        )

        # Step 2: Calculate operational costs that must be covered
        operational_costs = DriverCompensationService._calculate_operational_costs(
            request_obj, customer_price
        )

        # Step 3: Calculate complexity adjustments (affects driver share)
        complexity = DriverCompensationService._assess_job_complexity(request_obj)
        complexity_adjustment = DriverCompensationService._get_complexity_adjustment(
            complexity
        )

        # Step 4: Calculate total platform take
        total_platform_rate = (
            base_commission_rate + operational_costs["total_percentage"]
        )

        # Step 5: Apply complexity adjustment to driver share
        driver_base_rate = Decimal("100") - total_platform_rate
        driver_final_rate = driver_base_rate + complexity_adjustment

        # Step 6: Ensure platform sustainability (minimum 20%, maximum 35%)
        if total_platform_rate < Decimal("20"):
            total_platform_rate = Decimal("20")
            driver_final_rate = Decimal("80")
        elif total_platform_rate > Decimal("35"):
            total_platform_rate = Decimal("35")
            driver_final_rate = Decimal("65")
        else:
            driver_final_rate = Decimal("100") - total_platform_rate

        # Step 7: Calculate final amounts
        platform_commission = customer_price * (total_platform_rate / Decimal("100"))
        driver_payment = customer_price * (driver_final_rate / Decimal("100"))

        # Step 8: Apply minimum driver payment (but not if it breaks platform margins)
        min_payment = Decimal("20.00")  # Reduced minimum
        if driver_payment < min_payment and customer_price > Decimal("30"):
            driver_payment = min_payment
            platform_commission = customer_price - driver_payment

        return {
            "customer_price": customer_price,
            "driver_payment": round(driver_payment, 2),
            "platform_commission": round(platform_commission, 2),
            "platform_percentage": float(total_platform_rate),
            "driver_percentage": float(driver_final_rate),
            "breakdown": {
                "base_commission_rate": float(base_commission_rate),
                "operational_costs": operational_costs,
                "complexity": {
                    "level": complexity.value,
                    "adjustment": float(complexity_adjustment),
                },
                "total_platform_rate": float(total_platform_rate),
                "driver_rate": float(driver_final_rate),
            },
        }

    @staticmethod
    def _get_base_commission_rate(customer_price):
        """
        Base platform commission ensuring profitability
        Higher prices can afford slightly lower rates
        """
        if customer_price <= 50:
            return Decimal("30")  # 30% for small jobs (high overhead ratio)
        elif customer_price <= 100:
            return Decimal("25")  # 25% for medium jobs
        elif customer_price <= 200:
            return Decimal("22")  # 22% for larger jobs
        elif customer_price <= 500:
            return Decimal("20")  # 20% for big jobs
        else:
            return Decimal("18")  # 18% for premium jobs

    @staticmethod
    def _calculate_operational_costs(request_obj, customer_price):
        """
        Calculate operational costs as percentages
        """
        costs = {
            "payment_processing": Decimal("2"),  # 2% payment processing
            "insurance_cover": Decimal("1"),  # 1% platform insurance
            "customer_support": Decimal("1"),  # 1% support costs
            "marketing_acquisition": Decimal("3"),  # 3% marketing/acquisition
            "tax_vat": Decimal("2"),  # 2% taxes and VAT
            "total_percentage": Decimal("0"),
        }

        # Add extra costs for complex jobs
        if getattr(request_obj, "requires_special_handling", False):
            costs["special_handling_overhead"] = Decimal("2")
        else:
            costs["special_handling_overhead"] = Decimal("0")

        if getattr(request_obj, "insurance_required", False):
            costs["premium_insurance"] = Decimal("1")
        else:
            costs["premium_insurance"] = Decimal("0")

        costs["total_percentage"] = sum(
            [
                costs["payment_processing"],
                costs["insurance_cover"],
                costs["customer_support"],
                costs["marketing_acquisition"],
                costs["tax_vat"],
                costs["special_handling_overhead"],
                costs["premium_insurance"],
            ]
        )

        return costs

    @staticmethod
    def _assess_job_complexity(request_obj):
        """
        Assess job complexity - same as before
        """
        complexity_score = 0

        # Distance factor (0-3 points)
        if (
            hasattr(request_obj, "estimated_distance")
            and request_obj.estimated_distance
        ):
            distance = float(request_obj.estimated_distance)
            if distance > 100:
                complexity_score += 3
            elif distance > 50:
                complexity_score += 2
            elif distance > 20:
                complexity_score += 1

        # Staff requirement (0-2 points)
        staff_required = getattr(request_obj, "staff_required", 1) or 1
        if staff_required >= 3:
            complexity_score += 2
        elif staff_required >= 2:
            complexity_score += 1

        # Number of stops (0-2 points)
        if hasattr(request_obj, "stops"):
            try:
                stops_count = request_obj.stops.count()
                if stops_count > 4:
                    complexity_score += 2
                elif stops_count > 2:
                    complexity_score += 1
            except:
                pass

        # Special requirements (0-3 points)
        if getattr(request_obj, "requires_special_handling", False):
            complexity_score += 1
        if getattr(request_obj, "insurance_required", False):
            complexity_score += 1
        if getattr(request_obj, "request_type", "") == "instant":
            complexity_score += 1

        # Map score to complexity level
        if complexity_score >= 8:
            return JobComplexity.PREMIUM
        elif complexity_score >= 5:
            return JobComplexity.COMPLEX
        elif complexity_score >= 2:
            return JobComplexity.STANDARD
        else:
            return JobComplexity.SIMPLE

    @staticmethod
    def _get_complexity_adjustment(complexity):
        """
        Complexity adjustment to driver share (small bonuses only)
        """
        complexity_adjustments = {
            JobComplexity.SIMPLE: Decimal(
                "-2"
            ),  # -2% for simple jobs (platform keeps more)
            JobComplexity.STANDARD: Decimal("0"),  # No adjustment for standard
            JobComplexity.COMPLEX: Decimal("2"),  # +2% bonus for complex jobs
            JobComplexity.PREMIUM: Decimal("3"),  # +3% bonus for premium jobs
        }
        return complexity_adjustments[complexity]

    @staticmethod
    def get_pricing_examples():
        """
        Realistic pricing examples with proper platform margins
        """
        return {
            "small_job": {
                "customer_price": 50,
                "expected_driver": 32,  # 64% (30% + 9% costs = 39% platform)
                "expected_platform": 18,  # 36%
                "scenario": "Small local job",
            },
            "standard_job": {
                "customer_price": 150,
                "expected_driver": 105,  # 70% (22% + 9% costs = 31% platform)
                "expected_platform": 45,  # 30%
                "scenario": "Standard medium job",
            },
            "large_job": {
                "customer_price": 300,
                "expected_driver": 225,  # 75% (20% + 9% costs = 29% platform, +2% complexity)
                "expected_platform": 75,  # 25%
                "scenario": "Large complex job",
            },
            "premium_job": {
                "customer_price": 600,
                "expected_driver": 468,  # 78% (18% + 9% costs = 27% platform, +3% complexity)
                "expected_platform": 132,  # 22%
                "scenario": "Premium instant job",
            },
        }


# Integration method for existing RequestPricingService
def calculate_driver_payment_simple(request_obj, final_price):
    """
    Simplified method that integrates with existing RequestPricingService
    """
    result = DriverCompensationService.calculate_driver_compensation(
        request_obj, final_price
    )
    return result["driver_payment"]
