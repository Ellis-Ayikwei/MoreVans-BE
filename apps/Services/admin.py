# from django.contrib import admin
# from .models import Service, ServiceCategory

# @admin.register(Service)
# class ServiceAdmin(admin.ModelAdmin):
#     list_display = ('name', 'category', 'price', 'is_active', 'created_at')
#     list_filter = ('category', 'is_active', 'created_at')
#     search_fields = ('name', 'description', 'category__name')
#     readonly_fields = ('created_at', 'updated_at')

#     fieldsets = (
#         ('Service Information', {
#             'fields': ('name', 'description', 'category')
#         }),
#         ('Pricing', {
#             'fields': ('price', 'currency', 'pricing_type')
#         }),
#         ('Status', {
#             'fields': ('is_active',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )

# @admin.register(ServiceCategory)
# class ServiceCategoryAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description', 'is_active')
#     list_filter = ('is_active',)
#     search_fields = ('name', 'description')
