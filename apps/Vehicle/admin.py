from django.contrib import admin
from django.utils.html import format_html
from .models import Vehicle, VehicleDocument, VehicleInspection, MaintenanceRecord

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('registration', 'make_model_display', 'vehicle_type_display', 
                   'provider', 'primary_driver', 'is_active', 'mot_status', 'tax_status')
    list_filter = ('vehicle_type', 'fuel_type', 'is_active', 'provider')
    search_fields = ('registration', 'vin', 'make', 'model', 'fleet_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Vehicle Identity', {
            'fields': ('registration', 'vin', 'fleet_number')
        }),
        ('Vehicle Details', {
            'fields': ('make', 'model', 'year', 'vehicle_type', 'fuel_type', 
                      'transmission', 'color')
        }),
        ('Capacity', {
            'fields': ('payload_capacity_kg', 'gross_vehicle_weight_kg', 
                      'load_length_mm', 'load_width_mm', 'load_height_mm', 
                      'load_volume_m3')
        }),
        ('Compliance', {
            'fields': ('mot_expiry_date', 'road_tax_expiry_date', 'has_tachograph',
                      'ulez_compliant', 'clean_air_zone_status')
        }),
        ('Insurance & Documentation', {
            'fields': ('insurance_policy_number', 'insurance_expiry_date')
        }),
        ('Service & Maintenance', {
            'fields': ('last_service_date', 'next_service_date', 
                      'last_service_mileage', 'current_mileage',
                      'service_interval_months', 'service_interval_miles')
        }),
        ('Features', {
            'fields': ('has_tail_lift', 'has_refrigeration', 
                      'has_tracking_device', 'has_dash_cam', 'additional_features')
        }),
        ('Ownership & Assignment', {
            'fields': ('provider', 'primary_driver', 'is_active', 'is_available')
        }),
        ('Tracking', {
            'fields': ('location', 'last_location_update')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def make_model_display(self, obj):
        return f"{obj.make} {obj.model} ({obj.year})"
    make_model_display.short_description = "Vehicle"
    
    def vehicle_type_display(self, obj):
        return obj.get_vehicle_type_display()
    vehicle_type_display.short_description = "Type"
    
    def mot_status(self, obj):
        if obj.is_mot_valid:
            return format_html('<span style="color: green;">Valid until {}</span>', obj.mot_expiry_date)
        return format_html('<span style="color: red;">Expired</span>')
    mot_status.short_description = "MOT"
    
    def tax_status(self, obj):
        if obj.is_road_tax_valid:
            return format_html('<span style="color: green;">Valid until {}</span>', obj.road_tax_expiry_date)
        return format_html('<span style="color: red;">Expired</span>')
    tax_status.short_description = "Road Tax"


@admin.register(VehicleDocument)
class VehicleDocumentAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'document_type', 'issue_date', 'expiry_date', 'reference_number')
    list_filter = ('document_type', 'issue_date')
    search_fields = ('vehicle__registration', 'reference_number')
    autocomplete_fields = ['vehicle']
    
    fieldsets = (
        ('Document Details', {
            'fields': ('vehicle', 'document_type', 'document_file', 'issue_date', 
                      'expiry_date', 'reference_number', 'notes')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(VehicleInspection)
class VehicleInspectionAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'inspection_type', 'inspection_date', 
                   'inspector_name', 'overall_condition', 'is_roadworthy')
    list_filter = ('inspection_type', 'overall_condition', 'is_roadworthy', 'inspection_date')
    search_fields = ('vehicle__registration', 'inspector_name', 'defects_found')
    autocomplete_fields = ['vehicle']

    fieldsets = (
        ('Inspection Details', {
            'fields': ('vehicle', 'inspection_type', 'inspection_date', 
                      'inspector_name', 'mileage_at_inspection')
        }),
        ('Condition', {
            'fields': ('overall_condition', 'inspection_items', 
                      'defects_found', 'actions_required', 'is_roadworthy')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'maintenance_type', 'maintenance_date', 
                   'mileage', 'performed_by', 'cost')
    list_filter = ('maintenance_type', 'maintenance_date')
    search_fields = ('vehicle__registration', 'performed_by', 'work_performed', 'invoice_reference')
    autocomplete_fields = ['vehicle']

    fieldsets = (
        ('Maintenance Details', {
            'fields': ('vehicle', 'maintenance_type', 'maintenance_date', 
                      'mileage', 'performed_by')
        }),
        ('Work Details', {
            'fields': ('work_performed', 'parts_replaced', 'cost', 'invoice_reference')
        }),
        ('Next Maintenance', {
            'fields': ('next_maintenance_date', 'next_maintenance_mileage', 'notes')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
