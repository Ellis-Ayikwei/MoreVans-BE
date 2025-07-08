from django.core.management.base import BaseCommand
from django.db import transaction
from apps.CommonItems.models import VehicleType, VehicleCategory, VehicleSize


class Command(BaseCommand):
    help = "Imports predefined vehicle types, categories, and sizes into the database"

    def handle(self, *args, **kwargs):
        # Vehicle types data
        vehicle_types = [
            {
                "name": "Goods Vehicle",
                "description": "Commercial vehicles for transporting goods and cargo",
                "icon": "IconTruck",
                "color": "bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200",
                "tab_color": "bg-blue-500 text-blue-100 dark:bg-blue-800 dark:text-blue-200",
                "priority": 1,
            },
            {
                "name": "Vehicle Transporter",
                "description": "Specialized vehicles for transporting other vehicles",
                "icon": "IconTruckDelivery",
                "color": "bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200",
                "tab_color": "bg-green-500 text-green-100 dark:bg-green-800 dark:text-green-200",
                "priority": 2,
            },
        ]

        # Vehicle categories data
        vehicle_categories = [
            # Goods Vehicle categories
            {
                "name": "Small Van",
                "description": "Small commercial vans for light goods transport",
                "type_name": "Goods Vehicle",
                "icon": "IconVan",
                "color": "bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200",
                "tab_color": "bg-blue-500 text-blue-100 dark:bg-blue-800 dark:text-blue-200",
                "priority": 1,
            },
            {
                "name": "Transit Van",
                "description": "Medium-sized transit vans for general cargo",
                "type_name": "Goods Vehicle",
                "icon": "IconTruck",
                "color": "bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200",
                "tab_color": "bg-green-500 text-green-100 dark:bg-green-800 dark:text-green-200",
                "priority": 2,
            },
            {
                "name": "Luton Van",
                "description": "Large luton vans with high capacity",
                "type_name": "Goods Vehicle",
                "icon": "IconTruck",
                "color": "bg-orange-100 text-orange-800 dark:bg-orange-800 dark:text-orange-200",
                "tab_color": "bg-orange-500 text-orange-100 dark:bg-orange-800 dark:text-orange-200",
                "priority": 3,
            },
            {
                "name": "7.5t",
                "description": "7.5 tonne capacity trucks",
                "type_name": "Goods Vehicle",
                "icon": "IconTruck",
                "color": "bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-200",
                "tab_color": "bg-purple-500 text-purple-100 dark:bg-purple-800 dark:text-purple-200",
                "priority": 4,
            },
            {
                "name": "15t",
                "description": "15 tonne capacity trucks",
                "type_name": "Goods Vehicle",
                "icon": "IconTruck",
                "color": "bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200",
                "tab_color": "bg-red-500 text-red-100 dark:bg-red-800 dark:text-red-200",
                "priority": 5,
            },
            {
                "name": "Other Options",
                "description": "Other specialized goods vehicle options",
                "type_name": "Goods Vehicle",
                "icon": "IconTruckOff",
                "color": "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
                "tab_color": "bg-gray-500 text-gray-100 dark:bg-gray-800 dark:text-gray-200",
                "priority": 6,
            },
            # Vehicle Transporter categories
            {
                "name": "Single Flatbed",
                "description": "Single flatbed vehicle transporters",
                "type_name": "Vehicle Transporter",
                "icon": "IconTruck",
                "color": "bg-indigo-100 text-indigo-800 dark:bg-indigo-800 dark:text-indigo-200",
                "tab_color": "bg-indigo-500 text-indigo-100 dark:bg-indigo-800 dark:text-indigo-200",
                "priority": 1,
            },
            {
                "name": "Tow",
                "description": "Tow vehicle transporters",
                "type_name": "Vehicle Transporter",
                "icon": "IconTruck",
                "color": "bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200",
                "tab_color": "bg-yellow-500 text-yellow-100 dark:bg-yellow-800 dark:text-yellow-200",
                "priority": 2,
            },
            {
                "name": "Double Flatbed",
                "description": "Double flatbed vehicle transporters",
                "type_name": "Vehicle Transporter",
                "icon": "IconTruck",
                "color": "bg-teal-100 text-teal-800 dark:bg-teal-800 dark:text-teal-200",
                "tab_color": "bg-teal-500 text-teal-100 dark:bg-teal-800 dark:text-teal-200",
                "priority": 3,
            },
            {
                "name": "Triple Flatbed",
                "description": "Triple flatbed vehicle transporters",
                "type_name": "Vehicle Transporter",
                "icon": "IconTruck",
                "color": "bg-pink-100 text-pink-800 dark:bg-pink-800 dark:text-pink-200",
                "tab_color": "bg-pink-500 text-pink-100 dark:bg-pink-800 dark:text-pink-200",
                "priority": 4,
            },
            {
                "name": "Multi-Car",
                "description": "Multi-car vehicle transporters",
                "type_name": "Vehicle Transporter",
                "icon": "IconTruck",
                "color": "bg-cyan-100 text-cyan-800 dark:bg-cyan-800 dark:text-cyan-200",
                "tab_color": "bg-cyan-500 text-cyan-100 dark:bg-cyan-800 dark:text-cyan-200",
                "priority": 5,
            },
        ]

        # Vehicle sizes data (for Goods Vehicle)
        vehicle_sizes = [
            {
                "name": "SWB",
                "description": "Short Wheelbase - up to 2.4m",
                "max_length": 2.4,
                "icon": "IconRuler",
                "color": "bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200",
                "tab_color": "bg-blue-500 text-blue-100 dark:bg-blue-800 dark:text-blue-200",
                "priority": 1,
            },
            {
                "name": "MWB",
                "description": "Medium Wheelbase - up to 3m",
                "max_length": 3.0,
                "icon": "IconRuler",
                "color": "bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200",
                "tab_color": "bg-green-500 text-green-100 dark:bg-green-800 dark:text-green-200",
                "priority": 2,
            },
            {
                "name": "LWB",
                "description": "Long Wheelbase - up to 4m",
                "max_length": 4.0,
                "icon": "IconRuler",
                "color": "bg-orange-100 text-orange-800 dark:bg-orange-800 dark:text-orange-200",
                "tab_color": "bg-orange-500 text-orange-100 dark:bg-orange-800 dark:text-orange-200",
                "priority": 3,
            },
            {
                "name": "XLWB",
                "description": "Extra Long Wheelbase - 4m+",
                "max_length": None,
                "icon": "IconRuler",
                "color": "bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200",
                "tab_color": "bg-red-500 text-red-100 dark:bg-red-800 dark:text-red-200",
                "priority": 4,
            },
        ]

        # Process each vehicle type, category, and size
        with transaction.atomic():  # type: ignore
            types_created = 0
            categories_created = 0
            sizes_created = 0

            # Create vehicle types
            for type_data in vehicle_types:
                vehicle_type, created = VehicleType.objects.get_or_create(
                    name=type_data["name"],
                    defaults={
                        "description": type_data["description"],
                        "icon": type_data["icon"],
                        "color": type_data["color"],
                        "tab_color": type_data["tab_color"],
                        "priority": type_data["priority"],
                        "is_active": True,
                    },
                )

                if created:
                    types_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Created vehicle type: {type_data['name']}")  # type: ignore
                    )
                else:
                    # Update existing type with latest data
                    vehicle_type.description = type_data["description"]
                    vehicle_type.icon = type_data["icon"]
                    vehicle_type.color = type_data["color"]
                    vehicle_type.tab_color = type_data["tab_color"]
                    vehicle_type.priority = type_data["priority"]
                    vehicle_type.is_active = True
                    vehicle_type.save()
                    self.stdout.write(
                        self.style.WARNING(f"Updated vehicle type: {type_data['name']}")  # type: ignore
                    )

            # Create vehicle categories
            for category_data in vehicle_categories:
                vehicle_type = VehicleType.objects.get(name=category_data["type_name"])
                category, created = VehicleCategory.objects.get_or_create(
                    name=category_data["name"],
                    type=vehicle_type,
                    defaults={
                        "description": category_data["description"],
                        "icon": category_data["icon"],
                        "color": category_data["color"],
                        "tab_color": category_data["tab_color"],
                        "priority": category_data["priority"],
                        "is_active": True,
                    },
                )

                if created:
                    categories_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Created vehicle category: {category_data['name']}")  # type: ignore
                    )
                else:
                    # Update existing category with latest data
                    category.description = category_data["description"]
                    category.icon = category_data["icon"]
                    category.color = category_data["color"]
                    category.tab_color = category_data["tab_color"]
                    category.priority = category_data["priority"]
                    category.is_active = True
                    category.save()
                    self.stdout.write(
                        self.style.WARNING(f"Updated vehicle category: {category_data['name']}")  # type: ignore
                    )

            # Create vehicle sizes
            for size_data in vehicle_sizes:
                size, created = VehicleSize.objects.get_or_create(
                    name=size_data["name"],
                    defaults={
                        "description": size_data["description"],
                        "max_length": size_data["max_length"],
                        "icon": size_data["icon"],
                        "color": size_data["color"],
                        "tab_color": size_data["tab_color"],
                        "priority": size_data["priority"],
                        "is_active": True,
                    },
                )

                if created:
                    sizes_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Created vehicle size: {size_data['name']}")  # type: ignore
                    )
                else:
                    # Update existing size with latest data
                    size.description = size_data["description"]
                    size.max_length = size_data["max_length"]
                    size.icon = size_data["icon"]
                    size.color = size_data["color"]
                    size.tab_color = size_data["tab_color"]
                    size.priority = size_data["priority"]
                    size.is_active = True
                    size.save()
                    self.stdout.write(
                        self.style.WARNING(f"Updated vehicle size: {size_data['name']}")  # type: ignore
                    )

            self.stdout.write(
                self.style.SUCCESS(  # type: ignore
                    f"\nSuccessfully imported {types_created} vehicle types, {categories_created} vehicle categories, and {sizes_created} vehicle sizes"
                )
            )
