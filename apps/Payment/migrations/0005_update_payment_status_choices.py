# Generated manually to update payment status choices from "succeeded" to "completed"

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Payment", "0004_update_payment_status_succeeded_to_completed"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("processing", "Processing"),
                    ("completed", "Completed"),
                    ("failed", "Failed"),
                    ("cancelled", "Cancelled"),
                    ("refunded", "Refunded"),
                    ("partially_refunded", "Partially Refunded"),
                ],
                default="pending",
                max_length=30,
            ),
        ),
    ]
