# from django.contrib import admin
# from .models import Notification

# @admin.register(Notification)
# class NotificationAdmin(admin.ModelAdmin):
#     list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
#     list_filter = ('notification_type', 'is_read', 'created_at')
#     search_fields = ('user__email', 'title', 'message')
#     readonly_fields = ('created_at', 'updated_at')
#     ordering = ('-created_at',)

#     fieldsets = (
#         ('Notification Details', {
#             'fields': ('user', 'title', 'message', 'notification_type')
#         }),
#         ('Status', {
#             'fields': ('is_read', 'read_at')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
