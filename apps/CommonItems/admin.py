from django.contrib import admin
from .models import (
    CommonItem,
    ItemCategory,
    ItemBrand,
    ItemModel,
)

# @admin.register(CommonItem)
# class CommonItemAdmin(admin.ModelAdmin):
#     list_display = ('name', 'category', 'weight', 'dimensions', 'is_active')
#     list_filter = ('category', 'is_active', 'created_at')
#     search_fields = ('name', 'description', 'category__name')
#     readonly_fields = ('created_at', 'updated_at')

#     fieldsets = (
#         ('Item Information', {
#             'fields': ('name', 'description', 'category')
#         }),
#         ('Physical Properties', {
#             'fields': ('weight', 'dimensions', 'fragile', 'hazardous')
#         }),
#         ('Status', {
#             'fields': ('is_active',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )

# @admin.register(ItemCategory)
# class ItemCategoryAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description', 'is_active')
#     list_filter = ('is_active',)
#     search_fields = ('name', 'description')
