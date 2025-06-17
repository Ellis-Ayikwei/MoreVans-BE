# apps/accounts/admin.py (or your User app's admin.py)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import User, Address, UserActivity


class AddressInline(admin.TabularInline):
    """Inline for managing user addresses"""

    model = Address
    fk_name = "address_user"
    extra = 1
    max_num = 3
    fields = [
        "address_line1",
        "address_line2",
        "city",
        "state",
        "postal_code",
        "country",
        "address_type",
    ]
    verbose_name = "Address"
    verbose_name_plural = "Addresses"


class UserActivityInline(admin.TabularInline):
    """Inline for viewing recent user activities"""

    model = UserActivity
    extra = 0
    max_num = 10
    readonly_fields = ["activity_type", "request_link", "created_at"]
    fields = ["activity_type", "request_link", "created_at"]
    ordering = ["-created_at"]
    verbose_name = "Recent Activity"
    verbose_name_plural = "Recent Activities"

    def request_link(self, obj):
        """Create a clickable link to the related request"""
        if obj.request:
            try:
                app_label = obj.request._meta.app_label
                model_name = obj.request._meta.model_name
                url = reverse(
                    f"admin:{app_label}_{model_name}_change", args=[obj.request.pk]
                )
                display_text = (
                    obj.request.tracking_number or f"Request #{obj.request.pk}"
                )
                return format_html(
                    '<a href="{}" target="_blank">{}</a>', url, display_text
                )
            except:
                return obj.request.tracking_number or f"Request #{obj.request.pk}"
        return "-"

    request_link.short_description = "Request"

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class UserRequestInline(admin.TabularInline):
    """Inline for viewing user requests"""

    from apps.Request.models import Request

    model = Request
    extra = 0
    max_num = 10
    readonly_fields = [
        "request_link",
        "request_type",
        "status",
        "base_price",
        "created_at",
    ]
    fields = ["request_link", "request_type", "status", "base_price", "created_at"]
    ordering = ["-created_at"]
    verbose_name = "Request"
    verbose_name_plural = "User Requests"

    def request_link(self, obj):
        """Create a clickable link to the request admin page"""
        if obj.pk:
            try:
                app_label = obj._meta.app_label
                model_name = obj._meta.model_name
                url = reverse(f"admin:{app_label}_{model_name}_change", args=[obj.pk])
                display_text = obj.tracking_number or f"Request #{obj.pk}"
                return format_html(
                    '<a href="{}" target="_blank">{}</a>', url, display_text
                )
            except:
                return obj.tracking_number or f"Request #{obj.pk}"
        return "New Request"

    request_link.short_description = "Request"

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email",
        "first_name",
        "last_name",
        "user_type_display",
        "admin_status",
        "rating_display",
        "is_active",
        "date_joined",
    ]

    list_filter = [
        "user_type",
        "is_active",
        "is_staff",
        "is_superuser",
        "account_status",
        "date_joined",
    ]

    search_fields = ["email", "first_name", "last_name", "phone_number"]

    ordering = ["email"]

    readonly_fields = ["id", "last_login", "date_joined", "rating"]

    inlines = [
        AddressInline,
        UserRequestInline,
        UserActivityInline,
    ]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "phone_number", "profile_picture")},
        ),
        (
            "User Type & Status",
            {"fields": ("user_type", "account_status", "rating", "last_active")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Payment & Notifications",
            {
                "fields": (
                    "stripe_customer_id",
                    "notification_preferences",
                    "device_tokens",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Important dates",
            {"fields": ("last_login", "date_joined"), "classes": ("collapse",)},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "user_type"),
            },
        ),
    )

    def user_type_display(self, obj):
        """Display user type with color coding"""
        color_map = {
            "admin": "#dc3545",  # Red for admin
            "provider": "#007bff",  # Blue for provider
            "customer": "#28a745",  # Green for customer
        }
        color = color_map.get(obj.user_type, "#6c757d")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_user_type_display(),
        )

    user_type_display.short_description = "User Type"
    user_type_display.admin_order_field = "user_type"

    def admin_status(self, obj):
        """Show admin permissions status"""
        status_parts = []

        if obj.is_superuser:
            status_parts.append(
                '<span style="color: #dc3545; font-weight: bold;">SUPER</span>'
            )
        if obj.is_staff:
            status_parts.append(
                '<span style="color: #fd7e14; font-weight: bold;">STAFF</span>'
            )
        if obj.user_type == "admin":
            status_parts.append(
                '<span style="color: #6f42c1; font-weight: bold;">ADMIN</span>'
            )

        return format_html(" | ".join(status_parts)) if status_parts else "-"

    admin_status.short_description = "Admin Status"

    def rating_display(self, obj):
        """Display rating with stars"""
        if obj.rating:
            stars = "★" * int(obj.rating)
            return format_html(f"{stars} ({obj.rating:.1f})")
        return "-"

    rating_display.short_description = "Rating"

    def get_form(self, request, obj=None, **kwargs):
        """Override form to make fields optional in admin"""
        form = super().get_form(request, obj, **kwargs)

        # Make these fields optional in admin forms
        if "last_name" in form.base_fields:
            form.base_fields["last_name"].required = False
        if "rating" in form.base_fields:
            form.base_fields["rating"].required = False
        if "stripe_customer_id" in form.base_fields:
            form.base_fields["stripe_customer_id"].required = False
        if "notification_preferences" in form.base_fields:
            form.base_fields["notification_preferences"].required = False
        if "device_tokens" in form.base_fields:
            form.base_fields["device_tokens"].required = False
        if "phone_number" in form.base_fields:
            form.base_fields["phone_number"].required = False

        return form


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = [
        "address_user",
        "address_line1",
        "city",
        "postal_code",
        "country",
        "address_type",
    ]

    list_filter = ["address_type", "country", "state"]

    search_fields = ["address_user__email", "address_line1", "city", "postal_code"]


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ["user", "activity_type", "request", "created_at"]

    list_filter = ["activity_type", "created_at"]

    search_fields = ["user__email", "request__tracking_number"]

    readonly_fields = ["created_at", "updated_at"]
