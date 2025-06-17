# from django.contrib import admin
# from .models import TrackingStatus, TrackingHistory

# @admin.register(TrackingStatus)
# class TrackingStatusAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description', 'is_active')
#     list_filter = ('is_active',)
#     search_fields = ('name', 'description')

# @admin.register(TrackingHistory)
# class TrackingHistoryAdmin(admin.ModelAdmin):
#     list_display = ('request', 'status', 'location', 'timestamp', 'created_at')
#     list_filter = ('status', 'timestamp', 'created_at')
#     search_fields = ('request__tracking_number', 'location', 'notes')
#     readonly_fields = ('created_at', 'updated_at')
#     ordering = ('-timestamp',)

#     fieldsets = (
#         ('Tracking Information', {
#             'fields': ('request', 'status', 'location', 'timestamp')
#         }),
#         ('Details', {
#             'fields': ('notes', 'coordinates')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
