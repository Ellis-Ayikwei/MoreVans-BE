# Generated migration to create OTP and UserVerification models

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("Authentication", "0003_restore_otp_model"),
    ]

    operations = [
        # Drop the existing OTP table if it exists (from previous migration)
        migrations.RunSQL(
            "DROP TABLE IF EXISTS otps CASCADE;", reverse_sql="-- No reverse SQL needed"
        ),
        # Create OTP model with proper BaseModel inheritance
        migrations.CreateModel(
            name="OTP",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now=True, editable=False, null=False),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, editable=False, null=False),
                ),
                ("otp_code", models.CharField(max_length=6)),
                (
                    "otp_type",
                    models.CharField(
                        choices=[
                            ("signup", "Sign Up Verification"),
                            ("login", "Login Authentication"),
                            ("password_reset", "Password Reset"),
                            ("email_change", "Email Change"),
                            ("phone_change", "Phone Change"),
                        ],
                        max_length=20,
                    ),
                ),
                ("is_used", models.BooleanField(default=False)),
                ("expires_at", models.DateTimeField()),
                ("attempts", models.IntegerField(default=0)),
                ("max_attempts", models.IntegerField(default=3)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="otps",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "otps",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["user", "otp_type", "is_used"],
                        name="otps_user_id_otp_typ_is_used_idx",
                    ),
                    models.Index(
                        fields=["otp_code", "expires_at"],
                        name="otps_otp_cod_expires_idx",
                    ),
                ],
            },
        ),
        # Create UserVerification model
        migrations.CreateModel(
            name="UserVerification",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now=True, editable=False, null=False),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, editable=False, null=False),
                ),
                ("email_verified", models.BooleanField(default=False)),
                ("phone_verified", models.BooleanField(default=False)),
                ("email_verified_at", models.DateTimeField(null=True, blank=True)),
                ("phone_verified_at", models.DateTimeField(null=True, blank=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="verification",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "user_verifications",
            },
        ),
    ]
