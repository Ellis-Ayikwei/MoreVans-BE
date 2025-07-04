# Generated by Django 5.2.4 on 2025-07-04 18:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Bidding', '0003_initial'),
        ('Contract', '0001_initial'),
        ('Request', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contractagreement',
            name='logistics_request',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='Request.request'),
        ),
        migrations.AddField(
            model_name='contractagreement',
            name='selected_bid',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='Bidding.bid'),
        ),
    ]
