# from django.contrib import admin
# from .models import RequestItem

# @admin.register(RequestItem)
# class RequestItemAdmin(admin.ModelAdmin):
#     list_display = ('request', 'item', 'quantity', 'weight', 'created_at')
#     list_filter = ('created_at', 'item__category')
#     search_fields = ('request__tracking_number', 'item__name', 'description')
#     readonly_fields = ('created_at', 'updated_at')

#     fieldsets = (
#         ('Request Item Information', {
#             'fields': ('request', 'item', 'quantity', 'weight')
#         }),
#         ('Details', {
#             'fields': ('description', 'special_instructions')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
