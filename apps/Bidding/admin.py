# from django.contrib import admin
# from .models import Bid


# @admin.register(Bid)
# class BidAdmin(admin.ModelAdmin):
#     list_display = ("request", "provider", "amount", "status", "created_at")
#     list_filter = ("status", "created_at")
#     search_fields = (
#         "request__tracking_number",
#         "provider__company_name",
#         "provider__user__email",
#     )
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("-created_at",)

#     fieldsets = (
#         (
#             "Bid Information",
#             {"fields": ("request", "provider", "amount", "currency", "status")},
#         ),
#         (
#             "Details",
#             {"fields": ("description", "estimated_pickup", "estimated_delivery")},
#         ),
#         (
#             "Timestamps",
#             {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
#         ),
#     )
