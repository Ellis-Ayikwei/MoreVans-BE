from django.core.management.base import BaseCommand
from django.db import transaction
from apps.CommonItems.models import (
    CommonItem,
    ItemCategory,
    ItemBrand,
    ItemModel,
    ItemType,
)
from apps.Services.models import ServiceCategory
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
import re

# Import data from separate files
from .data.item_types_data import item_types_data
from .data.common_items import common_items
from .data.brand_data import brand_data


def to_snake_case(name):
    """Convert a display name to snake_case."""
    name = name.replace("&", "and")
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_").lower()


class Command(BaseCommand):
    help = (
        "Imports predefined item categories, brands, models and types into the database"
    )

    def handle(self, *args, **kwargs):
        # Category icons (Tabler) and colors mapping
        category_icons = {
            "furniture": {
                "icon": "IconSofa",
                "color": "bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200",
                "tab_color": "bg-blue-500 text-blue-100 dark:bg-blue-800 dark:text-blue-200",
            },
            "garden": {
                "icon": "IconPlant",
                "color": "bg-lime-100 text-lime-500 dark:bg-lime-800 dark:text-lime-200",
                "tab_color": "bg-lime-500 text-lime-100 dark:bg-lime-800 dark:text-lime-200",
            },
            "office_supplies": {
                "icon": "IconPencil",
                "color": "bg-indigo-100 text-indigo-500 dark:bg-indigo-800 dark:text-indigo-200",
                "tab_color": "bg-indigo-500 text-indigo-100 dark:bg-indigo-800 dark:text-indigo-200",
            },
            "storage": {
                "icon": "IconBoxSeam",
                "color": "bg-orange-100 text-orange-500 dark:bg-orange-800 dark:text-orange-200",
                "tab_color": "bg-orange-500 text-orange-100 dark:bg-orange-800 dark:text-orange-200",
            },
            "oversized": {
                "icon": "IconBox",
                "color": "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
                "tab_color": "bg-gray-500 text-gray-100 dark:bg-gray-800 dark:text-gray-200",
            },
            "clothing_accessories": {
                "icon": "IconShirt",
                "color": "bg-blue-100 text-blue-500 dark:bg-blue-800 dark:text-blue-200",
                "tab_color": "bg-blue-500 text-blue-100 dark:bg-blue-800 dark:text-blue-200",
            },
            "electronics": {
                "icon": "IconDeviceTv",
                "color": "bg-green-100 text-green-500 dark:bg-green-800 dark:text-green-200",
                "tab_color": "bg-green-500 text-green-100 dark:bg-green-800 dark:text-green-200",
            },
            "appliances": {
                "icon": "IconBlender",
                "color": "bg-yellow-100 text-yellow-500 dark:bg-yellow-800 dark:text-yellow-200",
                "tab_color": "bg-yellow-500 text-yellow-100 dark:bg-yellow-800 dark:text-yellow-200",
            },
            "musical": {
                "icon": "IconMusic",
                "color": "bg-red-100 text-red-500 dark:bg-red-800 dark:text-red-200",
                "tab_color": "bg-red-500 text-red-100 dark:bg-red-800 dark:text-red-200",
            },
            "automotive": {
                "icon": "IconCar",
                "color": "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-200",
                "tab_color": "bg-slate-500 text-slate-100 dark:bg-slate-800 dark:text-slate-200",
            },
            "exercise": {
                "icon": "IconBarbell",
                "color": "bg-teal-100 text-teal-500 dark:bg-teal-800 dark:text-teal-200",
                "tab_color": "bg-teal-500 text-teal-100 dark:bg-teal-800 dark:text-teal-200",
            },
            "kitchen_items": {
                "icon": "IconCooker",
                "color": "bg-red-100 text-red-500 dark:bg-red-800 dark:text-red-200",
                "tab_color": "bg-red-500 text-red-100 dark:bg-red-800 dark:text-red-200",
            },
            "tools_equipment": {
                "icon": "IconTool",
                "color": "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-200",
                "tab_color": "bg-zinc-500 text-zinc-100 dark:bg-zinc-800 dark:text-zinc-200",
            },
            "sports": {
                "icon": "IconBallBasketball",
                "color": "bg-amber-100 text-amber-500 dark:bg-amber-800 dark:text-amber-200",
                "tab_color": "bg-amber-500 text-amber-100 dark:bg-amber-800 dark:text-amber-200",
            },
            "books_media": {
                "icon": "IconBook",
                "color": "bg-emerald-100 text-emerald-500 dark:bg-emerald-800 dark:text-emerald-200",
                "tab_color": "bg-emerald-500 text-emerald-100 dark:bg-emerald-800 dark:text-emerald-200",
            },
            "art_collectibles": {
                "icon": "IconPalette",
                "color": "bg-fuchsia-100 text-fuchsia-500 dark:bg-fuchsia-800 dark:text-fuchsia-200",
                "tab_color": "bg-fuchsia-500 text-fuchsia-100 dark:bg-fuchsia-800 dark:text-fuchsia-200",
            },
        }

        # Updated mapping to match ServiceCategory display names in DB
        category_to_service = {
            "furniture": "Furniture Delivery",
            "electronics": "Furniture Delivery",
            "appliances": "Furniture Delivery",
            "musical": "Piano Moving",
            "boxes": "Courier & Delivery",
            "fragile": "Fragile Item Moving",
            "exercise": "Furniture Delivery",
            "garden": "Furniture Delivery",
            "office_supplies": "Office Relocations",
            "kitchen_items": "Furniture Delivery",
            "bathroom": "Furniture Delivery",
            "seasonal": "Furniture Delivery",
            "storage": "Storage Services",
            "children": "Furniture Delivery",
            "art_hobbies": "Fragile Item Moving",
            "sports": "Furniture Delivery",
            "oversized": "Large Item Delivery",
            "tools_equipment": "Furniture Delivery",
            "automotive": "Vehicle Transport",
            "collectibles": "Fragile Item Moving",
            "books_media": "Courier & Delivery",
            "business_equipment": "Office Relocations",
            "clothing_accessories": "Courier & Delivery",
            "outdoor_recreation": "Furniture Delivery",
            "medical_equipment": "Furniture Delivery",
            "home_decor": "Furniture Delivery",
        }

        with transaction.atomic():
            self.stdout.write("Starting import process...")

            # Create categories
            categories_created = 0
            categories_updated = 0

            # Build a mapping from display names to snake_case
            display_to_snake = {}
            for key in list(category_icons.keys()):
                display_to_snake[key] = key  # already snake_case
            # Add display names from data if not already present
            for category_data in common_items:
                display = category_data["name"]
                snake = to_snake_case(display)
                display_to_snake[display] = snake
                if snake not in category_icons:
                    # Add a default icon if missing
                    category_icons[snake] = {
                        "icon": "IconBox",
                        "color": "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
                        "tab_color": "bg-gray-500 text-gray-100 dark:bg-gray-800 dark:text-gray-200",
                    }

            # Create categories (always use snake_case for DB)
            for display_name, snake_case_name in display_to_snake.items():
                icon_data = category_icons[snake_case_name]
                category, created = ItemCategory.objects.get_or_create(
                    name=snake_case_name,
                    defaults={
                        "icon": icon_data["icon"],
                        "color": icon_data["color"],
                        "tab_color": icon_data["tab_color"],
                    },
                )
                if created:
                    categories_created += 1
                    self.stdout.write(
                        f"Created category: {snake_case_name} (from '{display_name}')"
                    )
                else:
                    # Update existing category with new icon data
                    category.icon = icon_data["icon"]
                    category.color = icon_data["color"]
                    category.tab_color = icon_data["tab_color"]
                    category.save()
                    categories_updated += 1
                    self.stdout.write(
                        f"Updated category: {snake_case_name} (from '{display_name}')"
                    )

            self.stdout.write(
                f"Categories: {categories_created} created, {categories_updated} updated"
            )

            # Create item types for each category
            types_created = 0
            types_updated = 0

            # When looking up categories, always use snake_case
            for category_name, types_list in item_types_data.items():
                snake_case_name = to_snake_case(category_name)
                try:
                    category = ItemCategory.objects.get(name=snake_case_name)
                except ObjectDoesNotExist:
                    self.stdout.write(
                        f"WARNING: Category '{snake_case_name}' not found. Skipping types."
                    )
                    continue

                for type_data in types_list:
                    item_type, created = ItemType.objects.get_or_create(
                        name=type_data["name"],
                        category=category,
                        defaults={
                            "description": type_data["description"],
                            "icon": type_data["icon"],
                            "color": type_data["color"],
                            "tab_color": type_data["tab_color"],
                            "priority": type_data["priority"],
                        },
                    )

                    if created:
                        types_created += 1
                        self.stdout.write(
                            f"Created type: {type_data['name']} for {category_name}"
                        )
                    else:
                        # Update existing type
                        item_type.description = type_data["description"]
                        item_type.icon = type_data["icon"]
                        item_type.color = type_data["color"]
                        item_type.tab_color = type_data["tab_color"]
                        item_type.priority = type_data["priority"]
                        item_type.save()
                        types_updated += 1
                        self.stdout.write(
                            f"Updated type: {type_data['name']} for {category_name}"
                        )

            self.stdout.write(
                f"Item types: {types_created} created, {types_updated} updated"
            )

            # Create brands and models for automotive category
            brands_created = 0
            models_created = 0

            if "automotive" in brand_data:
                try:
                    automotive_category = ItemCategory.objects.get(name="automotive")
                except ObjectDoesNotExist:
                    self.stdout.write(
                        f"WARNING: Automotive category not found. Skipping brands."
                    )
                else:
                    for brand_info in brand_data["automotive"]:
                        brand, created = ItemBrand.objects.get_or_create(
                            name=brand_info["brand"],
                            category=automotive_category,
                            defaults={"description": f"{brand_info['brand']} vehicles"},
                        )

                        if created:
                            brands_created += 1
                            self.stdout.write(f"Created brand: {brand_info['brand']}")

                        # Get the type for this brand
                        try:
                            brand_type = ItemType.objects.get(
                                name=brand_info["type"], category=automotive_category
                            )
                        except ObjectDoesNotExist:
                            self.stdout.write(
                                f"WARNING: Type '{brand_info['type']}' not found for brand {brand_info['brand']}. Skipping models."
                            )
                            continue

                        # Create models for this brand
                        for model_name in brand_info["models"]:
                            model, created = ItemModel.objects.get_or_create(
                                name=model_name,
                                brand=brand,
                                defaults={
                                    "description": f"{brand_info['brand']} {model_name}"
                                },
                            )

                            if created:
                                models_created += 1
                                self.stdout.write(
                                    f"Created model: {brand_info['brand']} {model_name}"
                                )

            self.stdout.write(f"Brands: {brands_created} created")
            self.stdout.write(f"Models: {models_created} created")

            # Create common items
            items_created = 0
            items_updated = 0

            # When creating items, always use snake_case for category lookup
            for category_data in common_items:
                display_name = category_data["name"]
                snake_case_name = to_snake_case(display_name)
                try:
                    category = ItemCategory.objects.get(name=snake_case_name)
                except ObjectDoesNotExist:
                    self.stdout.write(
                        f"WARNING: Category '{snake_case_name}' not found. Skipping items."
                    )
                    continue

                # Get service category for this item category
                service_category = None
                if snake_case_name in category_to_service:
                    try:
                        service_category = ServiceCategory.objects.get(
                            name=category_to_service[snake_case_name]
                        )
                    except ObjectDoesNotExist:
                        self.stdout.write(
                            f"WARNING: ServiceCategory '{category_to_service[snake_case_name]}' not found for item category '{snake_case_name}'. Leaving blank."
                        )

                for item_data in category_data["items"]:
                    # Determine the item type
                    item_type = None

                    # First, try to use the explicit type from the item data
                    if "type" in item_data:
                        try:
                            item_type = ItemType.objects.get(
                                name=item_data["type"], category=category
                            )
                        except ObjectDoesNotExist:
                            self.stdout.write(
                                f"WARNING: Type '{item_data['type']}' not found for item '{item_data['name']}'. Will try to infer type."
                            )

                    # If no explicit type or type not found, try to infer from brand/type mapping
                    if not item_type and snake_case_name in brand_data:
                        for brand_info in brand_data[snake_case_name]:
                            if brand_info["brand"].lower() in item_data["name"].lower():
                                try:
                                    item_type = ItemType.objects.get(
                                        name=brand_info["type"], category=category
                                    )
                                    break
                                except ObjectDoesNotExist:
                                    continue

                    # If still no type, try to infer from item name
                    if not item_type:
                        item_name_lower = item_data["name"].lower()
                        for type_obj in ItemType.objects.filter(category=category):
                            if type_obj.name.lower() in item_name_lower:
                                item_type = type_obj
                                break

                    # Create or update the common item
                    defaults = {
                        "category": category,
                        "type": item_type,
                        "service_category": service_category,
                        "dimensions": item_data.get("dimensions", {}),
                        "weight": item_data.get("weight", 0),
                        "needs_disassembly": item_data.get("needs_disassembly", False),
                        "fragile": item_data.get("fragile", False),
                    }

                    item, created = CommonItem.objects.get_or_create(
                        name=item_data["name"], category=category, defaults=defaults
                    )

                    if created:
                        items_created += 1
                        self.stdout.write(
                            f"Created item: {item_data['name']} ({snake_case_name})"
                        )
                    else:
                        # Update existing item
                        item.type = item_type
                        item.service_category = service_category
                        item.dimensions = item_data.get("dimensions", {})
                        item.weight = item_data.get("weight", 0)
                        item.needs_disassembly = item_data.get(
                            "needs_disassembly", False
                        )
                        item.fragile = item_data.get("fragile", False)
                        item.save()
                        items_updated += 1
                        self.stdout.write(
                            f"Updated item: {item_data['name']} ({snake_case_name})"
                        )

            self.stdout.write(
                f"Common items: {items_created} created, {items_updated} updated"
            )

            self.stdout.write("SUCCESS: Import completed successfully!")
