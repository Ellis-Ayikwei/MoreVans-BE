# from django.contrib import admin
# from .models import Contract

# @admin.register(Contract)
# class ContractAdmin(admin.ModelAdmin):
#     list_display = ('id', 'request', 'provider', 'status', 'total_amount', 'created_at')
#     list_filter = ('status', 'created_at')
#     search_fields = ('request__tracking_number', 'provider__company_name', 'provider__user__email')
#     readonly_fields = ('created_at', 'updated_at')
#     ordering = ('-created_at',)

#     fieldsets = (
#         ('Contract Information', {
#             'fields': ('request', 'provider', 'status')
#         }),
#         ('Financial Details', {
#             'fields': ('total_amount', 'currency', 'payment_terms')
#         }),
#         ('Contract Terms', {
#             'fields': ('terms_and_conditions', 'start_date', 'end_date')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
