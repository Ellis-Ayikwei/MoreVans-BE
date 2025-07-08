from django.core.management.base import BaseCommand
from django.db import transaction
from apps.CommonItems.models import CommonItem, ItemCategory, ItemBrand, ItemModel
from apps.Services.models import ServiceCategory


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

        brand_data = {
            "automotive": [
                {
                    "brand": "Toyota",
                    "models": [
                        "Corolla",
                        "Camry",
                        "RAV4",
                        "Highlander",
                        "Prius",
                        "Tacoma",
                        "Tundra",
                        "4Runner",
                        "Sequoia",
                        "Land Cruiser",
                        "Sienna",
                        "Avalon",
                        "Yaris",
                        "CH-R",
                        "Venza",
                    ],
                },
                {
                    "brand": "Ford",
                    "models": [
                        "F-150",
                        "Mustang",
                        "Explorer",
                        "Escape",
                        "Bronco",
                        "F-250",
                        "F-350",
                        "Expedition",
                        "Edge",
                        "Ranger",
                        "Focus",
                        "Fiesta",
                        "Transit",
                        "EcoSport",
                        "Fusion",
                    ],
                },
                {
                    "brand": "Chevrolet",
                    "models": [
                        "Silverado",
                        "Malibu",
                        "Camaro",
                        "Equinox",
                        "Bolt EV",
                        "Tahoe",
                        "Suburban",
                        "Colorado",
                        "Traverse",
                        "Blazer",
                        "Impala",
                        "Sonic",
                        "Spark",
                        "Cruze",
                        "Trax",
                    ],
                },
                {
                    "brand": "Honda",
                    "models": [
                        "Civic",
                        "Accord",
                        "CR-V",
                        "Pilot",
                        "Insight",
                        "HR-V",
                        "Passport",
                        "Ridgeline",
                        "Odyssey",
                        "Fit",
                        "Clarity",
                        "Element",
                        "S2000",
                        "NSX",
                    ],
                },
                {
                    "brand": "Tesla",
                    "models": [
                        "Model 3",
                        "Model S",
                        "Model X",
                        "Model Y",
                        "Cybertruck",
                        "Roadster",
                        "Semi",
                    ],
                },
                {
                    "brand": "BMW",
                    "models": [
                        "3 Series",
                        "5 Series",
                        "X3",
                        "X5",
                        "i4",
                        "X1",
                        "X7",
                        "iX",
                        "Z4",
                        "M3",
                        "M5",
                        "X6",
                        "8 Series",
                    ],
                },
                {
                    "brand": "Mercedes-Benz",
                    "models": [
                        "C-Class",
                        "E-Class",
                        "GLC",
                        "GLE",
                        "EQS",
                        "S-Class",
                        "GLA",
                        "GLB",
                        "GLS",
                        "AMG GT",
                        "A-Class",
                    ],
                },
                {
                    "brand": "Porsche",
                    "models": [
                        "911",
                        "Cayenne",
                        "Macan",
                        "Taycan",
                        "Panamera",
                        "Cayman",
                        "Boxster",
                        "718",
                    ],
                },
            ],
            "electronics": [
                {
                    "brand": "Apple",
                    "models": [
                        "iPhone",
                        "iPad",
                        "MacBook",
                        "iMac",
                        "Mac Pro",
                        "Apple Watch",
                        "AirPods",
                        "Apple TV",
                        "Mac Mini",
                        "MacBook Air",
                        "MacBook Pro",
                        "Studio Display",
                        "Pro Display XDR",
                    ],
                },
                {
                    "brand": "Samsung",
                    "models": [
                        "Galaxy S",
                        "Galaxy Note",
                        "Galaxy Tab",
                        "Galaxy A",
                        "Galaxy Z",
                        "Smart TV",
                        "Galaxy Watch",
                        "Galaxy Buds",
                        "The Frame TV",
                        "QLED TV",
                        "Neo QLED",
                        "Odyssey Monitor",
                    ],
                },
                {
                    "brand": "Sony",
                    "models": [
                        "PlayStation",
                        "Bravia TV",
                        "Xperia",
                        "Alpha Camera",
                        "WH-1000XM",
                        "WF-1000XM",
                        "FX Series",
                        "A7 Series",
                        "PlayStation VR",
                        "Walkman",
                        "SRS Speakers",
                    ],
                },
                {
                    "brand": "LG",
                    "models": [
                        "OLED TV",
                        "NanoCell TV",
                        "Gram Laptop",
                        "V60",
                        "G8",
                        "Wing",
                        "UltraFine Monitor",
                        "UltraWide Monitor",
                        "ThinQ Appliances",
                        "Tone Headphones",
                    ],
                },
                {
                    "brand": "Microsoft",
                    "models": [
                        "Surface Pro",
                        "Surface Laptop",
                        "Surface Book",
                        "Xbox",
                        "Surface Studio",
                        "Surface Go",
                        "HoloLens",
                    ],
                },
                {
                    "brand": "Dell",
                    "models": [
                        "XPS",
                        "Inspiron",
                        "Latitude",
                        "Precision",
                        "Alienware",
                        "OptiPlex",
                        "Vostro",
                        "UltraSharp Monitor",
                    ],
                },
                {
                    "brand": "ASUS",
                    "models": [
                        "ROG",
                        "ZenBook",
                        "VivoBook",
                        "TUF",
                        "ProArt",
                        "ROG Strix",
                        "ROG Phone",
                        "ZenFone",
                        "Transformer",
                    ],
                },
                {
                    "brand": "NVIDIA",
                    "models": [
                        "GeForce RTX",
                        "GeForce GTX",
                        "Quadro",
                        "Tesla",
                        "Shield TV",
                        "Jetson",
                        "DGX",
                    ],
                },
            ],
            "appliances": [
                {
                    "brand": "Samsung",
                    "models": [
                        "Bespoke",
                        "Family Hub",
                        "QuickDrive",
                        "AddWash",
                        "AirDresser",
                        "FlexZone",
                        "SpaceMax",
                        "Digital Inverter",
                    ],
                },
                {
                    "brand": "LG",
                    "models": [
                        "InstaView",
                        "TwinWash",
                        "SideKick",
                        "Steam",
                        "ThinQ",
                        "Door-in-Door",
                        "SmartThinQ",
                        "ProBake",
                        "EasyClean",
                    ],
                },
                {
                    "brand": "Whirlpool",
                    "models": [
                        "Cabrio",
                        "Duet",
                        "Maytag",
                        "KitchenAid",
                        "Jenn-Air",
                        "6th Sense",
                        "Load & Go",
                        "FreshFlow",
                        "Adaptive Wash",
                    ],
                },
                {
                    "brand": "GE",
                    "models": [
                        "Profile",
                        "Cafe",
                        "Monogram",
                        "Adora",
                        "Artistry",
                        "SmartDispense",
                        "UltraFresh",
                        "Precise Fill",
                    ],
                },
                {
                    "brand": "Bosch",
                    "models": [
                        "800 Series",
                        "500 Series",
                        "300 Series",
                        "Ascenta",
                        "Benchmark",
                        "FlexSpace",
                        "AutoAir",
                        "CrystalDry",
                    ],
                },
                {
                    "brand": "Dyson",
                    "models": [
                        "V15",
                        "V12",
                        "V11",
                        "V10",
                        "Airwrap",
                        "Hair Dryer",
                        "Pure Cool",
                        "Hot+Cool",
                        "Supersonic",
                        "Corrale",
                    ],
                },
            ],
            "musical": [
                {
                    "brand": "Yamaha",
                    "models": [
                        "Clavinova",
                        "P-Series",
                        "Arius",
                        "TransAcoustic",
                        "Silent Piano",
                        "Montage",
                        "MODX",
                        "PSR Series",
                    ],
                },
                {
                    "brand": "Kawai",
                    "models": [
                        "ES",
                        "CN",
                        "CA",
                        "GL",
                        "SK",
                        "Shigeru",
                        "MP Series",
                        "VPC",
                        "Novus",
                    ],
                },
                {
                    "brand": "Roland",
                    "models": [
                        "FP",
                        "HP",
                        "LX",
                        "V-Piano",
                        "V-Drums",
                        "Fantom",
                        "Jupiter",
                        "JD Series",
                        "TD Series",
                    ],
                },
                {
                    "brand": "Fender",
                    "models": [
                        "Stratocaster",
                        "Telecaster",
                        "Precision Bass",
                        "Jazz Bass",
                        "Mustang",
                        "Jazzmaster",
                        "Jaguar",
                    ],
                },
                {
                    "brand": "Gibson",
                    "models": [
                        "Les Paul",
                        "SG",
                        "ES-335",
                        "Flying V",
                        "Explorer",
                        "Firebird",
                        "Thunderbird",
                    ],
                },
                {
                    "brand": "Taylor",
                    "models": [
                        "814ce",
                        "714ce",
                        "614ce",
                        "514ce",
                        "414ce",
                        "314ce",
                        "214ce",
                        "114ce",
                        "Grand Auditorium",
                    ],
                },
            ],
            "exercise": [
                {
                    "brand": "Peloton",
                    "models": [
                        "Bike",
                        "Bike+",
                        "Tread",
                        "Tread+",
                        "Guide",
                        "Row",
                        "Strength",
                    ],
                },
                {
                    "brand": "NordicTrack",
                    "models": [
                        "Commercial",
                        "Elite",
                        "Pro",
                        "Select",
                        "SpaceSaver",
                        "X Series",
                        "T Series",
                        "Incline Trainer",
                    ],
                },
                {
                    "brand": "Bowflex",
                    "models": [
                        "Max Trainer",
                        "Revolution",
                        "TreadClimber",
                        "C6",
                        "C7",
                        "SelectTech",
                        "HVT",
                    ],
                },
                {
                    "brand": "Life Fitness",
                    "models": [
                        "T5",
                        "T7",
                        "T9",
                        "G7",
                        "Integrity",
                        "Signature Series",
                        "Club Series",
                    ],
                },
            ],
            "tools_equipment": [
                {
                    "brand": "DeWalt",
                    "models": [
                        "20V MAX",
                        "60V MAX",
                        "12V MAX",
                        "DCD Series",
                        "DCS Series",
                        "DCF Series",
                        "DCG Series",
                    ],
                },
                {
                    "brand": "Milwaukee",
                    "models": [
                        "M18",
                        "M12",
                        "M18 FUEL",
                        "M12 FUEL",
                        "PACKOUT",
                        "ONE-KEY",
                        "REDLITHIUM",
                    ],
                },
                {
                    "brand": "Makita",
                    "models": [
                        "18V LXT",
                        "40V MAX XGT",
                        "12V MAX",
                        "DDF Series",
                        "DTD Series",
                        "DGA Series",
                    ],
                },
                {
                    "brand": "Ryobi",
                    "models": [
                        "ONE+",
                        "40V",
                        "18V",
                        "P Series",
                        "RY Series",
                        "P1819",
                        "P108",
                    ],
                },
            ],
        }

        category_to_service = {
            "furniture": "Furniture & appliance delivery",
            "electronics": "Furniture & appliance delivery",
            "appliances": "Furniture & appliance delivery",
            "musical": "Piano delivery",
            "boxes": "Parcel delivery",
            "fragile": "Specialist & antiques delivery",
            "exercise": "Furniture & appliance delivery",
            "garden": "Furniture & appliance delivery",
            "office_supplies": "Office removals",
            "kitchen_items": "Furniture & appliance delivery",
            "bathroom": "Furniture & appliance delivery",
            "seasonal": "Furniture & appliance delivery",
            "storage": "Storage services",
            "children": "Furniture & appliance delivery",
            "art_hobbies": "Specialist & antiques delivery",
            "sports": "Furniture & appliance delivery",
            "oversized": "Heavy & large item delivery",
            "tools_equipment": "Furniture & appliance delivery",
            "automotive": "Car transport",
            "collectibles": "Specialist & antiques delivery",
            "books_media": "Parcel delivery",
            "business_equipment": "Office removals",
            "clothing_accessories": "Parcel delivery",
            "outdoor_recreation": "Furniture & appliance delivery",
            "medical_equipment": "Furniture & appliance delivery",
            "home_decor": "Furniture & appliance delivery",
        }

        # Common items data structure with proper JSON dimensions
        common_items = [
            {
                "name": "furniture",
                "items": [
                    {
                        "name": "Sofa/Couch (3-seater)",
                        "dimensions": {
                            "length": 200,
                            "width": 90,
                            "height": 90,
                            "unit": "cm",
                        },
                        "weight": 45,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Loveseat (2-seater)",
                        "dimensions": {
                            "length": 150,
                            "width": 90,
                            "height": 90,
                            "unit": "cm",
                        },
                        "weight": 35,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Dining Table (6-seater)",
                        "dimensions": {
                            "length": 180,
                            "width": 90,
                            "height": 75,
                            "unit": "cm",
                        },
                        "weight": 25,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Dining Chairs (set of 6)",
                        "dimensions": {
                            "length": 45,
                            "width": 45,
                            "height": 90,
                            "unit": "cm",
                        },
                        "weight": 8,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Bed Frame (Queen)",
                        "dimensions": {
                            "length": 200,
                            "width": 150,
                            "height": 30,
                            "unit": "cm",
                        },
                        "weight": 20,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Wardrobe",
                        "dimensions": {
                            "length": 200,
                            "width": 60,
                            "height": 200,
                            "unit": "cm",
                        },
                        "weight": 40,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Coffee Table",
                        "dimensions": {
                            "length": 120,
                            "width": 60,
                            "height": 45,
                            "unit": "cm",
                        },
                        "weight": 15,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Bookshelf",
                        "dimensions": {
                            "length": 80,
                            "width": 30,
                            "height": 180,
                            "unit": "cm",
                        },
                        "weight": 25,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "garden",
                "items": [
                    {
                        "name": "Patio Table",
                        "dimensions": {
                            "length": 150,
                            "width": 90,
                            "height": 75,
                            "unit": "cm",
                        },
                        "weight": 20,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Garden Chairs (set of 4)",
                        "dimensions": {
                            "length": 50,
                            "width": 50,
                            "height": 90,
                            "unit": "cm",
                        },
                        "weight": 6,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Garden Bench",
                        "dimensions": {
                            "length": 120,
                            "width": 40,
                            "height": 45,
                            "unit": "cm",
                        },
                        "weight": 15,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Plant Pots (large)",
                        "dimensions": {
                            "length": 60,
                            "width": 60,
                            "height": 60,
                            "unit": "cm",
                        },
                        "weight": 10,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Garden Shed",
                        "dimensions": {
                            "length": 200,
                            "width": 150,
                            "height": 200,
                            "unit": "cm",
                        },
                        "weight": 100,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "office_supplies",
                "items": [
                    {
                        "name": "Office Desk",
                        "dimensions": {
                            "length": 140,
                            "width": 70,
                            "height": 75,
                            "unit": "cm",
                        },
                        "weight": 25,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Office Chair",
                        "dimensions": {
                            "length": 60,
                            "width": 60,
                            "height": 120,
                            "unit": "cm",
                        },
                        "weight": 12,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Filing Cabinet",
                        "dimensions": {
                            "length": 50,
                            "width": 60,
                            "height": 130,
                            "unit": "cm",
                        },
                        "weight": 30,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Bookshelf (Office)",
                        "dimensions": {
                            "length": 100,
                            "width": 30,
                            "height": 180,
                            "unit": "cm",
                        },
                        "weight": 20,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Conference Table",
                        "dimensions": {
                            "length": 240,
                            "width": 120,
                            "height": 75,
                            "unit": "cm",
                        },
                        "weight": 50,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "storage",
                "items": [
                    {
                        "name": "Storage Boxes (set of 10)",
                        "dimensions": {
                            "length": 50,
                            "width": 35,
                            "height": 30,
                            "unit": "cm",
                        },
                        "weight": 5,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Plastic Storage Bins",
                        "dimensions": {
                            "length": 60,
                            "width": 40,
                            "height": 40,
                            "unit": "cm",
                        },
                        "weight": 3,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Cardboard Boxes (set of 20)",
                        "dimensions": {
                            "length": 40,
                            "width": 30,
                            "height": 25,
                            "unit": "cm",
                        },
                        "weight": 8,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Storage Cabinet",
                        "dimensions": {
                            "length": 80,
                            "width": 40,
                            "height": 180,
                            "unit": "cm",
                        },
                        "weight": 35,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "oversized",
                "items": [
                    {
                        "name": "Grand Piano",
                        "dimensions": {
                            "length": 280,
                            "width": 150,
                            "height": 100,
                            "unit": "cm",
                        },
                        "weight": 300,
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Pool Table",
                        "dimensions": {
                            "length": 240,
                            "width": 120,
                            "height": 80,
                            "unit": "cm",
                        },
                        "weight": 200,
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Large Safe",
                        "dimensions": {
                            "length": 120,
                            "width": 80,
                            "height": 180,
                            "unit": "cm",
                        },
                        "weight": 400,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Industrial Equipment",
                        "dimensions": {
                            "length": 200,
                            "width": 150,
                            "height": 200,
                            "unit": "cm",
                        },
                        "weight": 500,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "clothing_accessories",
                "items": [
                    {
                        "name": "Wardrobe Boxes (set of 5)",
                        "dimensions": {
                            "length": 60,
                            "width": 40,
                            "height": 120,
                            "unit": "cm",
                        },
                        "weight": 8,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Suitcases (set of 4)",
                        "dimensions": {
                            "length": 70,
                            "width": 45,
                            "height": 30,
                            "unit": "cm",
                        },
                        "weight": 6,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Shoe Boxes (set of 10)",
                        "dimensions": {
                            "length": 30,
                            "width": 20,
                            "height": 15,
                            "unit": "cm",
                        },
                        "weight": 2,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "electronics",
                "items": [
                    {
                        "name": "TV (55-inch)",
                        "dimensions": {
                            "length": 125,
                            "width": 8,
                            "height": 75,
                            "unit": "cm",
                        },
                        "weight": 20,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Computer Monitor",
                        "dimensions": {
                            "length": 60,
                            "width": 20,
                            "height": 40,
                            "unit": "cm",
                        },
                        "weight": 8,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Desktop Computer",
                        "dimensions": {
                            "length": 40,
                            "width": 20,
                            "height": 40,
                            "unit": "cm",
                        },
                        "weight": 10,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Laptop",
                        "dimensions": {
                            "length": 35,
                            "width": 25,
                            "height": 3,
                            "unit": "cm",
                        },
                        "weight": 2,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Gaming Console",
                        "dimensions": {
                            "length": 30,
                            "width": 15,
                            "height": 8,
                            "unit": "cm",
                        },
                        "weight": 3,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "appliances",
                "items": [
                    {
                        "name": "Refrigerator",
                        "dimensions": {
                            "length": 70,
                            "width": 70,
                            "height": 180,
                            "unit": "cm",
                        },
                        "weight": 80,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Washing Machine",
                        "dimensions": {
                            "length": 60,
                            "width": 60,
                            "height": 85,
                            "unit": "cm",
                        },
                        "weight": 70,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Dishwasher",
                        "dimensions": {
                            "length": 60,
                            "width": 60,
                            "height": 85,
                            "unit": "cm",
                        },
                        "weight": 45,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Microwave",
                        "dimensions": {
                            "length": 50,
                            "width": 40,
                            "height": 30,
                            "unit": "cm",
                        },
                        "weight": 15,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Coffee Maker",
                        "dimensions": {
                            "length": 30,
                            "width": 20,
                            "height": 40,
                            "unit": "cm",
                        },
                        "weight": 3,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "musical",
                "items": [
                    {
                        "name": "Acoustic Guitar",
                        "dimensions": {
                            "length": 100,
                            "width": 15,
                            "height": 40,
                            "unit": "cm",
                        },
                        "weight": 2,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Electric Guitar",
                        "dimensions": {
                            "length": 100,
                            "width": 15,
                            "height": 40,
                            "unit": "cm",
                        },
                        "weight": 3,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Keyboard/Piano",
                        "dimensions": {
                            "length": 140,
                            "width": 30,
                            "height": 15,
                            "unit": "cm",
                        },
                        "weight": 12,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Drum Set",
                        "dimensions": {
                            "length": 150,
                            "width": 100,
                            "height": 120,
                            "unit": "cm",
                        },
                        "weight": 25,
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Amplifier",
                        "dimensions": {
                            "length": 60,
                            "width": 40,
                            "height": 30,
                            "unit": "cm",
                        },
                        "weight": 15,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
            {
                "name": "automotive",
                "items": [
                    {
                        "name": "Car Parts (Engine)",
                        "dimensions": {
                            "length": 80,
                            "width": 60,
                            "height": 60,
                            "unit": "cm",
                        },
                        "weight": 150,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Car Parts (Transmission)",
                        "dimensions": {
                            "length": 60,
                            "width": 40,
                            "height": 40,
                            "unit": "cm",
                        },
                        "weight": 80,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Tires (set of 4)",
                        "dimensions": {
                            "length": 70,
                            "width": 70,
                            "height": 25,
                            "unit": "cm",
                        },
                        "weight": 40,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Car Battery",
                        "dimensions": {
                            "length": 30,
                            "width": 20,
                            "height": 20,
                            "unit": "cm",
                        },
                        "weight": 15,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "exercise",
                "items": [
                    {
                        "name": "Treadmill",
                        "dimensions": {
                            "length": 180,
                            "width": 80,
                            "height": 140,
                            "unit": "cm",
                        },
                        "weight": 120,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Exercise Bike",
                        "dimensions": {
                            "length": 140,
                            "width": 60,
                            "height": 120,
                            "unit": "cm",
                        },
                        "weight": 45,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Weight Bench",
                        "dimensions": {
                            "length": 180,
                            "width": 60,
                            "height": 50,
                            "unit": "cm",
                        },
                        "weight": 35,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Dumbbells (set)",
                        "dimensions": {
                            "length": 60,
                            "width": 40,
                            "height": 30,
                            "unit": "cm",
                        },
                        "weight": 50,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "kitchen_items",
                "items": [
                    {
                        "name": "Kitchen Table",
                        "dimensions": {
                            "length": 120,
                            "width": 80,
                            "height": 75,
                            "unit": "cm",
                        },
                        "weight": 20,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Kitchen Chairs (set of 4)",
                        "dimensions": {
                            "length": 45,
                            "width": 45,
                            "height": 90,
                            "unit": "cm",
                        },
                        "weight": 6,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Kitchen Island",
                        "dimensions": {
                            "length": 120,
                            "width": 60,
                            "height": 90,
                            "unit": "cm",
                        },
                        "weight": 40,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Kitchen Cabinets",
                        "dimensions": {
                            "length": 200,
                            "width": 60,
                            "height": 90,
                            "unit": "cm",
                        },
                        "weight": 60,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "tools_equipment",
                "items": [
                    {
                        "name": "Tool Box",
                        "dimensions": {
                            "length": 50,
                            "width": 30,
                            "height": 25,
                            "unit": "cm",
                        },
                        "weight": 8,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Drill Set",
                        "dimensions": {
                            "length": 40,
                            "width": 30,
                            "height": 20,
                            "unit": "cm",
                        },
                        "weight": 5,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Circular Saw",
                        "dimensions": {
                            "length": 35,
                            "width": 25,
                            "height": 15,
                            "unit": "cm",
                        },
                        "weight": 4,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Ladder (6ft)",
                        "dimensions": {
                            "length": 180,
                            "width": 50,
                            "height": 15,
                            "unit": "cm",
                        },
                        "weight": 12,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "sports",
                "items": [
                    {
                        "name": "Basketball Hoop",
                        "dimensions": {
                            "length": 120,
                            "width": 80,
                            "height": 300,
                            "unit": "cm",
                        },
                        "weight": 50,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Tennis Rackets (set of 4)",
                        "dimensions": {
                            "length": 70,
                            "width": 25,
                            "height": 5,
                            "unit": "cm",
                        },
                        "weight": 1,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Golf Clubs (set)",
                        "dimensions": {
                            "length": 120,
                            "width": 30,
                            "height": 15,
                            "unit": "cm",
                        },
                        "weight": 8,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Bicycle",
                        "dimensions": {
                            "length": 170,
                            "width": 60,
                            "height": 100,
                            "unit": "cm",
                        },
                        "weight": 15,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "books_media",
                "items": [
                    {
                        "name": "Book Boxes (set of 10)",
                        "dimensions": {
                            "length": 40,
                            "width": 30,
                            "height": 25,
                            "unit": "cm",
                        },
                        "weight": 8,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "DVD Collection",
                        "dimensions": {
                            "length": 50,
                            "width": 40,
                            "height": 30,
                            "unit": "cm",
                        },
                        "weight": 5,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Vinyl Records",
                        "dimensions": {
                            "length": 40,
                            "width": 40,
                            "height": 20,
                            "unit": "cm",
                        },
                        "weight": 3,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Magazine Collection",
                        "dimensions": {
                            "length": 35,
                            "width": 25,
                            "height": 15,
                            "unit": "cm",
                        },
                        "weight": 2,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "art_collectibles",
                "items": [
                    {
                        "name": "Paintings (Large)",
                        "dimensions": {
                            "length": 100,
                            "width": 5,
                            "height": 80,
                            "unit": "cm",
                        },
                        "weight": 8,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Sculptures",
                        "dimensions": {
                            "length": 50,
                            "width": 30,
                            "height": 60,
                            "unit": "cm",
                        },
                        "weight": 15,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Antique Vases",
                        "dimensions": {
                            "length": 30,
                            "width": 20,
                            "height": 40,
                            "unit": "cm",
                        },
                        "weight": 3,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Art Supplies",
                        "dimensions": {
                            "length": 60,
                            "width": 40,
                            "height": 30,
                            "unit": "cm",
                        },
                        "weight": 10,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                ],
            },
            {
                "name": "automotive",
                "items": [
                    {
                        "name": "Car Engine",
                        "dimensions": {
                            "length": 80,
                            "width": 60,
                            "height": 60,
                            "unit": "cm",
                        },
                        "weight": 150,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Car Transmission",
                        "dimensions": {
                            "length": 60,
                            "width": 40,
                            "height": 40,
                            "unit": "cm",
                        },
                        "weight": 80,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Car Battery",
                        "dimensions": {
                            "length": 30,
                            "width": 20,
                            "height": 20,
                            "unit": "cm",
                        },
                        "weight": 15,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Car Tires (Set of 4)",
                        "dimensions": {
                            "length": 70,
                            "width": 70,
                            "height": 25,
                            "unit": "cm",
                        },
                        "weight": 40,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Car Wheels (Set of 4)",
                        "dimensions": {
                            "length": 70,
                            "width": 70,
                            "height": 30,
                            "unit": "cm",
                        },
                        "weight": 50,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Car Radiator",
                        "dimensions": {
                            "length": 50,
                            "width": 40,
                            "height": 30,
                            "unit": "cm",
                        },
                        "weight": 8,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Car Alternator",
                        "dimensions": {
                            "length": 25,
                            "width": 20,
                            "height": 20,
                            "unit": "cm",
                        },
                        "weight": 5,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Car Starter Motor",
                        "dimensions": {
                            "length": 20,
                            "width": 15,
                            "height": 15,
                            "unit": "cm",
                        },
                        "weight": 3,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Car Exhaust System",
                        "dimensions": {
                            "length": 200,
                            "width": 15,
                            "height": 15,
                            "unit": "cm",
                        },
                        "weight": 25,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Car Suspension Kit",
                        "dimensions": {
                            "length": 60,
                            "width": 40,
                            "height": 30,
                            "unit": "cm",
                        },
                        "weight": 35,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Car Brake System",
                        "dimensions": {
                            "length": 50,
                            "width": 30,
                            "height": 25,
                            "unit": "cm",
                        },
                        "weight": 20,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Car Fuel Tank",
                        "dimensions": {
                            "length": 80,
                            "width": 40,
                            "height": 30,
                            "unit": "cm",
                        },
                        "weight": 12,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Car Dashboard",
                        "dimensions": {
                            "length": 120,
                            "width": 30,
                            "height": 20,
                            "unit": "cm",
                        },
                        "weight": 8,
                        "needs_disassembly": True,
                        "fragile": True,
                    },
                    {
                        "name": "Car Seats (Set of 4)",
                        "dimensions": {
                            "length": 60,
                            "width": 50,
                            "height": 100,
                            "unit": "cm",
                        },
                        "weight": 60,
                        "needs_disassembly": True,
                        "fragile": False,
                    },
                    {
                        "name": "Car Steering Wheel",
                        "dimensions": {
                            "length": 40,
                            "width": 40,
                            "height": 10,
                            "unit": "cm",
                        },
                        "weight": 2,
                        "needs_disassembly": False,
                        "fragile": False,
                    },
                    {
                        "name": "Complete Car (Sedan)",
                        "dimensions": {
                            "length": 480,
                            "width": 180,
                            "height": 150,
                            "unit": "cm",
                        },
                        "weight": 1500,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Complete Car (SUV)",
                        "dimensions": {
                            "length": 500,
                            "width": 200,
                            "height": 180,
                            "unit": "cm",
                        },
                        "weight": 2000,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Complete Car (Truck)",
                        "dimensions": {
                            "length": 550,
                            "width": 220,
                            "height": 190,
                            "unit": "cm",
                        },
                        "weight": 2500,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Complete Car (Sports Car)",
                        "dimensions": {
                            "length": 450,
                            "width": 180,
                            "height": 130,
                            "unit": "cm",
                        },
                        "weight": 1400,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Complete Car (Electric Vehicle)",
                        "dimensions": {
                            "length": 480,
                            "width": 190,
                            "height": 150,
                            "unit": "cm",
                        },
                        "weight": 1800,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Complete Car (Luxury Vehicle)",
                        "dimensions": {
                            "length": 520,
                            "width": 190,
                            "height": 150,
                            "unit": "cm",
                        },
                        "weight": 2000,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Complete Car (Compact)",
                        "dimensions": {
                            "length": 420,
                            "width": 170,
                            "height": 140,
                            "unit": "cm",
                        },
                        "weight": 1200,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Complete Car (Van/Minivan)",
                        "dimensions": {
                            "length": 500,
                            "width": 190,
                            "height": 190,
                            "unit": "cm",
                        },
                        "weight": 1800,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                    {
                        "name": "Complete Car (Hybrid)",
                        "dimensions": {
                            "length": 470,
                            "width": 180,
                            "height": 150,
                            "unit": "cm",
                        },
                        "weight": 1600,
                        "needs_disassembly": False,
                        "fragile": True,
                    },
                ],
            },
        ]

        # Process each category and its items
        with transaction.atomic():  # type: ignore
            categories_created = 0
            brands_created = 0
            models_created = 0
            items_created = 0

            for category_data in common_items:
                # Create or get the category
                category_name = category_data["name"]
                display_name = category_name.replace("_", " ").title()

                # Get icon and color information
                icon_data = category_icons.get(
                    category_name,
                    {
                        "icon": "IconBox",
                        "color": "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
                        "tab_color": "bg-gray-500 text-gray-100 dark:bg-gray-800 dark:text-gray-200",
                    },
                )

                category, created = ItemCategory.objects.get_or_create(
                    name=display_name,
                    defaults={
                        "description": f"Common {display_name} items for moving and transport",
                        "icon": icon_data["icon"],
                        "color": icon_data["color"],
                        "tab_color": icon_data["tab_color"],
                    },
                )

                if created:
                    categories_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Created category: {display_name}")  # type: ignore
                    )
                else:
                    # Update existing category with latest icon and color data
                    category.icon = icon_data["icon"]
                    category.color = icon_data["color"]
                    category.tab_color = icon_data["tab_color"]
                    category.description = (
                        f"Common {display_name} items for moving and transport"
                    )
                    category.save()

                # Create brands and models for this category if they exist
                if category_name in brand_data:
                    for brand_info in brand_data[category_name]:
                        brand_name = brand_info["brand"]
                        brand, created = ItemBrand.objects.get_or_create(
                            name=brand_name,
                            category=category,
                            defaults={
                                "description": f"{brand_name} {display_name} brand",
                                "icon": icon_data["icon"],
                                "color": icon_data["color"],
                                "tab_color": icon_data["tab_color"],
                            },
                        )
                        if created:
                            brands_created += 1
                            self.stdout.write(f"  Created brand: {brand_name}")
                        for model_name in brand_info["models"]:
                            model, created = ItemModel.objects.get_or_create(
                                name=model_name,
                                brand=brand,
                                defaults={
                                    "description": f"{brand_name} {model_name}",
                                    "icon": icon_data["icon"],
                                    "color": icon_data["color"],
                                    "tab_color": icon_data["tab_color"],
                                },
                            )
                            if created:
                                models_created += 1

                # Create the generic item types for this category
                for item_data in category_data["items"]:
                    weight = float(item_data.get("weight", 0))
                    needs_disassembly = item_data.get("needs_disassembly", False)
                    fragile = item_data.get("fragile", False)

                    # Look up the service category for this item
                    service_category_name = category_to_service.get(category_name)
                    service_category_obj = None
                    if service_category_name:
                        try:
                            service_category_obj = ServiceCategory.objects.get(
                                name=service_category_name
                            )
                        except ServiceCategory.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(  # type: ignore
                                    f"ServiceCategory '{service_category_name}' not found for item category '{category_name}'. Leaving blank."
                                )
                            )

                    # Create the generic item (without specific brand/model)
                    item_type, created = CommonItem.objects.get_or_create(
                        name=item_data["name"],
                        category=category,
                        brand=None,  # Generic item
                        model=None,  # Generic item
                        defaults={
                            "dimensions": item_data.get("dimensions", {}),
                            "weight": weight,
                            "needs_disassembly": needs_disassembly,
                            "fragile": fragile,
                            "service_category": service_category_obj,
                            "description": f"Generic {item_data['name']} for {display_name} category",
                        },
                    )
                    if created:
                        items_created += 1
                        self.stdout.write(f"    Created item: {item_data['name']}")

                    # If this category has brands, create a few specific brand/model items as examples
                    if category_name in brand_data:
                        for brand_info in brand_data[category_name][
                            :3
                        ]:  # Limit to first 3 brands
                            brand = ItemBrand.objects.get(
                                name=brand_info["brand"], category=category
                            )
                            for model_name in brand_info["models"][
                                :2
                            ]:  # Limit to first 2 models
                                model = ItemModel.objects.get(
                                    name=model_name, brand=brand
                                )
                                specific_item_name = f"{item_data['name']} - {brand_info['brand']} {model_name}"
                                specific_item, created = (
                                    CommonItem.objects.get_or_create(
                                        name=specific_item_name,
                                        category=category,
                                        brand=brand,
                                        model=model,
                                        defaults={
                                            "dimensions": item_data.get(
                                                "dimensions", {}
                                            ),
                                            "weight": weight,
                                            "needs_disassembly": needs_disassembly,
                                            "fragile": fragile,
                                            "service_category": service_category_obj,
                                            "description": f"{brand_info['brand']} {model_name} {item_data['name']}",
                                        },
                                    )
                                )
                                if created:
                                    items_created += 1

            self.stdout.write(
                self.style.SUCCESS(  # type: ignore
                    f"\nSuccessfully imported:"
                    f"\n  {categories_created} categories"
                    f"\n  {brands_created} brands"
                    f"\n  {models_created} models"
                    f"\n  {items_created} items"
                )
            )
