# from django.contrib import admin
# from .models import Job


# @admin.register(Job)
# class JobAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "request",
#         "driver",
#         "status",
#         "scheduled_pickup",
#         "created_at",
#     )
#     list_filter = ("status", "created_at", "scheduled_pickup")
#     search_fields = (
#         "request__tracking_number",
#         "driver__user__email",
#         "driver__user__first_name",
#     )
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("-created_at",)

#     fieldsets = (
#         ("Job Information", {"fields": ("request", "driver", "status")}),
#         (
#             "Schedule",
#             {
#                 "fields": (
#                     "scheduled_pickup",
#                     "scheduled_delivery",
#                     "actual_pickup",
#                     "actual_delivery",
#                 )
#             },
#         ),
#         (
#             "Timestamps",
#             {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
#         ),
#     )
