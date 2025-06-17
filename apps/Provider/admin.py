# from django.contrib import admin
# from .models import ServiceProvider


# @admin.register(ServiceProvider)
# class ProviderAdmin(admin.ModelAdmin):
#     list_display = ("user", "company_name", "is_active", "is_verified", "created_at")
#     list_filter = ("is_active", "is_verified", "created_at")
#     search_fields = ("user__email", "company_name", "business_registration")
#     readonly_fields = ("created_at", "updated_at")

#     fieldsets = (
#         (
#             "Provider Information",
#             {"fields": ("user", "company_name", "business_registration")},
#         ),
#         ("Contact Details", {"fields": ("phone", "address")}),
#         ("Status", {"fields": ("is_active", "is_verified")}),
#         (
#             "Timestamps",
#             {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
#         ),
#     )
