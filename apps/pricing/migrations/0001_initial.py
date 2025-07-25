# Generated by Django 5.2.4 on 2025-07-13 08:56

import django.core.validators
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DistancePricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('base_rate_per_km', models.DecimalField(decimal_places=2, max_digits=6, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('min_distance', models.IntegerField(default=0)),
                ('max_distance', models.IntegerField(default=1000)),
                ('base_rate_per_mile', models.DecimalField(decimal_places=2, default=0.0, help_text='Optional: For regions using miles instead of km', max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('additional_distance_threshold', models.IntegerField(default=50, help_text='Distance threshold after which higher rates apply')),
                ('additional_distance_multiplier', models.DecimalField(decimal_places=2, default=1.2, help_text='Multiplier for distances beyond the threshold', max_digits=3, validators=[django.core.validators.MinValueValidator(1.0)])),
            ],
            options={
                'db_table': 'pricing_distance',
            },
        ),
        migrations.CreateModel(
            name='InsurancePricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('base_rate', models.DecimalField(decimal_places=2, max_digits=6, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('value_percentage', models.DecimalField(decimal_places=2, default=0.5, max_digits=4, validators=[django.core.validators.MinValueValidator(0.01), django.core.validators.MaxValueValidator(5.0)])),
                ('min_premium', models.DecimalField(decimal_places=2, max_digits=6, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('premium_coverage_multiplier', models.DecimalField(decimal_places=2, default=2.0, help_text='Multiplier for premium coverage options', max_digits=3, validators=[django.core.validators.MinValueValidator(1.0)])),
                ('high_value_item_threshold', models.DecimalField(decimal_places=2, default=1000.0, help_text='Value threshold for items considered high value', max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('high_value_item_rate', models.DecimalField(decimal_places=2, default=1.0, help_text='Percentage rate for high value items', max_digits=4, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('deductible_amount', models.DecimalField(decimal_places=2, default=100.0, max_digits=8, validators=[django.core.validators.MinValueValidator(0.0)])),
            ],
            options={
                'db_table': 'pricing_insurance',
            },
        ),
        migrations.CreateModel(
            name='LoadingTimePricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('base_rate_per_hour', models.DecimalField(decimal_places=2, max_digits=6, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('min_hours', models.DecimalField(decimal_places=2, default=1.0, max_digits=4, validators=[django.core.validators.MinValueValidator(0.5)])),
                ('overtime_multiplier', models.DecimalField(decimal_places=2, default=1.5, max_digits=3, validators=[django.core.validators.MinValueValidator(1.0)])),
            ],
            options={
                'db_table': 'pricing_loading_time',
            },
        ),
        migrations.CreateModel(
            name='LocationPricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('city_name', models.CharField(max_length=100)),
                ('zone_multiplier', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.8), django.core.validators.MaxValueValidator(3.0)])),
                ('congestion_charge', models.DecimalField(decimal_places=2, default=0.0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('parking_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
            ],
            options={
                'db_table': 'pricing_location',
            },
        ),
        migrations.CreateModel(
            name='PropertyTypePricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('property_type', models.CharField(choices=[('house', 'House'), ('apartment', 'Apartment'), ('office', 'Office'), ('storage', 'Storage'), ('other', 'Other')], max_length=20)),
                ('base_rate', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('rate_per_room', models.DecimalField(decimal_places=2, max_digits=6, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('elevator_discount', models.DecimalField(decimal_places=2, default=0.9, max_digits=3, validators=[django.core.validators.MinValueValidator(0.5), django.core.validators.MaxValueValidator(1.0)])),
                ('floor_rate', models.DecimalField(decimal_places=2, default=10.0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('narrow_access_fee', models.DecimalField(decimal_places=2, default=25.0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('stairs_per_flight_fee', models.DecimalField(decimal_places=2, default=15.0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('rate_per_sq_meter', models.DecimalField(decimal_places=2, default=2.0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('long_carry_distance_fee', models.DecimalField(decimal_places=2, default=30.0, help_text='Fee for carrying items long distances from parking', max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
            ],
            options={
                'db_table': 'pricing_property_type',
            },
        ),
        migrations.CreateModel(
            name='ServiceLevelPricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('service_level', models.CharField(choices=[('standard', 'Standard (2-3 business days)'), ('express', 'Express (1-2 business days)'), ('same_day', 'Same Day Delivery'), ('scheduled', 'Scheduled (Flexible Date)')], max_length=20)),
                ('price_multiplier', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.5)])),
            ],
            options={
                'db_table': 'pricing_service_level',
            },
        ),
        migrations.CreateModel(
            name='SpecialRequirementsPricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('fragile_items_multiplier', models.DecimalField(decimal_places=2, default=1.3, max_digits=3, validators=[django.core.validators.MinValueValidator(1.0)])),
                ('assembly_required_rate', models.DecimalField(decimal_places=2, default=50.0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('special_equipment_rate', models.DecimalField(decimal_places=2, default=75.0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.01)])),
            ],
            options={
                'db_table': 'pricing_special_requirements',
            },
        ),
        migrations.CreateModel(
            name='StaffRequiredPricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('base_rate_per_staff', models.DecimalField(decimal_places=2, max_digits=6, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('min_staff', models.IntegerField(default=1)),
                ('max_staff', models.IntegerField(default=10)),
                ('hourly_rate', models.DecimalField(decimal_places=2, default=25.0, max_digits=8, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('overtime_rate_multiplier', models.DecimalField(decimal_places=2, default=1.5, max_digits=3, validators=[django.core.validators.MinValueValidator(1.0)])),
                ('specialist_staff_multiplier', models.DecimalField(decimal_places=2, default=1.5, help_text='Multiplier for specialized staff (piano movers, art handlers, etc.)', max_digits=3, validators=[django.core.validators.MinValueValidator(1.0)])),
            ],
            options={
                'db_table': 'pricing_staff_required',
            },
        ),
        migrations.CreateModel(
            name='TimePricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('peak_hour_multiplier', models.DecimalField(decimal_places=2, default=1.5, max_digits=3, validators=[django.core.validators.MinValueValidator(1.0)])),
                ('weekend_multiplier', models.DecimalField(decimal_places=2, default=1.3, max_digits=3, validators=[django.core.validators.MinValueValidator(1.0)])),
                ('holiday_multiplier', models.DecimalField(decimal_places=2, default=2.0, max_digits=3, validators=[django.core.validators.MinValueValidator(1.0)])),
            ],
            options={
                'db_table': 'pricing_time',
            },
        ),
        migrations.CreateModel(
            name='VehicleTypePricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('vehicle_type', models.CharField(max_length=50)),
                ('base_rate', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('capacity_multiplier', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(1.0)])),
                ('capacity_cubic_meters', models.DecimalField(decimal_places=2, default=0.0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('capacity_weight_kg', models.DecimalField(decimal_places=2, default=0.0, max_digits=8, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('fuel_efficiency_km_per_liter', models.DecimalField(decimal_places=2, default=8.0, max_digits=5, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('hourly_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('daily_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=8, validators=[django.core.validators.MinValueValidator(0.0)])),
            ],
            options={
                'db_table': 'pricing_vehicle_type',
            },
        ),
        migrations.CreateModel(
            name='WeatherPricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('rain_multiplier', models.DecimalField(decimal_places=2, default=1.2, max_digits=3, validators=[django.core.validators.MinValueValidator(1.0)])),
                ('snow_multiplier', models.DecimalField(decimal_places=2, default=1.5, max_digits=3, validators=[django.core.validators.MinValueValidator(1.0)])),
                ('extreme_weather_multiplier', models.DecimalField(decimal_places=2, default=2.0, max_digits=3, validators=[django.core.validators.MinValueValidator(1.0)])),
            ],
            options={
                'db_table': 'pricing_weather',
            },
        ),
        migrations.CreateModel(
            name='WeightPricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('base_rate_per_kg', models.DecimalField(decimal_places=2, max_digits=6, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('min_weight', models.IntegerField(default=0)),
                ('max_weight', models.IntegerField(default=10000)),
                ('base_rate_per_lb', models.DecimalField(decimal_places=2, default=0.0, help_text='Optional: For regions using pounds instead of kg', max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('volume_to_weight_ratio', models.DecimalField(decimal_places=2, default=167.0, help_text='Cubic cm to kg conversion ratio (volumetric weight)', max_digits=6, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('heavy_item_threshold', models.IntegerField(default=50, help_text='Weight threshold for items considered heavy')),
                ('heavy_item_surcharge', models.DecimalField(decimal_places=2, default=25.0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
            ],
            options={
                'db_table': 'pricing_weight',
            },
        ),
        migrations.CreateModel(
            name='ConfigDistanceFactor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(10.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('factor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.distancepricing')),
            ],
            options={
                'db_table': 'pricing_config_distance_factor',
                'ordering': ['priority'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ConfigInsuranceFactor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(10.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('factor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.insurancepricing')),
            ],
            options={
                'db_table': 'pricing_config_insurance_factor',
                'ordering': ['priority'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ConfigLoadingTimeFactor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(10.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('factor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.loadingtimepricing')),
            ],
            options={
                'db_table': 'pricing_config_loading_time_factor',
                'ordering': ['priority'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ConfigLocationFactor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(10.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('factor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.locationpricing')),
            ],
            options={
                'db_table': 'pricing_config_location_factor',
                'ordering': ['priority'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PricingConfiguration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('base_price', models.DecimalField(decimal_places=2, default=50.0, max_digits=8, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('min_price', models.DecimalField(decimal_places=2, default=30.0, max_digits=8, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('max_price_multiplier', models.DecimalField(decimal_places=2, help_text='Maximum multiplier for the base price', max_digits=7, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('fuel_surcharge_percentage', models.DecimalField(decimal_places=2, default=0.0, help_text='Fuel surcharge as percentage of total price', max_digits=6, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)])),
                ('carbon_offset_rate', models.DecimalField(decimal_places=2, default=0.0, help_text='Carbon offset rate as percentage of total price', max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('active_factors', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('distance_factors', models.ManyToManyField(blank=True, related_name='configurations', through='pricing.ConfigDistanceFactor', to='pricing.distancepricing')),
                ('insurance_factors', models.ManyToManyField(blank=True, related_name='configurations', through='pricing.ConfigInsuranceFactor', to='pricing.insurancepricing')),
                ('loading_time_factors', models.ManyToManyField(blank=True, related_name='configurations', through='pricing.ConfigLoadingTimeFactor', to='pricing.loadingtimepricing')),
                ('location_factors', models.ManyToManyField(blank=True, related_name='configurations', through='pricing.ConfigLocationFactor', to='pricing.locationpricing')),
            ],
            options={
                'db_table': 'pricing_configuration',
                'ordering': ['-created_at'],
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='ConfigWeightFactor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(10.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingconfiguration')),
                ('factor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.weightpricing')),
            ],
            options={
                'db_table': 'pricing_config_weight_factor',
                'ordering': ['priority'],
                'abstract': False,
                'unique_together': {('configuration', 'factor')},
            },
        ),
        migrations.CreateModel(
            name='ConfigWeatherFactor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(10.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingconfiguration')),
                ('factor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.weatherpricing')),
            ],
            options={
                'db_table': 'pricing_config_weather_factor',
                'ordering': ['priority'],
                'abstract': False,
                'unique_together': {('configuration', 'factor')},
            },
        ),
        migrations.CreateModel(
            name='ConfigVehicleFactor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(10.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingconfiguration')),
                ('factor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.vehicletypepricing')),
            ],
            options={
                'db_table': 'pricing_config_vehicle_factor',
                'ordering': ['priority'],
                'abstract': False,
                'unique_together': {('configuration', 'factor')},
            },
        ),
        migrations.CreateModel(
            name='ConfigTimeFactor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(10.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingconfiguration')),
                ('factor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.timepricing')),
            ],
            options={
                'db_table': 'pricing_config_time_factor',
                'ordering': ['priority'],
                'abstract': False,
                'unique_together': {('configuration', 'factor')},
            },
        ),
        migrations.CreateModel(
            name='ConfigStaffFactor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(10.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingconfiguration')),
                ('factor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.staffrequiredpricing')),
            ],
            options={
                'db_table': 'pricing_config_staff_factor',
                'ordering': ['priority'],
                'abstract': False,
                'unique_together': {('configuration', 'factor')},
            },
        ),
        migrations.CreateModel(
            name='ConfigSpecialRequirementsFactor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(10.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingconfiguration')),
                ('factor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.specialrequirementspricing')),
            ],
            options={
                'db_table': 'pricing_config_special_requirements_factor',
                'ordering': ['priority'],
                'abstract': False,
                'unique_together': {('configuration', 'factor')},
            },
        ),
        migrations.CreateModel(
            name='ConfigServiceLevelFactor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(10.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingconfiguration')),
                ('factor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.servicelevelpricing')),
            ],
            options={
                'db_table': 'pricing_config_service_level_factor',
                'ordering': ['priority'],
                'abstract': False,
                'unique_together': {('configuration', 'factor')},
            },
        ),
        migrations.CreateModel(
            name='ConfigPropertyTypeFactor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(10.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingconfiguration')),
                ('factor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.propertytypepricing')),
            ],
            options={
                'db_table': 'pricing_config_property_type_factor',
                'ordering': ['priority'],
                'abstract': False,
                'unique_together': {('configuration', 'factor')},
            },
        ),
        migrations.AddField(
            model_name='configlocationfactor',
            name='configuration',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingconfiguration'),
        ),
        migrations.AddField(
            model_name='configloadingtimefactor',
            name='configuration',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingconfiguration'),
        ),
        migrations.AddField(
            model_name='configinsurancefactor',
            name='configuration',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingconfiguration'),
        ),
        migrations.AddField(
            model_name='configdistancefactor',
            name='configuration',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingconfiguration'),
        ),
        migrations.AddField(
            model_name='pricingconfiguration',
            name='property_type_factors',
            field=models.ManyToManyField(blank=True, related_name='configurations', through='pricing.ConfigPropertyTypeFactor', to='pricing.propertytypepricing'),
        ),
        migrations.AddField(
            model_name='pricingconfiguration',
            name='service_level_factors',
            field=models.ManyToManyField(blank=True, related_name='configurations', through='pricing.ConfigServiceLevelFactor', to='pricing.servicelevelpricing'),
        ),
        migrations.AddField(
            model_name='pricingconfiguration',
            name='special_requirement_factors',
            field=models.ManyToManyField(blank=True, related_name='configurations', through='pricing.ConfigSpecialRequirementsFactor', to='pricing.specialrequirementspricing'),
        ),
        migrations.AddField(
            model_name='pricingconfiguration',
            name='staff_factors',
            field=models.ManyToManyField(blank=True, related_name='configurations', through='pricing.ConfigStaffFactor', to='pricing.staffrequiredpricing'),
        ),
        migrations.AddField(
            model_name='pricingconfiguration',
            name='time_factors',
            field=models.ManyToManyField(blank=True, related_name='configurations', through='pricing.ConfigTimeFactor', to='pricing.timepricing'),
        ),
        migrations.AddField(
            model_name='pricingconfiguration',
            name='vehicle_factors',
            field=models.ManyToManyField(blank=True, related_name='configurations', through='pricing.ConfigVehicleFactor', to='pricing.vehicletypepricing'),
        ),
        migrations.AddField(
            model_name='pricingconfiguration',
            name='weather_factors',
            field=models.ManyToManyField(blank=True, related_name='configurations', through='pricing.ConfigWeatherFactor', to='pricing.weatherpricing'),
        ),
        migrations.AddField(
            model_name='pricingconfiguration',
            name='weight_factors',
            field=models.ManyToManyField(blank=True, related_name='configurations', through='pricing.ConfigWeightFactor', to='pricing.weightpricing'),
        ),
        migrations.AlterUniqueTogether(
            name='configlocationfactor',
            unique_together={('configuration', 'factor')},
        ),
        migrations.AlterUniqueTogether(
            name='configloadingtimefactor',
            unique_together={('configuration', 'factor')},
        ),
        migrations.AlterUniqueTogether(
            name='configinsurancefactor',
            unique_together={('configuration', 'factor')},
        ),
        migrations.AlterUniqueTogether(
            name='configdistancefactor',
            unique_together={('configuration', 'factor')},
        ),
    ]
