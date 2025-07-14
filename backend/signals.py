# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out

from apps.Provider.models import ServiceProvider
from apps.User.models import User
from apps.User.models import UserActivity


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == "provider":
            ServiceProvider.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == "provider" and hasattr(instance, "provider"):
        instance.provider.save()


@receiver(user_logged_in)
def log_user_login(sender, user, request, **kwargs):
    UserActivity.objects.create(
        user=user,
        activity_type="login",
        details={"ip": request.META.get("REMOTE_ADDR")},
    )


@receiver(user_logged_out)
def log_user_logout(sender, user, request, **kwargs):
    UserActivity.objects.create(
        user=user,
        activity_type="logout",
        details={"ip": request.META.get("REMOTE_ADDR")},
    )
