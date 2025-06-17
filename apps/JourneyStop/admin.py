# from django.contrib import admin
# from .models import JourneyStop

# @admin.register(JourneyStop)
# class JourneyStopAdmin(admin.ModelAdmin):
#     list_display = ('request', 'stop_order', 'location', 'stop_type', 'is_completed')
#     list_filter = ('stop_type', 'is_completed', 'created_at')
#     search_fields = ('request__tracking_number', 'location', 'address')
#     readonly_fields = ('created_at', 'updated_at')
#     ordering = ('request', 'stop_order')

#     fieldsets = (
#         ('Stop Information', {
#             'fields': ('request', 'stop_order', 'location', 'address')
#         }),
#         ('Stop Details', {
#             'fields': ('stop_type', 'estimated_arrival', 'actual_arrival', 'departure_time')
#         }),
#         ('Status', {
#             'fields': ('is_completed', 'notes')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
