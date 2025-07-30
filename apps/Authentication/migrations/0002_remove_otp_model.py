# Generated migration to remove old OTP model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("Authentication", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="OTP",
        ),
    ]
