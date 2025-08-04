from django.core.management.base import BaseCommand
from apps.Job.services import InstantJobPricingService
from decimal import Decimal


class Command(BaseCommand):
    help = "Test the instant pricing system with various scenarios"

    def add_arguments(self, parser):
        parser.add_argument(
            "--scenario",
            type=str,
            default="basic",
            help="Pricing scenario to test (basic, complex, peak_hours, weekend, etc.)",
        )

    def handle(self, *args, **options):
        scenario = options["scenario"]

        if scenario == "basic":
            self.test_basic_scenario()
        elif scenario == "complex":
            self.test_complex_scenario()
        elif scenario == "peak_hours":
            self.test_peak_hours_scenario()
        elif scenario == "weekend":
            self.test_weekend_scenario()
        elif scenario == "all":
            self.test_all_scenarios()
        else:
            self.stdout.write(self.style.ERROR(f"Unknown scenario: {scenario}"))

    def test_basic_scenario(self):
        """Test basic instant pricing with minimal factors"""
        self.stdout.write(self.style.SUCCESS("\n=== BASIC SCENARIO ==="))

        class BasicRequest:
            def __init__(self):
                self.base_price = Decimal("50.00")
                self.estimated_distance = Decimal("10.0")
                self.total_weight = Decimal("50.0")
                self.requires_special_handling = False
                self.staff_required = 1
                self.insurance_required = False
                self.priority = "standard"
                self.special_instructions = ""
                self.service_type = "general"
                self.request_type = "instant"

                class MockLocation:
                    def __init__(self):
                        self.access_difficulty = "normal"

                self.pickup_location = MockLocation()
                self.dropoff_location = MockLocation()

        request = BasicRequest()
        pricing_data = InstantJobPricingService.calculate_instant_job_price(request)

        self.print_pricing_summary(pricing_data)

    def test_complex_scenario(self):
        """Test complex instant pricing with many factors"""
        self.stdout.write(self.style.SUCCESS("\n=== COMPLEX SCENARIO ==="))

        class ComplexRequest:
            def __init__(self):
                self.base_price = Decimal("200.00")
                self.estimated_distance = Decimal("50.0")
                self.total_weight = Decimal("300.0")
                self.requires_special_handling = True
                self.staff_required = 3
                self.insurance_required = True
                self.priority = "same_day"
                self.special_instructions = (
                    "Very fragile antique furniture, handle with extreme care"
                )
                self.service_type = "antique_furniture"
                self.request_type = "instant"

                class MockLocation:
                    def __init__(self, difficulty):
                        self.access_difficulty = difficulty

                self.pickup_location = MockLocation("very_difficult")
                self.dropoff_location = MockLocation("difficult")

        request = ComplexRequest()
        pricing_data = InstantJobPricingService.calculate_instant_job_price(request)

        self.print_pricing_summary(pricing_data)

    def test_peak_hours_scenario(self):
        """Test pricing during peak hours"""
        self.stdout.write(self.style.SUCCESS("\n=== PEAK HOURS SCENARIO ==="))

        class PeakHoursRequest:
            def __init__(self):
                self.base_price = Decimal("75.00")
                self.estimated_distance = Decimal("15.0")
                self.total_weight = Decimal("100.0")
                self.requires_special_handling = False
                self.staff_required = 1
                self.insurance_required = False
                self.priority = "express"
                self.special_instructions = ""
                self.service_type = "general"
                self.request_type = "instant"

                class MockLocation:
                    def __init__(self):
                        self.access_difficulty = "normal"

                self.pickup_location = MockLocation()
                self.dropoff_location = MockLocation()

        request = PeakHoursRequest()
        pricing_data = InstantJobPricingService.calculate_instant_job_price(request)

        self.print_pricing_summary(pricing_data)

    def test_weekend_scenario(self):
        """Test pricing during weekend"""
        self.stdout.write(self.style.SUCCESS("\n=== WEEKEND SCENARIO ==="))

        class WeekendRequest:
            def __init__(self):
                self.base_price = Decimal("100.00")
                self.estimated_distance = Decimal("20.0")
                self.total_weight = Decimal("150.0")
                self.requires_special_handling = True
                self.staff_required = 2
                self.insurance_required = True
                self.priority = "standard"
                self.special_instructions = "Weekend delivery requested"
                self.service_type = "furniture_moving"
                self.request_type = "instant"

                class MockLocation:
                    def __init__(self):
                        self.access_difficulty = "normal"

                self.pickup_location = MockLocation()
                self.dropoff_location = MockLocation()

        request = WeekendRequest()
        pricing_data = InstantJobPricingService.calculate_instant_job_price(request)

        self.print_pricing_summary(pricing_data)

    def test_all_scenarios(self):
        """Test all scenarios"""
        self.test_basic_scenario()
        self.test_complex_scenario()
        self.test_peak_hours_scenario()
        self.test_weekend_scenario()

    def print_pricing_summary(self, pricing_data):
        """Print a formatted pricing summary"""
        self.stdout.write(f"Customer Price: £{pricing_data['customer_price']}")
        self.stdout.write(f"Job Price: £{pricing_data['job_price']}")
        self.stdout.write(f"Platform Fee: £{pricing_data['platform_fee']}")
        self.stdout.write(
            f"Profit Margin: {pricing_data['breakdown']['profit_margin']:.1f}%"
        )

        self.stdout.write("\nPricing Factors Applied:")
        for factor in pricing_data["breakdown"]["factors_applied"]:
            self.stdout.write(f"  - {factor}")

        if pricing_data["breakdown"]["adjustments"]:
            self.stdout.write("\nAdjustments:")
            for adjustment, value in pricing_data["breakdown"]["adjustments"].items():
                self.stdout.write(f"  - {adjustment}: {value}")

        self.stdout.write(
            f"\nComplexity Score: {pricing_data['breakdown']['complexity_score']:.2f}"
        )
        self.stdout.write(
            f"Demand Score: {pricing_data['breakdown']['demand_score']:.2f}"
        )
        self.stdout.write("-" * 50)
