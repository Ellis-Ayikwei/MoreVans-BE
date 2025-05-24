# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

import Customer
from apps.Provider.models import ServiceProvider
from apps.User.models import User

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 'customer':
            Customer.objects.create(user=instance)
        elif instance.user_type == 'provider':
            ServiceProvider.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 'customer' and hasattr(instance, 'customer'):
        instance.customer.save()
    elif instance.user_type == 'provider' and hasattr(instance, 'provider'):
        instance.provider.save()
        
