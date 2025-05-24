# from django.contrib import admin
# from django.utils.html import format_html
# from .models import Bid

# @admin.register(Bid)
# class BidAdmin(admin.ModelAdmin):
#     list_display = ('id', 'job', 'provider', 'amount', 'status', 'created_at')
#     list_filter = ('status', 'created_at')
#     search_fields = ('job__request__tracking_number', 'provider__company_name', 'notes')
#     readonly_fields = ('created_at', 'updated_at')
#     ordering = ('-created_at',)
    
#     fieldsets = (
#         ('Bid Details', {
#             'fields': ('job', 'provider', 'amount', 'status')
#         }),
#         ('Timing', {
#             'fields': ('created_at', 'updated_at')
#         }),
#         ('Additional Information', {
#             'fields': ('notes',)
#         }),
#     )
    
#     def request_link(self, obj):
#         """Creates a link to the related request in admin"""
#         url = f"/admin/Request/request/{obj.job.request.id}/change/"
#         return format_html('<a href="{}">{}</a>', url, obj.job.request)
#     request_link.short_description = 'Request'
    
#     def driver_link(self, obj):
#         """Creates a link to the related driver in admin"""
#         url = f"/admin/Driver/driver/{obj.provider.id}/change/"
#         return format_html('<a href="{}">{}</a>', url, obj.provider.name)
#     driver_link.short_description = 'Driver'
