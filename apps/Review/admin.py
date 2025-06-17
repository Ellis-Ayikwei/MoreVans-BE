# from django.contrib import admin
# from .models import Review

# @admin.register(Review)
# class ReviewAdmin(admin.ModelAdmin):
#     list_display = ('reviewer', 'reviewee', 'rating', 'job', 'created_at')
#     list_filter = ('rating', 'created_at')
#     search_fields = ('reviewer__email', 'reviewee__email', 'job__request__tracking_number')
#     readonly_fields = ('created_at', 'updated_at')
#     ordering = ('-created_at',)

#     fieldsets = (
#         ('Review Information', {
#             'fields': ('reviewer', 'reviewee', 'job', 'rating')
#         }),
#         ('Content', {
#             'fields': ('title', 'comment')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
