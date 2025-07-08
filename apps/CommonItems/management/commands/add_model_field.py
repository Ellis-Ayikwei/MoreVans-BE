from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Add the missing model field to the common_item table"

    def handle(self, *args, **options):
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
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Model column already exists in common_item table"
                        )
                    )
                    return

                # Add the model column
                cursor.execute(
                    """
                    ALTER TABLE common_item 
                    ADD COLUMN model VARCHAR(100) DEFAULT ''
                """
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        "Successfully added model column to common_item table"
                    )
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error adding model column: {e}"))
