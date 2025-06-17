from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Driver", "0006_driverdocument_has_two_sides"),
    ]

    operations = [
        migrations.AlterField(
            model_name="driverdocument",
            name="document_front",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="uploads/docs/drivers/%(driver_id)s/%(id)s/",
                max_length=500,
            ),
        ),
        migrations.AlterField(
            model_name="driverdocument",
            name="document_back",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="uploads/docs/drivers/%(driver_id)s/%(id)s/",
                max_length=500,
            ),
        ),
    ]
