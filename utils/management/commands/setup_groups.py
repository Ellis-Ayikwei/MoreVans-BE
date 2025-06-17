# apps/accounts/management/commands/setup_groups.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.User.models import User


class Command(BaseCommand):
    help = "Create default groups and permissions"

    def handle(self, *args, **options):
        # Create groups
        admin_group, created = Group.objects.get_or_create(name="Administrators")
        provider_group, created = Group.objects.get_or_create(name="Service Providers")
        customer_group, created = Group.objects.get_or_create(name="Customers")

        # Get content types
        user_ct = ContentType.objects.get_for_model(User)

        # Assign permissions to groups
        # Administrators - full access
        admin_permissions = Permission.objects.filter(content_type__in=[user_ct])
        admin_group.permissions.set(admin_permissions)

        # Service Providers - limited access
        provider_permissions = Permission.objects.filter(
            content_type=user_ct,
            codename__in=["view_user", "change_user"],  # Only view and change
        )
        provider_group.permissions.set(provider_permissions)

        # Customers - minimal access
        customer_permissions = Permission.objects.filter(
            content_type=user_ct, codename="view_user"  # Only view
        )
        customer_group.permissions.set(customer_permissions)

        self.stdout.write(
            self.style.SUCCESS("Successfully created groups and permissions")
        )
