from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Message, Image


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