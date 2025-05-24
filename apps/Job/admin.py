# from django.contrib import admin
# from .models import Job

# @admin.register(Job)
# class JobAdmin(admin.ModelAdmin):
#     list_display = ('id', 'request', 'status', 'created_at', 'updated_at')
#     list_filter = ('status', 'created_at')
#     search_fields = ('request__tracking_number', 'notes')
#     readonly_fields = ('created_at', 'updated_at')
#     ordering = ('-created_at',)
