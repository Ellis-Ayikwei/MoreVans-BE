from django.core.management.base import BaseCommand
from django.db import transaction
from apps.pricing.services import PricingService
from apps.pricing.models import PricingConfiguration


class Command(BaseCommand):
    help = "Set up default pricing configuration and factors in the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force recreation of default configuration even if one exists",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating anything",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No data will be created")
            )
            self._dry_run()
            return

        if options["force"]:
            self.stdout.write(
                self.style.WARNING("Force mode - will recreate default configuration")
            )
            # Delete existing configurations
            existing_count = PricingConfiguration.objects.count()
            PricingConfiguration.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {existing_count} existing configurations")
            )

        try:
            with transaction.atomic():
                # Use the existing service method to create defaults
                config = PricingService.ensure_default_config_exists()

                if config:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully created default pricing configuration: {config.name}"
                        )
                    )

                    # Show what was created
                    self._show_created_data()
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            "Default configuration already exists. Use --force to recreate."
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Error creating default pricing configuration: {str(e)}"
                )
            )

    def _dry_run(self):
        """Show what would be created without actually creating it"""
        self.stdout.write("Would create the following:")
        self.stdout.write("1. Default Pricing Configuration")
        self.stdout.write("2. Distance Pricing Factor")
        self.stdout.write("3. Weight Pricing Factor")
        self.stdout.write("4. Time Pricing Factor")
        self.stdout.write("5. Weather Pricing Factor")
        self.stdout.write("6. Vehicle Type Pricing Factor")
        self.stdout.write("7. Special Requirements Pricing Factor")
        self.stdout.write("8. Service Level Pricing Factor")
        self.stdout.write("9. Staff Required Pricing Factor")
        self.stdout.write("10. Property Type Pricing Factor")
        self.stdout.write("11. Insurance Pricing Factor")
        self.stdout.write("12. Loading Time Pricing Factor")

    def _show_created_data(self):
        """Show details of what was created"""
        config = PricingConfiguration.objects.filter(is_default=True).first()
        if config:
            self.stdout.write(f"\nConfiguration Details:")
            self.stdout.write(f"  Name: {config.name}")
            self.stdout.write(f"  Base Price: £{config.base_price}")
            self.stdout.write(f"  Min Price: £{config.min_price}")
            self.stdout.write(f"  Max Price Multiplier: {config.max_price_multiplier}x")
            self.stdout.write(f"  Fuel Surcharge: {config.fuel_surcharge_percentage}%")
            self.stdout.write(f"  Carbon Offset: {config.carbon_offset_rate}%")

            # Show associated factors
            self.stdout.write(f"\nAssociated Pricing Factors:")
            self.stdout.write(f"  Distance Factors: {config.distance_factors.count()}")
            self.stdout.write(f"  Weight Factors: {config.weight_factors.count()}")
            self.stdout.write(f"  Time Factors: {config.time_factors.count()}")
            self.stdout.write(f"  Weather Factors: {config.weather_factors.count()}")
            self.stdout.write(f"  Vehicle Factors: {config.vehicle_factors.count()}")
            self.stdout.write(
                f"  Special Requirements: {config.special_requirement_factors.count()}"
            )
            self.stdout.write(
                f"  Service Level Factors: {config.service_level_factors.count()}"
            )
            self.stdout.write(f"  Staff Factors: {config.staff_factors.count()}")
            self.stdout.write(
                f"  Property Type Factors: {config.property_type_factors.count()}"
            )
            self.stdout.write(
                f"  Insurance Factors: {config.insurance_factors.count()}"
            )
            self.stdout.write(
                f"  Loading Time Factors: {config.loading_time_factors.count()}"
            )
