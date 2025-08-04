from django.core.management.base import BaseCommand
from apps.Request.driver_compensation import DriverCompensationService


class Command(BaseCommand):
    help = "Test the new driver compensation system with different scenarios"

    def add_arguments(self, parser):
        parser.add_argument(
            "--price", type=float, default=250.00, help="Customer price to test"
        )
        parser.add_argument(
            "--scenario",
            type=str,
            default="standard",
            choices=["simple", "standard", "complex", "instant"],
            help="Job scenario to test",
        )

    def handle(self, *args, **options):
        price = options["price"]
        scenario = options["scenario"]

        self.stdout.write(f"🚚 Driver Compensation Calculator")
        self.stdout.write(f"Customer Price: £{price}")
        self.stdout.write(f"Scenario: {scenario}")
        self.stdout.write("=" * 50)

        # Create mock request object
        mock_request = self._create_mock_request(scenario)

        # Calculate compensation
        result = DriverCompensationService.calculate_driver_compensation(
            mock_request, price
        )

        # Display results
        self._display_results(result)

        # Show examples
        self.stdout.write("\n📊 Pricing Examples:")
        self.stdout.write("-" * 30)
        examples = DriverCompensationService.get_pricing_examples()
        for name, example in examples.items():
            self.stdout.write(
                f"{name}: £{example['customer_price']} → £{example['expected_driver']} ({example['scenario']})"
            )

    def _create_mock_request(self, scenario):
        """Create a mock request object for testing"""

        class MockRequest:
            def __init__(self, scenario):
                if scenario == "simple":
                    self.estimated_distance = 15
                    self.staff_required = 1
                    self.requires_special_handling = False
                    self.insurance_required = False
                    self.request_type = "biddable"
                    self.stops = MockStops(2)

                elif scenario == "standard":
                    self.estimated_distance = 35
                    self.staff_required = 2
                    self.requires_special_handling = False
                    self.insurance_required = False
                    self.request_type = "biddable"
                    self.stops = MockStops(3)

                elif scenario == "complex":
                    self.estimated_distance = 75
                    self.staff_required = 3
                    self.requires_special_handling = True
                    self.insurance_required = True
                    self.request_type = "biddable"
                    self.stops = MockStops(5)

                elif scenario == "instant":
                    self.estimated_distance = 120
                    self.staff_required = 2
                    self.requires_special_handling = True
                    self.insurance_required = True
                    self.request_type = "instant"
                    self.stops = MockStops(4)

        class MockStops:
            def __init__(self, count):
                self._count = count

            def count(self):
                return self._count

        return MockRequest(scenario)

    def _display_results(self, result):
        """Display compensation calculation results"""
        breakdown = result["breakdown"]

        self.stdout.write(f"\n💰 COMPENSATION BREAKDOWN")
        self.stdout.write(f"Customer Price: £{result['customer_price']}")
        self.stdout.write(
            f"Driver Payment: £{result['driver_payment']} ({result['driver_percentage']:.1f}%)"
        )
        self.stdout.write(f"Platform Commission: £{result['platform_commission']}")

        self.stdout.write(f"\n📋 TIER INFO")
        tier = breakdown["tier"]
        self.stdout.write(f"Price Range: {tier['range']}")
        self.stdout.write(f"Platform Fee: {tier['platform_fee']}")
        self.stdout.write(f"Base Driver %: {breakdown['base_percentage']:.1f}%")

        self.stdout.write(f"\n🎯 COMPLEXITY")
        complexity = breakdown["complexity"]
        self.stdout.write(f"Level: {complexity['level']}")
        self.stdout.write(f"Bonus: +{complexity['bonus_percentage']:.1f}%")

        self.stdout.write(f"\n🎁 SERVICE BONUSES")
        bonuses = breakdown["service_bonuses"]
        if bonuses["details"]:
            for detail in bonuses["details"]:
                self.stdout.write(f"  {detail}")
        else:
            self.stdout.write("  No bonuses applied")

        self.stdout.write(f"\n✅ FINAL CALCULATION")
        self.stdout.write(f"Base: {breakdown['base_percentage']:.1f}%")
        self.stdout.write(f"Bonuses: +{breakdown['total_bonuses']:.1f}%")
        self.stdout.write(f"Final Rate: {breakdown['final_percentage']:.1f}%")

        if breakdown["minimum_applied"]:
            self.stdout.write(f"⚠️  Minimum payment guarantee applied")
