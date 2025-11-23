from django.apps import AppConfig
from django.db.models.signals import post_save


def create_profile(sender, instance, created, **kwargs):
    from .models import Profile
    if created:
        Profile.objects.create(user=instance)


class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        from django.contrib.auth.models import User
        post_save.connect(create_profile, sender=User)
