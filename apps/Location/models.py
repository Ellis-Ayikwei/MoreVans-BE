from django.db import models
from apps.Basemodel.models import Basemodel

class Location(Basemodel):
    address = models.TextField()
    postcode = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    contact_name = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=15)
    special_instructions = models.TextField(blank=True)
    
    class Meta:
        db_table = 'location'
        managed = True
