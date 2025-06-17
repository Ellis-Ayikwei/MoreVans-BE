from django.db import models
from apps.Basemodel.models import Basemodel
from apps.Request.models import Request
from apps.Location.models import Location


class JourneyStop(Basemodel):
    """A stop in a journey request"""

    TYPE_CHOICES = [
        ("pickup", "Pickup"),
        ("dropoff", "Dropoff"),
        ("stop", "Intermediate Stop"),
    ]

    SERVICE_TYPE_CHOICES = [
        ("residential_moving", "Residential Moving"),
        ("office_relocation", "Office Relocation"),
        ("piano_moving", "Piano Moving"),
        ("antique_moving", "Antique Moving"),
        ("storage_services", "Storage Services"),
        ("packing_services", "Packing Services"),
        ("vehicle_transportation", "Vehicle Transportation"),
        ("international_moving", "International Moving"),
        ("furniture_assembly", "Furniture Assembly"),
        ("fragile_items", "Fragile Items"),
        ("artwork_moving", "Artwork Moving"),
        ("industrial_equipment", "Industrial Equipment"),
        ("electronics", "Electronics"),
        ("appliances", "Appliances"),
        ("boxes_parcels", "Boxes/Parcels"),
    ]

    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="stops")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="stops")
    external_id = models.CharField(max_length=100, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    unit_number = models.CharField(max_length=50, blank=True)
    floor = models.IntegerField(default=0)
    has_elevator = models.BooleanField(default=False)
    parking_info = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    completed_time = models.TimeField(null=True, blank=True)
    property_type = models.CharField(max_length=50, default="house")
    number_of_rooms = models.IntegerField(default=1, null=True, blank=True)
    number_of_floors = models.IntegerField(default=1, null=True, blank=True)
    service_type = models.CharField(max_length=50, blank=True, null=True)
    sequence = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.get_type_display()} - {self.location.address}"

    class Meta:
        db_table = "journey_stop"
        managed = True
        verbose_name = "Journey Stop"
        verbose_name_plural = "Journey Stops"
        ordering = ["sequence"]
