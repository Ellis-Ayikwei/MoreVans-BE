# from django.contrib import admin
# from .models import InsurancePolicy

# @admin.register(InsurancePolicy)
# class InsurancePolicyAdmin(admin.ModelAdmin):
#     list_display = ('policy_number', 'provider', 'coverage_amount', 'is_active', 'expiry_date')
#     list_filter = ('is_active', 'expiry_date', 'created_at')
#     search_fields = ('policy_number', 'provider__company_name')
#     readonly_fields = ('created_at', 'updated_at')
