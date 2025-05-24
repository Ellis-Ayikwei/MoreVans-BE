from django.db import models

from datetime import datetime, time
from http import client
from math import prod
from operator import add
import random
from django.db import models
from django.forms import model_to_dict
import uuid



class Basemodel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now=True, editable=False, null=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False, null=False)

    def to_dict(self, exclude_fields=None):
        """
        Serializes the model instance into a dictionary.
        :param exclude_fields: List of fields to exclude (e.g., ['password']).
        :return: Dictionary representation of the model.
        """
        exclude_fields = exclude_fields or []
        
        # Ensure 'id', 'created_at', and 'updated_at' are not excluded
        exclude_fields = [field for field in exclude_fields if field not in ['id', 'created_at', 'updated_at']]
        
        # Retrieve the model data, excluding the specified fields
        data = model_to_dict(self, exclude=exclude_fields)

        # Ensure 'id', 'created_at', and 'updated_at' are always included
        for field_name in ['id', 'created_at', 'updated_at']:
            if field_name not in data:
                data[field_name] = getattr(self, field_name)

        # Format datetime fields
        for field_name in ['created_at', 'updated_at']:
            if field_name in data and isinstance(data[field_name], datetime):
                data[field_name] = data[field_name].isoformat()

        # Convert ImageFieldFile to URL
        for field_name in self._meta.get_fields():
            
            if isinstance(field_name, models.ImageField):
                if getattr(self, field_name.name):
                    data[field_name.name] = getattr(self, field_name.name).url

        return data
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        print("BaseModel save starting...")
        super().save(*args, **kwargs)
        print("BaseModel save completed")

