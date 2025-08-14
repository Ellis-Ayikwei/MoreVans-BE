from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ChatMessage, ConversationParticipant
from apps.Notification.services import NotificationService


@receiver(post_save, sender=ChatMessage)
def create_message_notification(_sender, instance, created, **_kwargs):
    """Create notifications when a new message is sent"""
    if not created or not instance.sender:
        return

    # Don't send notifications for system messages
    if instance.message_type == "system":
        return

    # Get all active participants except the sender
    participants = instance.conversation.participants.filter(
        is_active=True, notify_on_message=True
    ).exclude(user=instance.sender)

    # Create notification for each participant
    for participant in participants:
        try:
            NotificationService.create_notification(
                user=participant.user,
                notification_type="message_received",
                title=f"New message from {instance.sender.username}",
                message=(
                    instance.content[:100] + "..."
                    if len(instance.content) > 100
                    else instance.content
                ),
                related_object_type="chatmessage",
                related_object_id=str(instance.id),
                data={
                    "conversation_id": str(instance.conversation.id),
                    "conversation_type": instance.conversation.conversation_type,
                    "sender_id": str(instance.sender.id),
                    "sender_name": instance.sender.username,
                    "message_type": instance.message_type,
                },
                send_immediately=True,
            )
        except Exception as e:
            print(f"Error creating message notification: {e}")


@receiver(post_save, sender=ConversationParticipant)
def notify_participant_added(_sender, instance, created, **_kwargs):
    """Notify when a user is added to a conversation"""
    if not created or not instance.is_active:
        return

    try:
        NotificationService.create_notification(
            user=instance.user,
            notification_type="message_received",
            title="Added to conversation",
            message=f"You have been added to: {instance.conversation.title}",
            related_object_type="conversation",
            related_object_id=str(instance.conversation.id),
            data={
                "conversation_id": str(instance.conversation.id),
                "conversation_type": instance.conversation.conversation_type,
                "role": instance.role,
            },
            send_immediately=True,
        )
    except Exception as e:
        print(f"Error creating participant notification: {e}")
