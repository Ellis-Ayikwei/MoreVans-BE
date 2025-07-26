# Generated manually for OTP system

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
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
                ('code', models.CharField(max_length=6)),
                ('otp_type', models.CharField(choices=[('signup_verification', 'Signup Verification'), ('login_verification', 'Login Verification'), ('password_reset', 'Password Reset'), ('email_change', 'Email Change')], max_length=20)),
                ('email', models.EmailField(max_length=254)),
                ('is_used', models.BooleanField(default=False)),
                ('is_verified', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otps', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='LoginAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('ip_address', models.GenericIPAddressField()),
                ('attempt_time', models.DateTimeField(auto_now_add=True)),
                ('is_successful', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-attempt_time'],
            },
        ),
        migrations.AddIndex(
            model_name='otp',
            index=models.Index(fields=['code', 'otp_type'], name='Authenticat_code_7c1234_idx'),
        ),
        migrations.AddIndex(
            model_name='otp',
            index=models.Index(fields=['user', 'is_used'], name='Authenticat_user_id_5a6789_idx'),
        ),
        migrations.AddIndex(
            model_name='otp',
            index=models.Index(fields=['expires_at'], name='Authenticat_expires_1b2345_idx'),
        ),
        migrations.AddIndex(
            model_name='loginattempt',
            index=models.Index(fields=['email', 'attempt_time'], name='Authenticat_email_3c4567_idx'),
        ),
        migrations.AddIndex(
            model_name='loginattempt',
            index=models.Index(fields=['ip_address', 'attempt_time'], name='Authenticat_ip_addr_4d5678_idx'),
        ),
    ]