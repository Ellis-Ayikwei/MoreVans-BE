# Generated by Django 5.2.4 on 2025-07-13 08:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Job', '0001_initial'),
        ('Provider', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='assigned_provider',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_jobs', to='Provider.serviceprovider'),
        ),
    ]
