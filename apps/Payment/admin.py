# from django.contrib import admin
# from .models import Payment, PaymentMethod

# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'amount', 'currency', 'status', 'payment_method', 'created_at')
#     list_filter = ('status', 'currency', 'payment_method', 'created_at')
#     search_fields = ('user__email', 'stripe_payment_intent_id', 'transaction_id')
#     readonly_fields = ('stripe_payment_intent_id', 'created_at', 'updated_at')
#     ordering = ('-created_at',)

#     fieldsets = (
#         ('Payment Details', {
#             'fields': ('user', 'amount', 'currency', 'status', 'payment_method')
#         }),
#         ('Stripe Information', {
#             'fields': ('stripe_payment_intent_id', 'stripe_customer_id')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )

# @admin.register(PaymentMethod)
# class PaymentMethodAdmin(admin.ModelAdmin):
#     list_display = ('name', 'is_active', 'created_at')
#     list_filter = ('is_active', 'created_at')
#     search_fields = ('name', 'description')
