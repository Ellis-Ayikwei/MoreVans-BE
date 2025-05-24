from django.db import models

class ServiceCategory(models.Model):
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=30, null=True)

    def __str__(self):
        return self.name
        
    class Meta:
        db_table = 'service_category'
        managed = True
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"