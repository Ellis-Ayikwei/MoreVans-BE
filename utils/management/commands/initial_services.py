from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from apps.Services.models import ServiceCategory, Services


class Command(BaseCommand):
    help = "Imports predefined service categories and services into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating anything",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing service categories and services before importing",
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
                self.style.WARNING(
                    "Clearing all existing service categories and services..."
                )
            )
            services_deleted = Services.objects.all().count()
            categories_deleted = ServiceCategory.objects.all().count()
            Services.objects.all().delete()
            ServiceCategory.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Deleted {services_deleted} services and {categories_deleted} service categories"
                )
            )

        self._import_categories_and_services()

    def _dry_run(self):
        """Show what would be created without actually creating anything"""
        categories_data = self._get_categories_data()
        services_data = self._get_services_data()

        self.stdout.write(f"Would process {len(categories_data)} service categories:")
        for category_data in categories_data:
            slug = slugify(category_data["name"])
            if len(slug) > 50:
                slug = slug[:50].rstrip("-")

            exists = ServiceCategory.objects.filter(slug=slug).exists()
            status = "UPDATE" if exists else "CREATE"
            self.stdout.write(f"  {status}: {slug} - {category_data['name']}")

        self.stdout.write(f"\nWould process {len(services_data)} services:")
        for service_data in services_data:
            exists = Services.objects.filter(name=service_data["name"]).exists()
            status = "UPDATE" if exists else "CREATE"
            self.stdout.write(f"  {status}: {service_data['name']}")

    def _import_categories_and_services(self):
        """Main import logic for both categories and services"""
        categories_data = self._get_categories_data()
        services_data = self._get_services_data()

        with transaction.atomic():
            categories_created = 0
            categories_updated = 0
            services_created = 0
            services_updated = 0

            # First, create/update all categories
            category_map = {}  # To map category names to objects
            for category_data in categories_data:
                slug = slugify(category_data["name"])
                if len(slug) > 50:
                    slug = slug[:50].rstrip("-")

                category, created = ServiceCategory.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "name": category_data["name"],
                        "description": category_data["description"],
                        "icon": category_data["icon"],
                    },
                )

                category_map[category_data["name"]] = category

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

            # Then, create/update all services
            for service_data in services_data:
                category_name = service_data["category"]
                if category_name not in category_map:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Category '{category_name}' not found for service '{service_data['name']}'"
                        )
                    )
                    continue

                service, created = Services.objects.get_or_create(
                    name=service_data["name"],
                    defaults={
                        "description": service_data["description"],
                        "service_category": category_map[category_name],
                        "icon": service_data["icon"],
                    },
                )

                if created:
                    services_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created service: {service_data['name']} (Category: {category_name})"
                        )
                    )
                else:
                    # Update existing service with new data
                    updated = False
                    if service.description != service_data["description"]:
                        service.description = service_data["description"]
                        updated = True
                    if service.service_category != category_map[category_name]:
                        service.service_category = category_map[category_name]
                        updated = True
                    if service.icon != service_data["icon"]:
                        service.icon = service_data["icon"]
                        updated = True

                    if updated:
                        service.save()
                        services_updated += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"Updated service: {service_data['name']} (Category: {category_name})"
                            )
                        )

            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSummary:"
                    f"\n- Created: {categories_created} new service categories"
                    f"\n- Updated: {categories_updated} existing service categories"
                    f"\n- Created: {services_created} new services"
                    f"\n- Updated: {services_updated} existing services"
                    f"\n- Total processed: {len(categories_data)} categories, {len(services_data)} services"
                )
            )

            # Display all categories with their services
            self.stdout.write(
                self.style.HTTP_INFO(
                    f"\nAll service categories and services in database:"
                )
            )
            for category in ServiceCategory.objects.all().order_by("name"):
                self.stdout.write(f"  - {category.slug}: {category.name}")
                for service in category.services.all().order_by("name"):
                    self.stdout.write(f"    * {service.name}")

    def _get_categories_data(self):
        """Return the updated service categories data"""
        return [
            {
                "name": "Removals & Storage",
                "description": "Complete removal and storage services including home, office, student, and international relocations with secure storage solutions.",
                "icon": "IconHome2",
            },
            {
                "name": "Man & Van Services",
                "description": "Affordable delivery and moving services for furniture, appliances, pianos, parcels, and specialized items.",
                "icon": "IconTruck",
            },
            {
                "name": "Vehicle Delivery",
                "description": "Safe and reliable car and motorcycle transport services across the country and internationally.",
                "icon": "IconCar",
            },
        ]

    def _get_services_data(self):
        """Return the updated services data with their associated categories"""
        return [
            # Removals & Storage
            {
                "name": "Home Removals",
                "description": "Complete home relocations with professional moving teams.",
                "category": "Removals & Storage",
                "icon": "IconHome2",
            },
            {
                "name": "International Removals",
                "description": "Cross-border and international moving services with customs handling.",
                "category": "Removals & Storage",
                "icon": "IconWorld",
            },
            {
                "name": "Office Removals",
                "description": "Business and commercial moving services including office furniture and equipment.",
                "category": "Removals & Storage",
                "icon": "IconBuilding",
            },
            {
                "name": "Student Removals",
                "description": "Specialized moving services for university students, including dormitory and shared accommodation moves.",
                "category": "Removals & Storage",
                "icon": "IconSchool",
            },
            {
                "name": "Storage Services",
                "description": "Secure storage solutions with collection and delivery services for short-term or long-term needs.",
                "category": "Removals & Storage",
                "icon": "IconBox",
            },
            # Man & Van Services
            {
                "name": "Furniture & Appliance Delivery",
                "description": "Delivery and moving services for furniture and appliances.",
                "category": "Man & Van Services",
                "icon": "IconSofa",
            },
            {
                "name": "Piano Delivery",
                "description": "Specialist piano transport services with expert handling.",
                "category": "Man & Van Services",
                "icon": "IconMusic",
            },
            {
                "name": "Parcel Delivery",
                "description": "Same-day and next-day parcel delivery services.",
                "category": "Man & Van Services",
                "icon": "IconPackage",
            },
            {
                "name": "eBay Delivery",
                "description": "Specialized delivery services for eBay purchases and sales.",
                "category": "Man & Van Services",
                "icon": "IconPackageImport",
            },
            {
                "name": "Gumtree Delivery",
                "description": "Delivery services for Gumtree purchases and sales.",
                "category": "Man & Van Services",
                "icon": "IconPackageImport",
            },
            {
                "name": "Heavy & Large Item Delivery",
                "description": "Specialized transport for oversized items, appliances, and bulky goods.",
                "category": "Man & Van Services",
                "icon": "IconArrowsMaximize",
            },
            {
                "name": "Specialist & Antiques Delivery",
                "description": "Expert handling and transport of delicate, valuable, or antique items.",
                "category": "Man & Van Services",
                "icon": "IconGlass",
            },
            # Vehicle Delivery
            {
                "name": "Car Transport",
                "description": "Safe and reliable car delivery services across the country.",
                "category": "Vehicle Delivery",
                "icon": "IconCar",
            },
            {
                "name": "Motorcycle Transport",
                "description": "Specialized motorcycle transport with proper securing.",
                "category": "Vehicle Delivery",
                "icon": "IconMotorbike",
            },
        ]
