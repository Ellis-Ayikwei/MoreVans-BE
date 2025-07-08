#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.db import connection


def add_model_field():
    """Add the missing model field to the common_item table"""
    with connection.cursor() as cursor:
        try:
            # Check if the model column already exists
            cursor.execute(
                """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'common_item' AND column_name = 'model'
            """
            )

            if cursor.fetchone():
                print("Model column already exists in common_item table")
                return

            # Add the model column
            cursor.execute(
                """
                ALTER TABLE common_item 
                ADD COLUMN model VARCHAR(100) DEFAULT ''
            """
            )

            print("Successfully added model column to common_item table")

        except Exception as e:
            print(f"Error adding model column: {e}")


if __name__ == "__main__":
    add_model_field()
