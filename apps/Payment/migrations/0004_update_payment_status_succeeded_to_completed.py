# Generated manually to update payment status from "succeeded" to "completed"

from django.db import migrations


def update_payment_status_succeeded_to_completed(apps, schema_editor):
    """
    Update all payment records with status "succeeded" to "completed"
    """
    Payment = apps.get_model("Payment", "Payment")

    # Update all payments with status "succeeded" to "completed"
    updated_count = Payment.objects.filter(status="succeeded").update(
        status="completed"
    )
    print(f"Updated {updated_count} payments from 'succeeded' to 'completed'")


def reverse_update_payment_status_completed_to_succeeded(apps, schema_editor):
    """
    Reverse migration: update all payment records with status "completed" back to "succeeded"
    """
    Payment = apps.get_model("Payment", "Payment")

    # Update all payments with status "completed" back to "succeeded"
    updated_count = Payment.objects.filter(status="completed").update(
        status="succeeded"
    )
    print(f"Updated {updated_count} payments from 'completed' back to 'succeeded'")


class Migration(migrations.Migration):

    dependencies = [
        ("Payment", "0003_initial"),
    ]

    operations = [
        migrations.RunPython(
            update_payment_status_succeeded_to_completed,
            reverse_update_payment_status_completed_to_succeeded,
        ),
    ]
