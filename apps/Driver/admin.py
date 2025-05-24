from django.contrib import admin
from django.utils.html import format_html
from .models import Driver, DriverLocation, DriverAvailability, DriverDocument, DriverInfringement

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'provider', 'employment_type', 
                  'license_status', 'cpc_status', 'status', 'penalty_points')
    list_filter = ('status', 'employment_type', 'provider', 'has_cpc', 'has_adr')
    search_fields = ('name', 'email', 'phone_number', 'license_number', 'national_insurance_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'name', 'email', 'phone_number', 'date_of_birth', 
                       'national_insurance_number', 'address', 'postcode')
        }),
        ('Employment Details', {
            'fields': ('provider', 'employment_type', 'date_started')
        }),
        ('License Information', {
            'fields': ('license_number', 'license_country_of_issue', 'license_categories',
                       'license_expiry_date', 'digital_tachograph_card_number', 
                       'tacho_card_expiry_date')
        }),
        ('Qualifications', {
            'fields': ('has_cpc', 'cpc_expiry_date', 'has_adr', 'adr_expiry_date')
        }),
        ('Training & Compliance', {
            'fields': ('induction_completed', 'induction_date')
        }),
        ('Working Time', {
            'fields': ('max_weekly_hours', 'opted_out_of_working_time_directive')
        }),
        ('Driver Status', {
            'fields': ('status', 'penalty_points')
        }),
        ('Preferences', {
            'fields': ('preferred_vehicle_types', 'notes')
        }),
        ('Tracking', {
            'fields': ('location', 'last_location_update')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def license_status(self, obj):
        if obj.is_license_valid:
            return format_html('<span style="color: green;">Valid until {}</span>', obj.license_expiry_date)
        return format_html('<span style="color: red;">Expired</span>')
    license_status.short_description = "License"
    
    def cpc_status(self, obj):
        if not obj.has_cpc:
            return format_html('<span style="color: gray;">N/A</span>')
        if obj.is_cpc_valid:
            return format_html('<span style="color: green;">Valid until {}</span>', obj.cpc_expiry_date)
        return format_html('<span style="color: red;">Expired</span>')
    cpc_status.short_description = "CPC"


@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = ('driver', 'timestamp', 'speed', 'heading', 'accuracy')
    list_filter = ('timestamp',)
    search_fields = ('driver__name',)
    autocomplete_fields = ['driver']
    readonly_fields = ('timestamp',)


@admin.register(DriverAvailability)
class DriverAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('driver', 'date', 'max_jobs')
    list_filter = ('date',)
    search_fields = ('driver__name', 'notes')
    autocomplete_fields = ['driver']


@admin.register(DriverDocument)
class DriverDocumentAdmin(admin.ModelAdmin):
    list_display = ('driver', 'document_type', 'issue_date', 'expiry_date', 'reference_number')
    list_filter = ('document_type', 'issue_date')
    search_fields = ('driver__name', 'reference_number')
    autocomplete_fields = ['driver']
    
    fieldsets = (
        ('Document Details', {
            'fields': ('driver', 'document_type', 'document_file', 'issue_date', 
                      'expiry_date', 'reference_number', 'notes')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DriverInfringement)
class DriverInfringementAdmin(admin.ModelAdmin):
    list_display = ('driver', 'infringement_type', 'infringement_date', 
                   'penalty_points_added', 'fine_amount', 'is_resolved')
    list_filter = ('infringement_type', 'is_resolved', 'infringement_date')
    search_fields = ('driver__name', 'description', 'reported_by')
    autocomplete_fields = ['driver']

    fieldsets = (
        ('Infringement Details', {
            'fields': ('driver', 'infringement_type', 'infringement_date', 
                      'description', 'penalty_points_added', 'fine_amount', 'reported_by')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolution_date', 'resolution_notes')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
