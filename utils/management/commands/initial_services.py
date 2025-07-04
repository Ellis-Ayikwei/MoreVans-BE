from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from apps.Services.models import ServiceCategory


class Command(BaseCommand):
    help = "Imports predefined service categories into the database"

    def handle(self, *args, **kwargs):
        # Define main categories and their subcategories
        main_categories = [
            {
                "name": "Removals & Storage",
                "icon": "IconHome2",
                "description": "All types of removals and storage services.",
                "subcategories": [
                    {"name": "Home removals", "icon": "IconHome2", "description": "Complete home relocations with professional moving teams. From small apartments to large family homes."},
                    {"name": "International removals", "icon": "IconWorld", "description": "Cross-border removals and European transportation services with customs handling."},
                    {"name": "Office removals", "icon": "IconBuilding", "description": "Business and commercial moving services including office furniture, equipment, and document handling."},
                    {"name": "Student removals", "icon": "IconSchool", "description": "Specialized moving services for university students, including dormitory and shared accommodation moves."},
                    {"name": "Storage services", "icon": "IconBox", "description": "Secure storage solutions with collection and delivery services for short-term or long-term needs."},
                ]
            },
            {
                "name": "Man & Van Services",
                "icon": "IconTruck",
                "description": "Flexible van and delivery services for a variety of needs.",
                "subcategories": [
                    {"name": "Furniture & appliance delivery", "icon": "IconSofa", "description": "Single item and furniture courier services for purchases, sales, or individual piece relocations."},
                    {"name": "Piano delivery", "icon": "IconMusic", "description": "Specialist piano transport services with expert handling for upright, grand, and digital pianos."},
                    {"name": "Parcel delivery", "icon": "IconPackage", "description": "Same-day and next-day courier services for parcels, documents, and urgent deliveries."},
                    {"name": "eBay delivery", "icon": "IconPackageImport", "description": "Delivery services for eBay purchases and sales."},
                    {"name": "Gumtree delivery", "icon": "IconPackageImport", "description": "Delivery services for Gumtree purchases and sales."},
                    {"name": "Heavy & large item delivery", "icon": "IconArrowsMaximize", "description": "Specialized transport for oversized items, appliances, and bulky goods that won't fit in regular vehicles."},
                    {"name": "Specialist & antiques delivery", "icon": "IconGlass", "description": "Expert handling and transport of delicate items including artwork, antiques, and valuable possessions."},
                ]
            },
            {
                "name": "Vehicle Delivery",
                "icon": "IconCar",
                "description": "Transport services for cars and motorcycles.",
                "subcategories": [
                    {"name": "Car transport", "icon": "IconCar", "description": "Safe and reliable car delivery services across the country and internationally."},
                    {"name": "Motorcycle transport", "icon": "IconMotorbike", "description": "Safe and reliable motorcycle delivery services."},
                ]
            },
        ]

        with transaction.atomic():
            for main_cat in main_categories:
                main_slug = slugify(main_cat["name"])
                main_obj, _ = ServiceCategory.objects.get_or_create(
                    slug=main_slug,
                    defaults={
                        "name": main_cat["name"],
                        "description": main_cat["description"],
                        "icon": main_cat["icon"],
                        "parent": None,
                    },
                )
                for sub in main_cat["subcategories"]:
                    sub_slug = slugify(sub["name"])
                    ServiceCategory.objects.get_or_create(
                        slug=sub_slug,
                        defaults={
                            "name": sub["name"],
                            "description": sub["description"],
                            "icon": sub["icon"],
                            "parent": main_obj,
                        },
                    )
        self.stdout.write(self.style.SUCCESS("Service categories and subcategories imported successfully."))

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating anything",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing service categories before importing",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No data will be created or modified")
            )
            self._dry_run()
            return

        if options["clear"]:
            self.stdout.write(
                self.style.WARNING("Clearing all existing service categories...")
            )
            deleted_count = ServiceCategory.objects.all().count()
            ServiceCategory.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Deleted {deleted_count} existing service categories"
                )
            )

        self._import_categories()

    def _dry_run(self):
        """Show what would be created without actually creating anything"""
        service_categories = self._get_service_categories_data()

        self.stdout.write(
            f"Would process {len(service_categories)} service categories:"
        )
        for category_data in service_categories:
            slug = slugify(category_data["name"])
            if len(slug) > 50:
                slug = slug[:50].rstrip("-")

            exists = ServiceCategory.objects.filter(slug=slug).exists()
            status = "UPDATE" if exists else "CREATE"
            self.stdout.write(f"  {status}: {slug} - {category_data['name']}")

    def _import_categories(self):
        """Main import logic"""
        service_categories = self._get_service_categories_data()

        with transaction.atomic():
            categories_created = 0
            categories_updated = 0

            for category_data in service_categories:
                # Generate slug from name
                slug = slugify(category_data["name"])

                # Ensure slug is not longer than 50 characters
                if len(slug) > 50:
                    slug = slug[:50].rstrip("-")

                # Create or update the service category
                category, created = ServiceCategory.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "name": category_data["name"],
                        "description": category_data["description"],
                        "icon": category_data["icon"],
                    },
                )

                if created:
                    categories_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created service category: {category_data['name']}"
                        )
                    )
                else:
                    # Update existing category with new data
                    updated = False
                    if category.name != category_data["name"]:
                        category.name = category_data["name"]
                        updated = True
                    if category.description != category_data["description"]:
                        category.description = category_data["description"]
                        updated = True
                    if category.icon != category_data["icon"]:
                        category.icon = category_data["icon"]
                        updated = True

                    if updated:
                        category.save()
                        categories_updated += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"Updated service category: {category_data['name']}"
                            )
                        )
                    else:
                        self.stdout.write(
                            f"Service category already exists and is up to date: {category_data['name']}"
                        )

            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSummary:"
                    f"\n- Created: {categories_created} new service categories"
                    f"\n- Updated: {categories_updated} existing service categories"
                    f"\n- Total processed: {len(service_categories)} service categories"
                )
            )

            # Display all categories
            self.stdout.write(
                self.style.HTTP_INFO(f"\nAll service categories in database:")
            )
            for category in ServiceCategory.objects.all().order_by("name"):
                self.stdout.write(f"  - {category.slug}: {category.name}")

    def _get_service_categories_data(self):
        """Return the service categories data"""
        return [
            {
                "name": "House Removals",
                "description": "Complete home relocations with professional moving teams. From small apartments to large family homes.",
                "icon": "IconHome2",
            },
            {
                "name": "Man and Van Services",
                "description": "Affordable moving services for smaller loads, single items, or when you need an extra pair of hands.",
                "icon": "IconTruck",
            },
            {
                "name": "Office Relocations",
                "description": "Business and commercial moving services including office furniture, equipment, and document handling.",
                "icon": "IconBuilding",
            },
            {
                "name": "Student Removals",
                "description": "Specialized moving services for university students, including dormitory and shared accommodation moves.",
                "icon": "IconSchool",
            },
            {
                "name": "Vehicle Transport",
                "description": "Safe and reliable car, motorcycle, and vehicle delivery services across the country and internationally.",
                "icon": "IconCar",
            },
            {
                "name": "Furniture Delivery",
                "description": "Single item and furniture courier services for purchases, sales, or individual piece relocations.",
                "icon": "IconSofa",
            },
            {
                "name": "Piano Moving",
                "description": "Specialist piano transport services with expert handling for upright, grand, and digital pianos.",
                "icon": "IconMusic",
            },
            {
                "name": "Storage Services",
                "description": "Secure storage solutions with collection and delivery services for short-term or long-term needs.",
                "icon": "IconBox",
            },
            {
                "name": "International Moving",
                "description": "Cross-border removals and European transportation services with customs handling.",
                "icon": "IconWorld",
            },
            {
                "name": "Courier & Delivery",
                "description": "Same-day and next-day courier services for parcels, documents, and urgent deliveries.",
                "icon": "IconPackage",
            },
            {
                "name": "Large Item Delivery",
                "description": "Specialized transport for oversized items, appliances, and bulky goods that won't fit in regular vehicles.",
                "icon": "IconArrowsMaximize",
            },
            {
                "name": "Business Logistics",
                "description": "B2B and B2B2C delivery solutions for retailers, e-commerce, and commercial operations.",
                "icon": "IconBriefcase",
            },
            {
                "name": "Fragile Item Moving",
                "description": "Expert handling and transport of delicate items including artwork, antiques, and valuable possessions.",
                "icon": "IconGlass",
            },
            {
                "name": "Emergency Moving",
                "description": "Last-minute and urgent moving services for time-sensitive relocations and deliveries.",
                "icon": "IconClock",
            },
            {
                "name": "Packing Services",
                "description": "Professional packing and unpacking services with quality materials and expert techniques.",
                "icon": "IconPackageImport",
            },
            {
                "name": "Assembly Services",
                "description": "Furniture assembly and disassembly services for complex items and flat-pack furniture.",
                "icon": "IconTool",
            },
            {
                "name": "Waste Removal",
                "description": "House clearance and waste disposal services for unwanted items during moves.",
                "icon": "IconTrash",
            },
            {
                "name": "Pet Transport",
                "description": "Safe and comfortable transportation services for pets during relocations.",
                "icon": "IconDog",
            },
        ]
