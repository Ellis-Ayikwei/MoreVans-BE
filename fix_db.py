import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(
        "ALTER TABLE common_item ADD COLUMN IF NOT EXISTS model VARCHAR(100) DEFAULT ''"
    )
    print("Model field added successfully!")
