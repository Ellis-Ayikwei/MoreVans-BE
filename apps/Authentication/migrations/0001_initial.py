# Generated migration for OTP models

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp_code', models.CharField(max_length=6)),
                ('otp_type', models.CharField(choices=[
                    ('signup', 'Sign Up Verification'),
                    ('login', 'Login Authentication'),
                    ('password_reset', 'Password Reset'),
                    ('email_change', 'Email Change'),
                    ('phone_change', 'Phone Change')
                ], max_length=20)),
                ('is_used', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('attempts', models.IntegerField(default=0)),
                ('max_attempts', models.IntegerField(default=3)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otps', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'otps',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['user', 'otp_type', 'is_used'], name='otps_user_id_otp_typ_is_used_idx'),
                    models.Index(fields=['otp_code', 'expires_at'], name='otps_otp_cod_expires_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='UserVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_verified', models.BooleanField(default=False)),
                ('phone_verified', models.BooleanField(default=False)),
                ('email_verified_at', models.DateTimeField(blank=True, null=True)),
                ('phone_verified_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='verification', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_verifications',
            },
        ),
    ]
