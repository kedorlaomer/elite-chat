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
        from django.core.management.base import CommandError
        import os

        post_save.connect(create_profile, sender=User)

        # Create superuser if none exists
        if not User.objects.filter(is_superuser=True).exists():
            required_vars = {
                'username': 'DJANGO_SUPERUSER_USERNAME',
                'email': 'DJANGO_SUPERUSER_EMAIL',
                'password': 'DJANGO_SUPERUSER_PASSWORD'
            }

            values = {}
            for key, env_var in required_vars.items():
                value = os.environ.get(env_var)
                if not value:
                    # Skip if not all vars are set, to avoid errors on every startup
                    return
                values[key] = value

            try:
                User.objects.create_superuser(
                    username=values['username'],
                    email=values['email'],
                    password=values['password']
                )
                print(f'Superuser created: {values["username"]}')
            except Exception as e:
                print(f'Error creating superuser: {e}')
