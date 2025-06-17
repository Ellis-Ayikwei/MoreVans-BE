from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json
from .models import Request, MoveMilestone


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = (
        "tracking_number",
        "user_email",
        "request_type",
        "status_badge",
        "priority",
        "service_level",
        "base_price_display",
        "pickup_date_display",
        "created_at",
    )

    list_filter = (
        "status",
        "request_type",
        "priority",
        "service_level",
        "payment_status",
        "insurance_required",
        "requires_special_handling",
        "created_at",
        "preferred_pickup_date",
    )

    search_fields = (
        "tracking_number",
        "booking_code",
        "user__email",
        "user__first_name",
        "user__last_name",
        "contact_name",
        "contact_email",
        "contact_phone",
        "items_description",
    )

    readonly_fields = (
        "tracking_number",
        "created_at",
        "updated_at",
        "id",
        "price_breakdown_display",
        "locations_display",
        "items_count",
        "estimated_completion_time",
    )

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    save_on_top = True

    actions = [
        "mark_as_pending",
        "mark_as_accepted",
        "mark_as_completed",
        "cancel_requests",
    ]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    ("tracking_number", "booking_code"),
                    ("user", "driver", "provider"),
                    ("request_type", "status", "priority"),
                    ("service_level", "service_type"),
                    "id",
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    ("contact_name", "contact_email"),
                    "contact_phone",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Location Details",
            {
                "fields": (
                    ("pickup_location", "dropoff_location"),
                    "locations_display",
                    "route_waypoints",
                    "estimated_distance",
                    "route_optimization_data",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Schedule & Timing",
            {
                "fields": (
                    ("preferred_pickup_date", "preferred_pickup_time"),
                    ("preferred_delivery_date", "preferred_delivery_time"),
                    "preferred_pickup_time_window",
                    ("is_flexible", "estimated_completion_time"),
                    ("loading_time", "unloading_time"),
                )
            },
        ),
        (
            "Cargo & Items",
            {
                "fields": (
                    "items_description",
                    ("total_weight", "items_count"),
                    "dimensions",
                    "moving_items",
                    ("requires_special_handling", "staff_required"),
                    "special_instructions",
                    "photo_urls",
                )
            },
        ),
        (
            "Pricing & Payment",
            {
                "fields": (
                    ("base_price", "final_price"),
                    "price_breakdown_display",
                    "price_factors",
                    "payment_status",
                )
            },
        ),
        (
            "Insurance & Protection",
            {
                "fields": (
                    ("insurance_required", "insurance_value"),
                    ("cancellation_reason", "cancellation_time"),
                    "cancellation_fee",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Environmental & Analytics",
            {
                "fields": (
                    ("estimated_fuel_consumption", "carbon_footprint"),
                    "weather_conditions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def user_email(self, obj):
        """Display user email"""
        if obj.user:
            return obj.user.email
        return "-"

    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"  # Allows sorting

    def status_badge(self, obj):
        """Display status with color coding"""
        color_map = {
            "draft": "#6c757d",
            "pending": "#ffc107",
            "bidding": "#17a2b8",
            "accepted": "#28a745",
            "assigned": "#007bff",
            "in_transit": "#fd7e14",
            "completed": "#28a745",
            "cancelled": "#dc3545",
        }
        color = color_map.get(obj.status, "#6c757d")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def base_price_display(self, obj):
        """Display base price with currency"""
        if obj.base_price:
            return f"£{obj.base_price:.2f}"
        return "-"

    base_price_display.short_description = "Base Price"

    def pickup_date_display(self, obj):
        """Display pickup date and time"""
        if obj.preferred_pickup_date:
            date_str = obj.preferred_pickup_date.strftime("%d/%m/%Y")
            if obj.preferred_pickup_time:
                return f"{date_str} ({obj.get_preferred_pickup_time_display()})"
            return date_str
        return "-"

    pickup_date_display.short_description = "Pickup Date"

    def price_breakdown_display(self, obj):
        """Display price breakdown in a readable format"""
        if obj.price_breakdown:
            try:
                breakdown = (
                    json.loads(obj.price_breakdown)
                    if isinstance(obj.price_breakdown, str)
                    else obj.price_breakdown
                )
                html = "<table style='border-collapse: collapse; width: 100%;'>"
                for key, value in breakdown.items():
                    html += f"<tr><td style='border: 1px solid #ddd; padding: 5px;'>{key.replace('_', ' ').title()}</td>"
                    html += f"<td style='border: 1px solid #ddd; padding: 5px; text-align: right;'>£{value:.2f}</td></tr>"
                html += "</table>"
                return mark_safe(html)
            except:
                return str(obj.price_breakdown)
        return "-"

    price_breakdown_display.short_description = "Price Breakdown"

    def locations_display(self, obj):
        """Display pickup and dropoff locations"""
        locations = []
        if obj.pickup_location:
            locations.append(f"<strong>Pickup:</strong> {obj.pickup_location}")
        if obj.dropoff_location:
            locations.append(f"<strong>Dropoff:</strong> {obj.dropoff_location}")

        # Also show journey stops if any
        journey_stops = obj.get_journey_stops()
        if journey_stops:
            stops_info = []
            for stop in journey_stops:
                stops_info.append(f"Stop {stop.sequence}: {stop.location}")
            locations.append(
                f"<strong>Journey Stops:</strong><br>{'<br>'.join(stops_info)}"
            )

        return mark_safe("<br>".join(locations)) if locations else "-"

    locations_display.short_description = "Locations"

    def items_count(self, obj):
        """Display total item count"""
        return obj.get_total_item_count()

    items_count.short_description = "Items Count"

    # Admin Actions
    def mark_as_pending(self, request, queryset):
        """Mark selected requests as pending"""
        updated = queryset.update(status="pending")
        self.message_user(request, f"{updated} request(s) marked as pending.")

    mark_as_pending.short_description = "Mark selected requests as pending"

    def mark_as_accepted(self, request, queryset):
        """Mark selected requests as accepted"""
        updated = queryset.update(status="accepted")
        self.message_user(request, f"{updated} request(s) marked as accepted.")

    mark_as_accepted.short_description = "Mark selected requests as accepted"

    def mark_as_completed(self, request, queryset):
        """Mark selected requests as completed"""
        updated = queryset.update(status="completed")
        self.message_user(request, f"{updated} request(s) marked as completed.")

    mark_as_completed.short_description = "Mark selected requests as completed"

    def cancel_requests(self, request, queryset):
        """Cancel selected requests"""
        updated = queryset.update(
            status="cancelled", cancellation_reason="Cancelled by admin"
        )
        self.message_user(request, f"{updated} request(s) cancelled.")

    cancel_requests.short_description = "Cancel selected requests"

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "user", "driver", "provider", "pickup_location", "dropoff_location"
            )
            .prefetch_related("stops")
        )


@admin.register(MoveMilestone)
class MoveMilestoneAdmin(admin.ModelAdmin):
    list_display = (
        "request_tracking",
        "milestone_type",
        "status_badge",
        "sequence",
        "scheduled_start",
        "actual_duration_display",
    )

    list_filter = (
        "milestone_type",
        "status",
        "scheduled_start",
        "actual_start",
    )

    search_fields = (
        "request__tracking_number",
        "notes",
        "delay_reason",
    )

    ordering = ("request", "sequence")

    readonly_fields = ("created_at", "updated_at", "actual_duration")

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    ("request", "milestone_type"),
                    ("status", "sequence"),
                )
            },
        ),
        (
            "Timing",
            {
                "fields": (
                    ("estimated_duration", "actual_duration"),
                    ("scheduled_start", "actual_start", "actual_end"),
                )
            },
        ),
        (
            "Notes & Issues",
            {
                "fields": (
                    "notes",
                    "delay_reason",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def request_tracking(self, obj):
        """Display request tracking number"""
        return obj.request.tracking_number or "New Request"

    request_tracking.short_description = "Request"
    request_tracking.admin_order_field = "request__tracking_number"

    def status_badge(self, obj):
        """Display status with color coding"""
        color_map = {
            "pending": "#ffc107",
            "in_progress": "#17a2b8",
            "completed": "#28a745",
            "delayed": "#dc3545",
        }
        color = color_map.get(obj.status, "#6c757d")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def actual_duration_display(self, obj):
        """Display actual duration in human-readable format"""
        if obj.actual_duration:
            total_seconds = int(obj.actual_duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        return "-"

    actual_duration_display.short_description = "Actual Duration"
