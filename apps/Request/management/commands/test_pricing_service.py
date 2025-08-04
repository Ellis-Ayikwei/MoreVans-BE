from django.core.management.base import BaseCommand
from apps.Request.models import Request
from apps.Request.services import RequestPricingService
from decimal import Decimal


class Command(BaseCommand):
    help = "Test the RequestPricingService with different scenarios"

    def add_arguments(self, parser):
        parser.add_argument(
            "--scenario",
            type=str,
            default="basic",
            help="Test scenario: basic, instant, complex, high_value",
        )
        parser.add_argument(
            "--final_price", type=float, default=250.00, help="Final price to test with"
        )

    def handle(self, *args, **options):
        scenario = options["scenario"]
        final_price = Decimal(str(options["final_price"]))

        self.stdout.write(f"Testing RequestPricingService with scenario: {scenario}")
        self.stdout.write(f"Final price: £{final_price}")
        self.stdout.write("-" * 50)

        # Create a mock request object for testing
        mock_request = self._create_mock_request(scenario, final_price)

        # Test the pricing service
        try:
            # Calculate base job price
            base_job_price = (
                RequestPricingService.calculate_base_job_price_from_final_price(
                    mock_request, final_price
                )
            )

            # Get detailed breakdown
            breakdown = RequestPricingService.get_pricing_breakdown(
                mock_request, final_price
            )

            # Display results
            self.stdout.write(f"Final Price: £{breakdown['final_price']}")
            self.stdout.write(f"Base Job Price: £{base_job_price}")
            self.stdout.write(f"Platform Profit: £{breakdown['platform_profit']}")
            self.stdout.write(f"Total Costs: £{breakdown['total_costs']}")
            self.stdout.write(
                f"Provider Percentage: {breakdown['provider_percentage']:.1f}%"
            )
            self.stdout.write(
                f"Platform Percentage: {breakdown['platform_percentage']:.1f}%"
            )
            self.stdout.write(f"Costs Percentage: {breakdown['costs_percentage']:.1f}%")

            self.stdout.write("\nDetailed Cost Breakdown:")
            cost_breakdown = breakdown["cost_breakdown"]
            for component, amount in cost_breakdown.items():
                if amount > 0:
                    self.stdout.write(
                        f"  {component.replace('_', ' ').title()}: £{amount}"
                    )

            self.stdout.write(f"\nSummary:")
            self.stdout.write(
                f"  Provider gets: £{base_job_price} ({breakdown['provider_percentage']:.1f}%)"
            )
            self.stdout.write(
                f"  Platform keeps: £{breakdown['platform_profit']} ({breakdown['platform_percentage']:.1f}%)"
            )
            self.stdout.write(
                f"  Costs covered: £{breakdown['total_costs']} ({breakdown['costs_percentage']:.1f}%)"
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error testing pricing service: {str(e)}")
            )
            import traceback

            self.stdout.write(traceback.format_exc())

    def _create_mock_request(self, scenario, final_price):
        """Create a mock request object for testing"""

        class MockRequest:
            def __init__(self, scenario, final_price):
                self.final_price = final_price
                self.base_price = final_price
                self.request_type = (
                    "instant" if scenario in ["instant", "complex"] else "biddable"
                )
                self.estimated_distance = (
                    Decimal("50")
                    if scenario in ["complex", "high_value"]
                    else Decimal("20")
                )
                self.total_weight = (
                    Decimal("500")
                    if scenario in ["complex", "high_value"]
                    else Decimal("100")
                )
                self.staff_required = 2 if scenario == "complex" else 1
                self.requires_special_handling = scenario in ["complex", "high_value"]
                self.insurance_required = scenario == "high_value"
                self.insurance_value = (
                    final_price * Decimal("1.5") if scenario == "high_value" else None
                )

                # Mock stops for multiple locations scenario
                class MockStops:
                    def count(self):
                        return 3 if scenario == "complex" else 1

                self.stops = MockStops()

        return MockRequest(scenario, final_price)
