from django.contrib import admin
from .models import ServiceCategory, Services


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "description",
        "icon",
        "services_count",
        "created_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "description", "slug")
    readonly_fields = ("slug", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        ("Basic Information", {"fields": ("name", "slug", "description", "icon")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def services_count(self, obj):
        return obj.services.count()

    services_count.short_description = "Services Count"


@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    list_display = ("name", "service_category", "icon", "providers_count", "created_at")
    list_filter = ("service_category", "created_at", "updated_at")
    search_fields = ("name", "description", "service_category__name")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Service Information",
            {"fields": ("name", "description", "service_category", "icon")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def providers_count(self, obj):
        return obj.providers.count()

    providers_count.short_description = "Providers Count"
