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

    def _get_services_data(self):
        """Return the services data with their associated categories"""
        return [
            # House Removals Services
            {
                "name": "Complete Home Removal",
                "description": "Full-service home relocation including packing, moving, and unpacking.",
                "category": "House Removals",
                "icon": "IconHome2",
            },
            {
                "name": "Apartment Moving",
                "description": "Specialized moving services for apartment and flat relocations.",
                "category": "House Removals",
                "icon": "IconHome2",
            },
            {
                "name": "Furniture Moving",
                "description": "Professional furniture moving and placement services.",
                "category": "House Removals",
                "icon": "IconSofa",
            },
            # Man and Van Services
            {
                "name": "Single Item Delivery",
                "description": "Quick and affordable delivery for individual items and small loads.",
                "category": "Man and Van Services",
                "icon": "IconTruck",
            },
            {
                "name": "Small Load Moving",
                "description": "Efficient moving services for small apartments and studio moves.",
                "category": "Man and Van Services",
                "icon": "IconTruck",
            },
            {
                "name": "Same Day Moving",
                "description": "Urgent same-day moving services for time-sensitive relocations.",
                "category": "Man and Van Services",
                "icon": "IconClock",
            },
            # Office Relocations
            {
                "name": "Office Furniture Moving",
                "description": "Professional moving of office furniture, desks, and equipment.",
                "category": "Office Relocations",
                "icon": "IconBuilding",
            },
            {
                "name": "Commercial Equipment Transport",
                "description": "Safe transport of commercial equipment and machinery.",
                "category": "Office Relocations",
                "icon": "IconBuilding",
            },
            {
                "name": "Document and File Moving",
                "description": "Secure handling and transport of important documents and files.",
                "category": "Office Relocations",
                "icon": "IconFile",
            },
            # Student Removals
            {
                "name": "Student Dorm Moving",
                "description": "Specialized moving services for university dormitory relocations.",
                "category": "Student Removals",
                "icon": "IconSchool",
            },
            {
                "name": "Student Storage",
                "description": "Secure storage solutions for students during holidays and breaks.",
                "category": "Student Removals",
                "icon": "IconBox",
            },
            # Vehicle Transport
            {
                "name": "Car Transport",
                "description": "Safe and reliable car delivery services across the country.",
                "category": "Vehicle Transport",
                "icon": "IconCar",
            },
            {
                "name": "Motorcycle Transport",
                "description": "Specialized motorcycle transport with proper securing.",
                "category": "Vehicle Transport",
                "icon": "IconMotorbike",
            },
            {
                "name": "Boat Transport",
                "description": "Professional boat and watercraft transport services.",
                "category": "Vehicle Transport",
                "icon": "IconShip",
            },
            # Furniture Delivery
            {
                "name": "Furniture Assembly",
                "description": "Professional furniture assembly and installation services.",
                "category": "Furniture Delivery",
                "icon": "IconTool",
            },
            {
                "name": "Furniture Disassembly",
                "description": "Safe disassembly of furniture for moving and transport.",
                "category": "Furniture Delivery",
                "icon": "IconTool",
            },
            {
                "name": "Furniture Collection",
                "description": "Collection and delivery of purchased furniture items.",
                "category": "Furniture Delivery",
                "icon": "IconSofa",
            },
            # Piano Moving
            {
                "name": "Grand Piano Moving",
                "description": "Expert handling and transport of grand pianos.",
                "category": "Piano Moving",
                "icon": "IconMusic",
            },
            {
                "name": "Upright Piano Moving",
                "description": "Professional moving services for upright pianos.",
                "category": "Piano Moving",
                "icon": "IconMusic",
            },
            {
                "name": "Digital Piano Transport",
                "description": "Safe transport of digital pianos and keyboards.",
                "category": "Piano Moving",
                "icon": "IconMusic",
            },
            # Storage Services
            {
                "name": "Short-term Storage",
                "description": "Flexible storage solutions for temporary needs.",
                "category": "Storage Services",
                "icon": "IconBox",
            },
            {
                "name": "Long-term Storage",
                "description": "Secure long-term storage with regular maintenance.",
                "category": "Storage Services",
                "icon": "IconBox",
            },
            {
                "name": "Climate-controlled Storage",
                "description": "Temperature and humidity controlled storage for sensitive items.",
                "category": "Storage Services",
                "icon": "IconBox",
            },
            # International Moving
            {
                "name": "European Moving",
                "description": "Cross-border moving services within Europe.",
                "category": "International Moving",
                "icon": "IconWorld",
            },
            {
                "name": "International Shipping",
                "description": "Global shipping and moving services with customs handling.",
                "category": "International Moving",
                "icon": "IconWorld",
            },
            # Courier & Delivery
            {
                "name": "Same Day Delivery",
                "description": "Express same-day delivery services for urgent items.",
                "category": "Courier & Delivery",
                "icon": "IconPackage",
            },
            {
                "name": "Next Day Delivery",
                "description": "Reliable next-day delivery for parcels and documents.",
                "category": "Courier & Delivery",
                "icon": "IconPackage",
            },
            {
                "name": "eBay Delivery",
                "description": "Specialized delivery services for eBay purchases and sales.",
                "category": "Courier & Delivery",
                "icon": "IconPackageImport",
            },
            {
                "name": "Gumtree Delivery",
                "description": "Delivery services for Gumtree purchases and sales.",
                "category": "Courier & Delivery",
                "icon": "IconPackageImport",
            },
            # Large Item Delivery
            {
                "name": "Appliance Delivery",
                "description": "Safe delivery of large appliances like refrigerators and washing machines.",
                "category": "Large Item Delivery",
                "icon": "IconArrowsMaximize",
            },
            {
                "name": "Oversized Item Transport",
                "description": "Specialized transport for items that exceed standard vehicle dimensions.",
                "category": "Large Item Delivery",
                "icon": "IconArrowsMaximize",
            },
            # Business Logistics
            {
                "name": "B2B Delivery",
                "description": "Business-to-business delivery solutions for commercial clients.",
                "category": "Business Logistics",
                "icon": "IconBriefcase",
            },
            {
                "name": "E-commerce Fulfillment",
                "description": "Order fulfillment and delivery services for online retailers.",
                "category": "Business Logistics",
                "icon": "IconBriefcase",
            },
            # Fragile Item Moving
            {
                "name": "Artwork Transport",
                "description": "Expert handling and transport of paintings, sculptures, and artwork.",
                "category": "Fragile Item Moving",
                "icon": "IconGlass",
            },
            {
                "name": "Antique Moving",
                "description": "Specialized moving services for valuable antiques and collectibles.",
                "category": "Fragile Item Moving",
                "icon": "IconGlass",
            },
            {
                "name": "Glass Item Transport",
                "description": "Safe transport of fragile glass items and mirrors.",
                "category": "Fragile Item Moving",
                "icon": "IconGlass",
            },
            # Emergency Moving
            {
                "name": "Emergency Relocation",
                "description": "Urgent moving services for emergency situations.",
                "category": "Emergency Moving",
                "icon": "IconClock",
            },
            {
                "name": "Last-minute Moving",
                "description": "Quick response moving services for immediate needs.",
                "category": "Emergency Moving",
                "icon": "IconClock",
            },
            # Packing Services
            {
                "name": "Professional Packing",
                "description": "Expert packing services using quality materials and techniques.",
                "category": "Packing Services",
                "icon": "IconPackageImport",
            },
            {
                "name": "Unpacking Services",
                "description": "Professional unpacking and organization services.",
                "category": "Packing Services",
                "icon": "IconPackageImport",
            },
            {
                "name": "Specialty Item Packing",
                "description": "Specialized packing for delicate and valuable items.",
                "category": "Packing Services",
                "icon": "IconPackageImport",
            },
            # Assembly Services
            {
                "name": "Furniture Assembly",
                "description": "Professional assembly of flat-pack and complex furniture.",
                "category": "Assembly Services",
                "icon": "IconTool",
            },
            {
                "name": "Equipment Installation",
                "description": "Installation and setup of commercial equipment.",
                "category": "Assembly Services",
                "icon": "IconTool",
            },
            # Waste Removal
            {
                "name": "House Clearance",
                "description": "Complete house clearance and waste removal services.",
                "category": "Waste Removal",
                "icon": "IconTrash",
            },
            {
                "name": "Furniture Disposal",
                "description": "Safe disposal of unwanted furniture and large items.",
                "category": "Waste Removal",
                "icon": "IconTrash",
            },
            # Pet Transport
            {
                "name": "Pet Moving",
                "description": "Safe and comfortable transport services for pets during relocations.",
                "category": "Pet Transport",
                "icon": "IconDog",
            },
            {
                "name": "Pet-friendly Moving",
                "description": "Moving services that accommodate pets during the process.",
                "category": "Pet Transport",
                "icon": "IconDog",
            },
        ]
