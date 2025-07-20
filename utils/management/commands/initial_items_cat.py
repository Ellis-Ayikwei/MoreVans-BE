from django.core.management.base import BaseCommand
from django.db import transaction
from apps.CommonItems.models import CommonItem, ItemCategory


class Command(BaseCommand):
    help = "Imports predefined item categories and types into the database"

    def handle(self, *args, **kwargs):
        # Category icons (Tabler) and colors mapping
        category_icons = {
            "furniture": {
                "icon": "IconSofa",
                "color": "bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200",
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
            "boxes": {
                "icon": "IconBox",
                "color": "bg-orange-100 text-orange-500 dark:bg-orange-800 dark:text-orange-200",
                "tab_color": "bg-orange-500 text-orange-100 dark:bg-orange-800 dark:text-orange-200",
            },
            "fragile": {
                "icon": "IconGlass",
                "color": "bg-pink-100 text-pink-500 dark:bg-pink-800 dark:text-pink-200",
                "tab_color": "bg-pink-500 text-pink-100 dark:bg-pink-800 dark:text-pink-200",
            },
            "exercise": {
                "icon": "IconBarbell",
                "color": "bg-teal-100 text-teal-500 dark:bg-teal-800 dark:text-teal-200",
                "tab_color": "bg-teal-500 text-teal-100 dark:bg-teal-800 dark:text-teal-200",
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
            "kitchen_items": {
                "icon": "IconCooker",
                "color": "bg-red-100 text-red-500 dark:bg-red-800 dark:text-red-200",
                "tab_color": "bg-red-500 text-red-100 dark:bg-red-800 dark:text-red-200",
            },
            "bathroom": {
                "icon": "IconBath",
                "color": "bg-cyan-100 text-cyan-500 dark:bg-cyan-800 dark:text-cyan-200",
                "tab_color": "bg-cyan-500 text-cyan-100 dark:bg-cyan-800 dark:text-cyan-200",
            },
            "seasonal": {
                "icon": "IconSnowflake",
                "color": "bg-sky-100 text-sky-500 dark:bg-sky-800 dark:text-sky-200",
                "tab_color": "bg-sky-500 text-sky-100 dark:bg-sky-800 dark:text-sky-200",
            },
            "storage": {
                "icon": "IconBoxSeam",
                "color": "bg-orange-100 text-orange-500 dark:bg-orange-800 dark:text-orange-200",
                "tab_color": "bg-orange-500 text-orange-100 dark:bg-orange-800 dark:text-orange-200",
            },
            "children": {
                "icon": "IconBabyCarriage",
                "color": "bg-purple-100 text-purple-500 dark:bg-purple-800 dark:text-purple-200",
                "tab_color": "bg-purple-500 text-purple-100 dark:bg-purple-800 dark:text-purple-200",
            },
            "art_hobbies": {
                "icon": "IconPalette",
                "color": "bg-fuchsia-100 text-fuchsia-500 dark:bg-fuchsia-800 dark:text-fuchsia-200",
                "tab_color": "bg-fuchsia-500 text-fuchsia-100 dark:bg-fuchsia-800 dark:text-fuchsia-200",
            },
            "sports": {
                "icon": "IconBallBasketball",
                "color": "bg-amber-100 text-amber-500 dark:bg-amber-800 dark:text-amber-200",
                "tab_color": "bg-amber-500 text-amber-100 dark:bg-amber-800 dark:text-amber-200",
            },
            "oversized": {
                "icon": "IconArrowsMaximize",
                "color": "bg-rose-100 text-rose-500 dark:bg-rose-800 dark:text-rose-200",
                "tab_color": "bg-rose-500 text-rose-100 dark:bg-rose-800 dark:text-rose-200",
            },
            "tools_equipment": {
                "icon": "IconTool",
                "color": "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-200",
                "tab_color": "bg-zinc-500 text-zinc-100 dark:bg-zinc-800 dark:text-zinc-200",
            },
            "automotive": {
                "icon": "IconCar",
                "color": "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-200",
                "tab_color": "bg-slate-500 text-slate-100 dark:bg-slate-800 dark:text-slate-200",
            },
            "collectibles": {
                "icon": "IconDiamond",
                "color": "bg-violet-100 text-violet-500 dark:bg-violet-800 dark:text-violet-200",
                "tab_color": "bg-violet-500 text-violet-100 dark:bg-violet-800 dark:text-violet-200",
            },
            "books_media": {
                "icon": "IconBook",
                "color": "bg-emerald-100 text-emerald-500 dark:bg-emerald-800 dark:text-emerald-200",
                "tab_color": "bg-emerald-500 text-emerald-100 dark:bg-emerald-800 dark:text-emerald-200",
            },
            "business_equipment": {
                "icon": "IconBriefcase",
                "color": "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-200",
                "tab_color": "bg-gray-500 text-gray-100 dark:bg-gray-800 dark:text-gray-200",
            },
            "clothing_accessories": {
                "icon": "IconShirt",
                "color": "bg-blue-100 text-blue-500 dark:bg-blue-800 dark:text-blue-200",
                "tab_color": "bg-blue-500 text-blue-100 dark:bg-blue-800 dark:text-blue-200",
            },
            "outdoor_recreation": {
                "icon": "IconMountain",
                "color": "bg-lime-100 text-lime-500 dark:bg-lime-800 dark:text-lime-200",
                "tab_color": "bg-lime-500 text-lime-100 dark:bg-lime-800 dark:text-lime-200",
            },
            "medical_equipment": {
                "icon": "IconFirstAidKit",
                "color": "bg-red-100 text-red-500 dark:bg-red-800 dark:text-red-200",
                "tab_color": "bg-red-500 text-red-100 dark:bg-red-800 dark:text-red-200",
            },
            "home_decor": {
                "icon": "IconHome",
                "color": "bg-amber-100 text-amber-500 dark:bg-amber-800 dark:text-amber-200",
                "tab_color": "bg-amber-500 text-amber-100 dark:bg-amber-800 dark:text-amber-200",
            },
        }

        # Mapping from item category to sub-service category name
        category_to_service = {
            "furniture": "Furniture & Appliance Delivery",
            "electronics": "Furniture & Appliance Delivery",
            "appliances": "Furniture & Appliance Delivery",
            "musical": "Piano Delivery",
            "boxes": "Parcel Delivery",
            "fragile": "Specialist & Antiques Delivery",
            "exercise": "Furniture & Appliance Delivery",
            "garden": "Furniture & Appliance Delivery",
            "office_supplies": "Office Removals",
            "kitchen_items": "Furniture & Appliance Delivery",
            "bathroom": "Furniture & Appliance Delivery",
            "seasonal": "Furniture & Appliance Delivery",
            "storage": "Storage Services",
            "children": "Furniture & Appliance Delivery",
            "art_hobbies": "Specialist & Antiques Delivery",
            "sports": "Furniture & Appliance Delivery",
            "oversized": "Heavy & Large Item Delivery",
            "tools_equipment": "Furniture & Appliance Delivery",
            "automotive": "Car Transport",
            "collectibles": "Specialist & Antiques Delivery",
            "books_media": "Parcel Delivery",
            "business_equipment": "Office Removals",
            "clothing_accessories": "Furniture & Appliance Delivery",
            "outdoor_recreation": "Furniture & Appliance Delivery",
            "medical_equipment": "Furniture & Appliance Delivery",
            "home_decor": "Furniture & Appliance Delivery",
        }

        # Common moving "items" data structure
        common_items = [
            {
                "name": "furniture",
                "items": [
                    {
                        "name": "Sofa/Couch (3-seater)",
                        "dimensions": "200 × 90 × 90 cm",
                        "weight": "45",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Loveseat (2-seater)",
                        "dimensions": "150 × 90 × 90 cm",
                        "weight": "35",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Sectional Sofa",
                        "dimensions": "300 × 200 × 90 cm",
                        "weight": "80",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Armchair",
                        "dimensions": "90 × 85 × 85 cm",
                        "weight": "25",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Recliner Chair",
                        "dimensions": "95 × 95 × 100 cm",
                        "weight": "35",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Ottoman",
                        "dimensions": "60 × 60 × 45 cm",
                        "weight": "8",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Coffee Table",
                        "dimensions": "120 × 60 × 45 cm",
                        "weight": "15",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Side Table",
                        "dimensions": "45 × 45 × 55 cm",
                        "weight": "8",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "TV Stand",
                        "dimensions": "160 × 45 × 50 cm",
                        "weight": "25",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Display Cabinet",
                        "dimensions": "100 × 40 × 180 cm",
                        "weight": "35",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Dining Table",
                        "dimensions": "180 × 90 × 75 cm",
                        "weight": "30",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Dining Chair",
                        "dimensions": "45 × 45 × 90 cm",
                        "weight": "5",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Buffet/Sideboard",
                        "dimensions": "150 × 50 × 85 cm",
                        "weight": "45",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "China Cabinet",
                        "dimensions": "120 × 45 × 190 cm",
                        "weight": "55",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Bar Stool",
                        "dimensions": "40 × 40 × 75 cm",
                        "weight": "7",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Bed Frame (Single)",
                        "dimensions": "90 × 190 × 40 cm",
                        "weight": "30",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Bed Frame (Double)",
                        "dimensions": "140 × 190 × 40 cm",
                        "weight": "40",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Bed Frame (Queen)",
                        "dimensions": "150 × 200 × 40 cm",
                        "weight": "45",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Bed Frame (King)",
                        "dimensions": "180 × 200 × 40 cm",
                        "weight": "50",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Mattress (Single)",
                        "dimensions": "90 × 190 × 20 cm",
                        "weight": "15",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Mattress (Double)",
                        "dimensions": "140 × 190 × 25 cm",
                        "weight": "25",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Mattress (Queen)",
                        "dimensions": "150 × 200 × 25 cm",
                        "weight": "30",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Mattress (King)",
                        "dimensions": "180 × 200 × 25 cm",
                        "weight": "35",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Nightstand",
                        "dimensions": "45 × 40 × 50 cm",
                        "weight": "10",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Dresser",
                        "dimensions": "120 × 50 × 80 cm",
                        "weight": "40",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Wardrobe",
                        "dimensions": "120 × 60 × 200 cm",
                        "weight": "60",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Chest of Drawers",
                        "dimensions": "80 × 45 × 90 cm",
                        "weight": "30",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Vanity Table",
                        "dimensions": "100 × 45 × 75 cm",
                        "weight": "20",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Mirror (Floor)",
                        "dimensions": "60 × 5 × 170 cm",
                        "weight": "15",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Desk",
                        "dimensions": "140 × 70 × 75 cm",
                        "weight": "25",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Office Chair",
                        "dimensions": "60 × 60 × 110 cm",
                        "weight": "12",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Bookshelf",
                        "dimensions": "90 × 30 × 180 cm",
                        "weight": "25",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Filing Cabinet",
                        "dimensions": "40 × 50 × 100 cm",
                        "weight": "30",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Crib",
                        "dimensions": "140 × 70 × 90 cm",
                        "weight": "25",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Changing Table",
                        "dimensions": "90 × 60 × 90 cm",
                        "weight": "20",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Bunk Bed",
                        "dimensions": "200 × 90 × 160 cm",
                        "weight": "70",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Toy Chest",
                        "dimensions": "80 × 40 × 50 cm",
                        "weight": "15",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "electronics",
                "items": [
                    {
                        "name": "TV (32-40 inch)",
                        "dimensions": "95 × 15 × 60 cm",
                        "weight": "10",
                        "fragile": True,
                    },
                    {
                        "name": "TV (40-50 inch)",
                        "dimensions": "120 × 15 × 70 cm",
                        "weight": "15",
                        "fragile": True,
                    },
                    {
                        "name": "TV (50-65 inch)",
                        "dimensions": "150 × 15 × 90 cm",
                        "weight": "20",
                        "fragile": True,
                    },
                    {
                        "name": "TV (65+ inch)",
                        "dimensions": "170 × 15 × 100 cm",
                        "weight": "30",
                        "fragile": True,
                    },
                    {
                        "name": "Computer Monitor",
                        "dimensions": "60 × 20 × 40 cm",
                        "weight": "5",
                        "fragile": True,
                    },
                    {
                        "name": "Projector",
                        "dimensions": "35 × 25 × 15 cm",
                        "weight": "4",
                        "fragile": True,
                    },
                    {
                        "name": "Desktop Computer",
                        "dimensions": "50 × 25 × 50 cm",
                        "weight": "10",
                        "fragile": True,
                    },
                    {
                        "name": "Laptop",
                        "dimensions": "35 × 25 × 3 cm",
                        "weight": "2.5",
                        "fragile": True,
                    },
                    {
                        "name": "Tablet",
                        "dimensions": "25 × 18 × 1 cm",
                        "weight": "0.5",
                        "fragile": True,
                    },
                    {
                        "name": "Stereo System",
                        "dimensions": "60 × 40 × 30 cm",
                        "weight": "15",
                        "fragile": True,
                    },
                    {
                        "name": "Speakers (Pair)",
                        "dimensions": "30 × 25 × 40 cm",
                        "weight": "8",
                        "fragile": True,
                    },
                    {
                        "name": "Soundbar",
                        "dimensions": "100 × 10 × 10 cm",
                        "weight": "4",
                        "fragile": True,
                    },
                    {
                        "name": "Turntable/Record Player",
                        "dimensions": "45 × 35 × 15 cm",
                        "weight": "6",
                        "fragile": True,
                    },
                    {
                        "name": "Subwoofer",
                        "dimensions": "40 × 40 × 40 cm",
                        "weight": "12",
                        "fragile": True,
                    },
                    {
                        "name": "Printer",
                        "dimensions": "50 × 40 × 30 cm",
                        "weight": "8",
                        "fragile": True,
                    },
                    {
                        "name": "Scanner",
                        "dimensions": "45 × 30 × 10 cm",
                        "weight": "4",
                        "fragile": True,
                    },
                    {
                        "name": "Photocopier (Small)",
                        "dimensions": "60 × 50 × 40 cm",
                        "weight": "20",
                        "fragile": True,
                    },
                    {
                        "name": "Gaming Console",
                        "dimensions": "35 × 30 × 10 cm",
                        "weight": "3",
                        "fragile": True,
                    },
                    {
                        "name": "Gaming PC",
                        "dimensions": "50 × 25 × 50 cm",
                        "weight": "15",
                        "fragile": True,
                    },
                    {
                        "name": "Router/Modem",
                        "dimensions": "25 × 20 × 5 cm",
                        "weight": "1",
                        "fragile": True,
                    },
                    {
                        "name": "Network Switch",
                        "dimensions": "30 × 20 × 5 cm",
                        "weight": "1.5",
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "appliances",
                "items": [
                    {
                        "name": "Refrigerator (Standard)",
                        "dimensions": "70 × 70 × 180 cm",
                        "weight": "80",
                        "fragile": True,
                    },
                    {
                        "name": "Refrigerator (Side-by-Side)",
                        "dimensions": "90 × 70 × 180 cm",
                        "weight": "120",
                        "fragile": True,
                    },
                    {
                        "name": "Freezer (Upright)",
                        "dimensions": "60 × 60 × 150 cm",
                        "weight": "70",
                        "fragile": True,
                    },
                    {
                        "name": "Freezer (Chest)",
                        "dimensions": "90 × 60 × 85 cm",
                        "weight": "60",
                        "fragile": True,
                    },
                    {
                        "name": "Range/Stove",
                        "dimensions": "75 × 65 × 90 cm",
                        "weight": "60",
                        "fragile": True,
                    },
                    {
                        "name": "Oven (Built-in)",
                        "dimensions": "60 × 60 × 60 cm",
                        "weight": "35",
                        "fragile": True,
                    },
                    {
                        "name": "Dishwasher",
                        "dimensions": "60 × 60 × 85 cm",
                        "weight": "50",
                        "fragile": True,
                    },
                    {
                        "name": "Washing Machine",
                        "dimensions": "60 × 60 × 85 cm",
                        "weight": "70",
                        "fragile": True,
                    },
                    {
                        "name": "Dryer",
                        "dimensions": "60 × 60 × 85 cm",
                        "weight": "40",
                        "fragile": True,
                    },
                    {
                        "name": "Washer/Dryer Combo",
                        "dimensions": "60 × 60 × 85 cm",
                        "weight": "85",
                        "fragile": True,
                    },
                    {
                        "name": "Microwave",
                        "dimensions": "50 × 40 × 30 cm",
                        "weight": "12",
                        "fragile": True,
                    },
                    {
                        "name": "Toaster Oven",
                        "dimensions": "45 × 35 × 25 cm",
                        "weight": "5",
                        "fragile": True,
                    },
                    {
                        "name": "Coffee Maker",
                        "dimensions": "35 × 25 × 40 cm",
                        "weight": "4",
                        "fragile": True,
                    },
                    {
                        "name": "Food Processor",
                        "dimensions": "30 × 25 × 40 cm",
                        "weight": "5",
                        "fragile": True,
                    },
                    {
                        "name": "Blender",
                        "dimensions": "20 × 20 × 40 cm",
                        "weight": "3",
                        "fragile": True,
                    },
                    {
                        "name": "Stand Mixer",
                        "dimensions": "35 × 30 × 35 cm",
                        "weight": "10",
                        "fragile": True,
                    },
                    {
                        "name": "Toaster",
                        "dimensions": "30 × 20 × 20 cm",
                        "weight": "2",
                        "fragile": True,
                    },
                    {
                        "name": "Kettle",
                        "dimensions": "25 × 20 × 25 cm",
                        "weight": "1.5",
                        "fragile": True,
                    },
                    {
                        "name": "Vacuum Cleaner",
                        "dimensions": "40 × 30 × 30 cm",
                        "weight": "7",
                        "fragile": False,
                    },
                    {
                        "name": "Air Purifier",
                        "dimensions": "40 × 25 × 60 cm",
                        "weight": "8",
                        "fragile": True,
                    },
                    {
                        "name": "Dehumidifier",
                        "dimensions": "35 × 25 × 50 cm",
                        "weight": "10",
                        "fragile": True,
                    },
                    {
                        "name": "Air Conditioner (Portable)",
                        "dimensions": "45 × 40 × 80 cm",
                        "weight": "30",
                        "fragile": True,
                    },
                    {
                        "name": "Air Conditioner (Window)",
                        "dimensions": "60 × 55 × 40 cm",
                        "weight": "25",
                        "fragile": True,
                    },
                    {
                        "name": "Space Heater",
                        "dimensions": "25 × 20 × 40 cm",
                        "weight": "4",
                        "fragile": True,
                    },
                    {
                        "name": "Fan (Standing)",
                        "dimensions": "50 × 50 × 130 cm",
                        "weight": "5",
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "exercise",
                "items": [
                    {
                        "name": "Treadmill",
                        "dimensions": "180 × 90 × 140 cm",
                        "weight": "90",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Exercise Bike",
                        "dimensions": "100 × 60 × 140 cm",
                        "weight": "35",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Elliptical Machine",
                        "dimensions": "170 × 65 × 170 cm",
                        "weight": "80",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Weight Bench",
                        "dimensions": "120 × 60 × 50 cm",
                        "weight": "25",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Home Gym System",
                        "dimensions": "200 × 100 × 210 cm",
                        "weight": "150",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Rowing Machine",
                        "dimensions": "210 × 55 × 50 cm",
                        "weight": "30",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Dumbbells Set",
                        "dimensions": "50 × 30 × 25 cm",
                        "weight": "30",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Weight Plates Set",
                        "dimensions": "60 × 60 × 30 cm",
                        "weight": "80",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Yoga Equipment",
                        "dimensions": "70 × 40 × 15 cm",
                        "weight": "3",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "musical",
                "items": [
                    {
                        "name": "Piano (Upright)",
                        "dimensions": "150 × 60 × 130 cm",
                        "weight": "250",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Piano (Grand)",
                        "dimensions": "200 × 150 × 100 cm",
                        "weight": "400",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Digital Piano/Keyboard",
                        "dimensions": "140 × 45 × 90 cm",
                        "weight": "25",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Guitar (Acoustic)",
                        "dimensions": "110 × 40 × 15 cm",
                        "weight": "3",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Guitar (Electric)",
                        "dimensions": "100 × 40 × 15 cm",
                        "weight": "4",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Drum Set",
                        "dimensions": "150 × 150 × 130 cm",
                        "weight": "50",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Amplifier",
                        "dimensions": "60 × 50 × 25 cm",
                        "weight": "15",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Violin/Viola",
                        "dimensions": "80 × 30 × 15 cm",
                        "weight": "1.5",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Cello",
                        "dimensions": "120 × 40 × 20 cm",
                        "weight": "5",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "garden",
                "items": [
                    {
                        "name": "Patio Table",
                        "dimensions": "150 × 90 × 75 cm",
                        "weight": "20",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Patio Chair",
                        "dimensions": "60 × 60 × 90 cm",
                        "weight": "6",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Garden Bench",
                        "dimensions": "150 × 60 × 85 cm",
                        "weight": "25",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "BBQ/Grill",
                        "dimensions": "120 × 60 × 110 cm",
                        "weight": "40",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Lawn Mower",
                        "dimensions": "170 × 50 × 100 cm",
                        "weight": "30",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Garden Shed (Small)",
                        "dimensions": "180 × 120 × 200 cm",
                        "weight": "90",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Parasol/Umbrella",
                        "dimensions": "200 × 30 × 30 cm",
                        "weight": "10",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Outdoor Heater",
                        "dimensions": "50 × 50 × 220 cm",
                        "weight": "15",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Plant Pots (Large)",
                        "dimensions": "50 × 50 × 50 cm",
                        "weight": "15",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "fragile",
                "items": [
                    {
                        "name": "Mirror (Wall)",
                        "dimensions": "100 × 5 × 80 cm",
                        "weight": "10",
                        "fragile": True,
                    },
                    {
                        "name": "Artwork/Painting",
                        "dimensions": "100 × 5 × 80 cm",
                        "weight": "5",
                        "fragile": True,
                    },
                    {
                        "name": "China Set",
                        "dimensions": "60 × 40 × 30 cm",
                        "weight": "15",
                        "fragile": True,
                    },
                    {
                        "name": "Glassware Box",
                        "dimensions": "40 × 30 × 30 cm",
                        "weight": "10",
                        "fragile": True,
                    },
                    {
                        "name": "Crystal Chandelier",
                        "dimensions": "60 × 60 × 80 cm",
                        "weight": "15",
                        "fragile": True,
                    },
                    {
                        "name": "Antique Furniture",
                        "dimensions": "120 × 60 × 90 cm",
                        "weight": "40",
                        "fragile": True,
                        "needs_disassembly": False,
                    },
                    {
                        "name": "Sculpture",
                        "dimensions": "40 × 40 × 60 cm",
                        "weight": "15",
                        "fragile": True,
                    },
                    {
                        "name": "Aquarium (Empty)",
                        "dimensions": "100 × 50 × 50 cm",
                        "weight": "20",
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "office_supplies",
                "items": [
                    {
                        "name": "File Boxes",
                        "dimensions": "40 × 30 × 25 cm",
                        "weight": "5",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Paper Shredder",
                        "dimensions": "35 × 25 × 45 cm",
                        "weight": "7",
                        "fragile": True,
                    },
                    {
                        "name": "Whiteboard",
                        "dimensions": "120 × 5 × 90 cm",
                        "weight": "8",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Cork Board",
                        "dimensions": "90 × 3 × 60 cm",
                        "weight": "4",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Office Safe",
                        "dimensions": "50 × 45 × 60 cm",
                        "weight": "80",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Projector Screen",
                        "dimensions": "200 × 10 × 15 cm",
                        "weight": "7",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Document Storage Cabinet",
                        "dimensions": "80 × 40 × 150 cm",
                        "weight": "35",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Office Water Cooler",
                        "dimensions": "35 × 35 × 100 cm",
                        "weight": "15",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "kitchen_items",
                "items": [
                    {
                        "name": "Knife Block Set",
                        "dimensions": "30 × 15 × 35 cm",
                        "weight": "3",
                        "fragile": True,
                    },
                    {
                        "name": "Pots and Pans Set",
                        "dimensions": "60 × 40 × 30 cm",
                        "weight": "10",
                        "fragile": False,
                    },
                    {
                        "name": "Dish Set (12 piece)",
                        "dimensions": "45 × 30 × 40 cm",
                        "weight": "8",
                        "fragile": True,
                    },
                    {
                        "name": "Cutlery Set",
                        "dimensions": "35 × 25 × 15 cm",
                        "weight": "3",
                        "fragile": False,
                    },
                    {
                        "name": "Cutting Board",
                        "dimensions": "40 × 30 × 3 cm",
                        "weight": "2",
                        "fragile": False,
                    },
                    {
                        "name": "Pressure Cooker",
                        "dimensions": "30 × 30 × 25 cm",
                        "weight": "4",
                        "fragile": True,
                    },
                    {
                        "name": "Air Fryer",
                        "dimensions": "35 × 35 × 40 cm",
                        "weight": "5",
                        "fragile": True,
                    },
                    {
                        "name": "Kitchen Scale",
                        "dimensions": "20 × 15 × 5 cm",
                        "weight": "0.5",
                        "fragile": True,
                    },
                    {
                        "name": "Baking Trays Set",
                        "dimensions": "40 × 30 × 15 cm",
                        "weight": "3",
                        "fragile": False,
                    },
                    {
                        "name": "Mixer/Blender",
                        "dimensions": "25 × 20 × 35 cm",
                        "weight": "3",
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "bathroom",
                "items": [
                    {
                        "name": "Bathroom Cabinet",
                        "dimensions": "60 × 20 × 70 cm",
                        "weight": "15",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Shower Caddy",
                        "dimensions": "25 × 15 × 70 cm",
                        "weight": "2",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Toilet Paper Stand",
                        "dimensions": "20 × 20 × 70 cm",
                        "weight": "3",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Towel Rack",
                        "dimensions": "60 × 20 × 10 cm",
                        "weight": "2",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Bathroom Scale",
                        "dimensions": "30 × 30 × 5 cm",
                        "weight": "2",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Shower Curtain & Rod",
                        "dimensions": "180 × 10 × 10 cm",
                        "weight": "2",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Bath Mats Set",
                        "dimensions": "60 × 40 × 10 cm",
                        "weight": "2",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "seasonal",
                "items": [
                    {
                        "name": "Christmas Tree (Artificial)",
                        "dimensions": "100 × 100 × 180 cm",
                        "weight": "10",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Holiday Decorations Box",
                        "dimensions": "60 × 40 × 35 cm",
                        "weight": "8",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Camping Tent",
                        "dimensions": "70 × 30 × 30 cm",
                        "weight": "7",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Snowblower",
                        "dimensions": "140 × 60 × 100 cm",
                        "weight": "40",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Inflatable Pool",
                        "dimensions": "60 × 40 × 20 cm",
                        "weight": "5",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Beach Umbrella",
                        "dimensions": "160 × 20 × 20 cm",
                        "weight": "3",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Patio Heater",
                        "dimensions": "50 × 50 × 220 cm",
                        "weight": "20",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Skiing Equipment",
                        "dimensions": "180 × 30 × 20 cm",
                        "weight": "12",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "storage",
                "items": [
                    {
                        "name": "Plastic Storage Bin (Large)",
                        "dimensions": "60 × 40 × 40 cm",
                        "weight": "3",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Plastic Storage Bin (Medium)",
                        "dimensions": "45 × 35 × 30 cm",
                        "weight": "2",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Plastic Storage Bin (Small)",
                        "dimensions": "35 × 25 × 20 cm",
                        "weight": "1",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Metal Shelving Unit",
                        "dimensions": "90 × 45 × 180 cm",
                        "weight": "25",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Closet Organizer System",
                        "dimensions": "180 × 40 × 200 cm",
                        "weight": "30",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Shoe Rack",
                        "dimensions": "80 × 30 × 40 cm",
                        "weight": "5",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Coat Rack",
                        "dimensions": "50 × 50 × 180 cm",
                        "weight": "8",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Cube Storage Unit",
                        "dimensions": "120 × 30 × 120 cm",
                        "weight": "20",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "children",
                "items": [
                    {
                        "name": "Playpen",
                        "dimensions": "100 × 100 × 80 cm",
                        "weight": "15",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "High Chair",
                        "dimensions": "60 × 70 × 100 cm",
                        "weight": "8",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Baby Walker",
                        "dimensions": "65 × 65 × 70 cm",
                        "weight": "5",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Stroller",
                        "dimensions": "80 × 60 × 100 cm",
                        "weight": "10",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Baby Swing",
                        "dimensions": "70 × 60 × 80 cm",
                        "weight": "7",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Baby Monitor",
                        "dimensions": "15 × 10 × 10 cm",
                        "weight": "0.5",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Toy Storage Box",
                        "dimensions": "80 × 40 × 40 cm",
                        "weight": "5",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Changing Station",
                        "dimensions": "90 × 50 × 90 cm",
                        "weight": "15",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Baby Bouncer",
                        "dimensions": "60 × 50 × 40 cm",
                        "weight": "4",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "art_hobbies",
                "items": [
                    {
                        "name": "Easel",
                        "dimensions": "70 × 70 × 180 cm",
                        "weight": "8",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Art Supplies Box",
                        "dimensions": "50 × 40 × 20 cm",
                        "weight": "10",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Sewing Machine",
                        "dimensions": "45 × 25 × 35 cm",
                        "weight": "8",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Crafting Table",
                        "dimensions": "120 × 60 × 75 cm",
                        "weight": "20",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Quilting Frame",
                        "dimensions": "200 × 100 × 110 cm",
                        "weight": "15",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Model Building Set",
                        "dimensions": "40 × 30 × 20 cm",
                        "weight": "5",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Pottery Wheel",
                        "dimensions": "60 × 60 × 50 cm",
                        "weight": "30",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Photography Equipment",
                        "dimensions": "50 × 40 × 30 cm",
                        "weight": "10",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "sports",
                "items": [
                    {
                        "name": "Bicycle",
                        "dimensions": "180 × 60 × 110 cm",
                        "weight": "15",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Golf Clubs Set",
                        "dimensions": "120 × 40 × 40 cm",
                        "weight": "12",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Snowboard/Skis",
                        "dimensions": "180 × 30 × 15 cm",
                        "weight": "8",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Tennis Rackets",
                        "dimensions": "70 × 30 × 5 cm",
                        "weight": "1",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Basketball Hoop",
                        "dimensions": "120 × 80 × 30 cm",
                        "weight": "25",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Kayak",
                        "dimensions": "350 × 70 × 40 cm",
                        "weight": "20",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Surfboard",
                        "dimensions": "220 × 60 × 8 cm",
                        "weight": "4",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Table Tennis Table",
                        "dimensions": "280 × 150 × 80 cm",
                        "weight": "70",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Fishing Equipment",
                        "dimensions": "150 × 30 × 20 cm",
                        "weight": "10",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "oversized",
                "items": [
                    {
                        "name": "Hot Tub",
                        "dimensions": "220 × 220 × 90 cm",
                        "weight": "300",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Pool Table",
                        "dimensions": "250 × 140 × 80 cm",
                        "weight": "320",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Large Artwork/Sculpture",
                        "dimensions": "200 × 50 × 200 cm",
                        "weight": "40",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Grandfather Clock",
                        "dimensions": "60 × 40 × 200 cm",
                        "weight": "60",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Chandelier (Large)",
                        "dimensions": "100 × 100 × 120 cm",
                        "weight": "25",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Antique Cabinet",
                        "dimensions": "180 × 60 × 210 cm",
                        "weight": "100",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Gun Safe",
                        "dimensions": "60 × 50 × 150 cm",
                        "weight": "270",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Large Aquarium/Terrarium",
                        "dimensions": "150 × 60 × 80 cm",
                        "weight": "50",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "tools_equipment",
                "items": [
                    {
                        "name": "Toolbox (Large)",
                        "dimensions": "60 × 30 × 30 cm",
                        "weight": "15",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Workbench",
                        "dimensions": "150 × 60 × 90 cm",
                        "weight": "35",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Power Drill Set",
                        "dimensions": "40 × 30 × 15 cm",
                        "weight": "5",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Circular Saw",
                        "dimensions": "35 × 25 × 30 cm",
                        "weight": "6",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Table Saw",
                        "dimensions": "80 × 70 × 100 cm",
                        "weight": "45",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Ladder (Extension)",
                        "dimensions": "180 × 40 × 15 cm",
                        "weight": "12",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Pressure Washer",
                        "dimensions": "40 × 35 × 90 cm",
                        "weight": "25",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Generator (Portable)",
                        "dimensions": "60 × 45 × 50 cm",
                        "weight": "40",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "automotive",
                "items": [
                    {
                        "name": "Car Roof Box",
                        "dimensions": "200 × 80 × 40 cm",
                        "weight": "20",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Spare Tire",
                        "dimensions": "65 × 65 × 20 cm",
                        "weight": "15",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Car Parts Box",
                        "dimensions": "60 × 40 × 30 cm",
                        "weight": "25",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Motorcycle Helmet",
                        "dimensions": "35 × 25 × 25 cm",
                        "weight": "1.5",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Bicycle Rack",
                        "dimensions": "120 × 30 × 80 cm",
                        "weight": "10",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Car Battery",
                        "dimensions": "30 × 20 × 25 cm",
                        "weight": "18",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Motorcycle Cover",
                        "dimensions": "200 × 40 × 25 cm",
                        "weight": "3",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "collectibles",
                "items": [
                    {
                        "name": "Vinyl Records Collection",
                        "dimensions": "40 × 40 × 40 cm",
                        "weight": "15",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Comic Books Box",
                        "dimensions": "50 × 35 × 30 cm",
                        "weight": "10",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Coin Collection",
                        "dimensions": "30 × 25 × 15 cm",
                        "weight": "5",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Stamp Collection",
                        "dimensions": "35 × 25 × 10 cm",
                        "weight": "3",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Vintage Toys",
                        "dimensions": "60 × 40 × 40 cm",
                        "weight": "8",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Display Case",
                        "dimensions": "100 × 40 × 120 cm",
                        "weight": "30",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Trading Cards Collection",
                        "dimensions": "30 × 20 × 20 cm",
                        "weight": "2",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "books_media",
                "items": [
                    {
                        "name": "Book Box (Small)",
                        "dimensions": "35 × 25 × 25 cm",
                        "weight": "12",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Book Box (Large)",
                        "dimensions": "40 × 30 × 30 cm",
                        "weight": "18",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "DVD/Blu-ray Collection",
                        "dimensions": "40 × 30 × 20 cm",
                        "weight": "8",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Board Games Box",
                        "dimensions": "50 × 40 × 40 cm",
                        "weight": "10",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Encyclopedia Set",
                        "dimensions": "50 × 40 × 30 cm",
                        "weight": "20",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Magazine Collection",
                        "dimensions": "40 × 30 × 40 cm",
                        "weight": "15",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "business_equipment",
                "items": [
                    {
                        "name": "Cash Register",
                        "dimensions": "45 × 45 × 30 cm",
                        "weight": "10",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Credit Card Terminal",
                        "dimensions": "20 × 15 × 10 cm",
                        "weight": "0.8",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Barcode Scanner",
                        "dimensions": "25 × 15 × 10 cm",
                        "weight": "0.5",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Commercial Printer",
                        "dimensions": "80 × 60 × 120 cm",
                        "weight": "60",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Security System",
                        "dimensions": "40 × 35 × 15 cm",
                        "weight": "5",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Office Phone System",
                        "dimensions": "30 × 20 × 15 cm",
                        "weight": "4",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Conference Table",
                        "dimensions": "200 × 100 × 75 cm",
                        "weight": "70",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "clothing_accessories",
                "items": [
                    {
                        "name": "Wardrobe Box",
                        "dimensions": "50 × 60 × 120 cm",
                        "weight": "10",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Shoe Box Collection",
                        "dimensions": "60 × 40 × 40 cm",
                        "weight": "10",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Hat Box",
                        "dimensions": "40 × 40 × 30 cm",
                        "weight": "3",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Jewelry Box",
                        "dimensions": "30 × 20 × 15 cm",
                        "weight": "3",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Dress/Suit Bags",
                        "dimensions": "60 × 10 × 120 cm",
                        "weight": "5",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Winter Clothing Box",
                        "dimensions": "60 × 40 × 40 cm",
                        "weight": "12",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "outdoor_recreation",
                "items": [
                    {
                        "name": "Canoe",
                        "dimensions": "400 × 90 × 40 cm",
                        "weight": "35",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Paddleboard",
                        "dimensions": "350 × 80 × 15 cm",
                        "weight": "12",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Climbing Equipment",
                        "dimensions": "70 × 40 × 30 cm",
                        "weight": "15",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Hiking Backpack",
                        "dimensions": "60 × 40 × 25 cm",
                        "weight": "5",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Golf Cart",
                        "dimensions": "180 × 120 × 180 cm",
                        "weight": "120",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Camping Stove",
                        "dimensions": "70 × 40 × 20 cm",
                        "weight": "8",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Life Jackets (Set)",
                        "dimensions": "60 × 40 × 30 cm",
                        "weight": "6",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "medical_equipment",
                "items": [
                    {
                        "name": "Wheelchair",
                        "dimensions": "75 × 65 × 90 cm",
                        "weight": "15",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Walker",
                        "dimensions": "65 × 55 × 90 cm",
                        "weight": "5",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Hospital Bed",
                        "dimensions": "210 × 100 × 45 cm",
                        "weight": "80",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Oxygen Concentrator",
                        "dimensions": "40 × 35 × 65 cm",
                        "weight": "15",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "CPAP Machine",
                        "dimensions": "30 × 20 × 15 cm",
                        "weight": "2",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Mobility Scooter",
                        "dimensions": "120 × 60 × 90 cm",
                        "weight": "45",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Commode Chair",
                        "dimensions": "55 × 55 × 85 cm",
                        "weight": "8",
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "home_decor",
                "items": [
                    {
                        "name": "Floor Lamp",
                        "dimensions": "45 × 45 × 160 cm",
                        "weight": "8",
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Table Lamp",
                        "dimensions": "35 × 35 × 60 cm",
                        "weight": "3",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Area Rug (Small)",
                        "dimensions": "150 × 150 × 5 cm",
                        "weight": "8",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Area Rug (Large)",
                        "dimensions": "300 × 200 × 5 cm",
                        "weight": "15",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Curtains/Drapes",
                        "dimensions": "40 × 30 × 20 cm",
                        "weight": "4",
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Wall Clock",
                        "dimensions": "40 × 10 × 40 cm",
                        "weight": "2",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Vases Collection",
                        "dimensions": "50 × 40 × 30 cm",
                        "weight": "12",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Indoor Plants (Medium)",
                        "dimensions": "40 × 40 × 80 cm",
                        "weight": "8",
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
        ]

        # Process each category and its "items"
        with transaction.atomic():
            categories_created = 0
            items_created = 0

            for category_data in common_items:
                # Create or get the category
                category_name = category_data["name"]
                display_name = category_name.replace(
                    "_", " "
                ).title()  # Convert underscores to spaces and capitalize

                # Get icon and color information
                icon_data = category_icons.get(
                    category_name,
                    {
                        "icon": "IconBox",  # Default icon
                        "color": "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
                        "tab_color": "bg-gray-500 text-gray-100 dark:bg-gray-800 dark:text-gray-200",
                    },
                )

                category, created = ItemCategory.objects.get_or_create(
                    name=display_name,
                    defaults={
                        "description": f"Common {display_name} items for moving",
                        "icon": icon_data["icon"],
                        "color": icon_data["color"],
                        "tab_color": icon_data["tab_color"],
                    },
                )

                if created:
                    categories_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Created category: {display_name}")
                    )
                else:
                    # Update the category with icon and color if it already exists
                    category.icon = icon_data["icon"]
                    category.color = icon_data["color"]
                    category.tab_color = icon_data["tab_color"]
                    category.save()
                    self.stdout.write(
                        f"Updated category: {display_name} with icon and color information"
                    )

                # Create the item types for this category
                for item_data in category_data["items"]:
                    # Convert "weight" to numeric
                    weight = float(item_data.get("weight", 0))

                    # Handle missing fields with defaults
                    needs_disassembly = item_data.get("needs_disassembly", False)
                    fragile = item_data.get("fragile", False)

                    # Look up the service category for this item (sub-service category)
                    service_category_name = category_to_service.get(category_name)
                    service_category_obj = None
                    if service_category_name:
                        from apps.Services.models import ServiceCategory

                        try:
                            service_category_obj = ServiceCategory.objects.get(
                                name=service_category_name
                            )
                        except ServiceCategory.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"ServiceCategory '{service_category_name}' not found for item category '{category_name}'. Leaving blank."
                                )
                            )

                    # Create the item type
                    item_type, created = CommonItem.objects.get_or_create(
                        name=item_data["name"],
                        category=category,
                        defaults={
                            "dimensions": item_data.get("dimensions", ""),
                            "weight": weight,
                            "needs_disassembly": needs_disassembly,
                            "fragile": fragile,
                            "service_category": service_category_obj,
                        },
                    )

                    if created:
                        items_created += 1
                        if (
                            items_created % 10 == 0
                        ):  # Log every 10 "items" to avoid console spam
                            self.stdout.write(f"Created {items_created} items...")

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully imported {categories_created} categories and {items_created} item types with Tabler icon information"
                )
            )
