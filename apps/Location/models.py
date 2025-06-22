from django.db import models
from apps.Basemodel.models import Basemodel


class Location(Basemodel):
    """Location model for storing address and contact information"""

    address = models.CharField(max_length=255)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    latitude = models.DecimalField(
        max_digits=30, decimal_places=20, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=30, decimal_places=20, null=True, blank=True
    )
    contact_name = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    use_main_contact = models.BooleanField(default=True)
    special_instructions = models.TextField(blank=True)

    def __str__(self):
        return f"{self.address}, {self.city}"

    class Meta:
        db_table = "location"
        managed = True
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("Location init:", self.address_line1)
