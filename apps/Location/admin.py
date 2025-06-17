# from django.contrib import admin
# from .models import Location

# @admin.register(Location)
# class LocationAdmin(admin.ModelAdmin):
#     list_display = ('name', 'address', 'latitude', 'longitude', 'created_at')
#     list_filter = ('created_at',)
#     search_fields = ('name', 'address', 'city', 'country')
#     readonly_fields = ('created_at', 'updated_at')

#     fieldsets = (
#         ('Location Information', {
#             'fields': ('name', 'address', 'city', 'state', 'country', 'postal_code')
#         }),
#         ('Coordinates', {
#             'fields': ('latitude', 'longitude')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
