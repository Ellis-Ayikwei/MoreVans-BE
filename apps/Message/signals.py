"""
Django signals for automatic chat notifications
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import ChatMessage
from .chat_services import ChatNotificationService

User = get_user_model()


@receiver(post_save, sender=ChatMessage)
def chat_message_created(sender, instance, created, **kwargs):
    """
    Send notifications when a new chat message is created
    """
    if created and instance.message_type not in ['system', 'status_update']:
        # Send notification to other participants
        ChatNotificationService.send_chat_notification(
            chat_room=instance.chat_room,
            message=instance,
            exclude_user=instance.sender
        )


# Use lazy imports for models to avoid circular imports
def get_bid_model():
    from apps.Bidding.models import Bid
    return Bid


def get_job_model():
    from apps.Job.models import Job
    return Job


def get_request_model():
    from apps.Request.models import Request
    return Request


@receiver(post_save, sender=None)  # We'll connect this manually
def bid_status_changed(sender, instance, created, **kwargs):
    """
    Send chat notifications when bid status changes
    """
    if created:
        # New bid submitted
        ChatNotificationService.notify_bid_update(
            bid=instance,
            action='submitted',
            user=getattr(instance.provider, 'user', None) if instance.provider else None
        )
    else:
        # Check if status changed
        if hasattr(instance, '_original_status'):
            old_status = instance._original_status
            if old_status != instance.status:
                action_map = {
                    'accepted': 'accepted',
                    'rejected': 'rejected',
                }
                action = action_map.get(instance.status, 'updated')
                
                ChatNotificationService.notify_bid_update(
                    bid=instance,
                    action=action,
                    user=getattr(instance.provider, 'user', None) if instance.provider else None
                )
        
        # Check if counter offer was made
        if hasattr(instance, '_original_counter_offer'):
            old_counter = instance._original_counter_offer
            if old_counter != instance.counter_offer and instance.counter_offer:
                ChatNotificationService.notify_bid_update(
                    bid=instance,
                    action='counter_offered',
                    user=getattr(instance.provider, 'user', None) if instance.provider else None
                )


@receiver(pre_save, sender=None)  # We'll connect this manually
def bid_pre_save(sender, instance, **kwargs):
    """
    Store original values before save to detect changes
    """
    if instance.pk:
        try:
            Bid = get_bid_model()
            original = Bid.objects.get(pk=instance.pk)
            instance._original_status = original.status
            instance._original_counter_offer = original.counter_offer
        except Bid.DoesNotExist:
            pass


@receiver(post_save, sender=None)  # We'll connect this manually
def job_status_changed(sender, instance, created, **kwargs):
    """
    Send chat notifications when job status changes
    """
    if not created and hasattr(instance, '_original_status'):
        old_status = instance._original_status
        if old_status != instance.status:
            ChatNotificationService.notify_job_status_change(
                job=instance,
                old_status=old_status,
                new_status=instance.status,
                user=getattr(instance.request, 'user', None) if instance.request else None
            )


@receiver(pre_save, sender=None)  # We'll connect this manually
def job_pre_save(sender, instance, **kwargs):
    """
    Store original status before save to detect changes
    """
    if instance.pk:
        try:
            Job = get_job_model()
            original = Job.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Job.DoesNotExist:
            pass


@receiver(post_save, sender=None)  # We'll connect this manually
def request_status_changed(sender, instance, created, **kwargs):
    """
    Send chat notifications when request status changes
    """
    if not created and hasattr(instance, '_original_status'):
        old_status = instance._original_status
        if old_status != instance.status:
            ChatNotificationService.notify_request_status_change(
                request=instance,
                old_status=old_status,
                new_status=instance.status,
                user=instance.user
            )


@receiver(pre_save, sender=None)  # We'll connect this manually
def request_pre_save(sender, instance, **kwargs):
    """
    Store original status before save to detect changes
    """
    if instance.pk:
        try:
            Request = get_request_model()
            original = Request.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Request.DoesNotExist:
            pass


# Connect signals manually to avoid circular imports
def connect_signals():
    """Connect signals to models to avoid circular import issues"""
    try:
        from apps.Bidding.models import Bid
        post_save.connect(bid_status_changed, sender=Bid)
        pre_save.connect(bid_pre_save, sender=Bid)
    except ImportError:
        pass
    
    try:
        from apps.Job.models import Job
        post_save.connect(job_status_changed, sender=Job)
        pre_save.connect(job_pre_save, sender=Job)
    except ImportError:
        pass
    
    try:
        from apps.Request.models import Request
        post_save.connect(request_status_changed, sender=Request)
        pre_save.connect(request_pre_save, sender=Request)
    except ImportError:
        pass