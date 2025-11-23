import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create superuser using required environment variables'

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS('Superuser already exists'))
            return

        required_vars = {
            'username': 'DJANGO_SUPERUSER_USERNAME',
            'email': 'DJANGO_SUPERUSER_EMAIL',
            'password': 'DJANGO_SUPERUSER_PASSWORD'
        }

        values = {}
        for key, env_var in required_vars.items():
            value = os.environ.get(env_var)
            if not value:
                raise CommandError(f'{env_var} environment variable is required')
            values[key] = value

        User.objects.create_superuser(
            username=values['username'],
            email=values['email'],
            password=values['password']
        )
        self.stdout.write(self.style.SUCCESS(f'Superuser created: {values["username"]}'))