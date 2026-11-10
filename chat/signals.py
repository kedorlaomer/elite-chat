from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Message, Image, DeletedMessage


@receiver(post_save, sender=Message)
def cleanup_orphaned_images(sender, instance, created, **kwargs):
    """
    Delete orphaned images older than 24 hours when a new message is created.
    This is database-independent and works across all Django-supported databases.
    """
    if created:
        cutoff_time = timezone.now() - timedelta(hours=24)
        Image.objects.filter(
            message__isnull=True,
            created_at__lt=cutoff_time
        ).delete()
        # Tombstones only need to outlive the slowest poller's catch-up window
        DeletedMessage.objects.filter(deleted_at__lt=cutoff_time).delete()


@receiver(post_delete, sender=Message)
def record_deleted_message(sender, instance, **kwargs):
    """
    Leave a tombstone so polling clients remove the message too. post_delete
    fires for views, admin actions and cascades alike (queryset deletes emit
    it per row because Message has a signal receiver).
    """
    DeletedMessage.objects.create(message_id=instance.id, room_id=instance.room_id)