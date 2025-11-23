import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create superuser using required environment variables'

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS('Superuser already exists'))
            return

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        if not username:
            raise CommandError('DJANGO_SUPERUSER_USERNAME environment variable is required')

        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        if not email:
            raise CommandError('DJANGO_SUPERUSER_EMAIL environment variable is required')

        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        if not password:
            raise CommandError('DJANGO_SUPERUSER_PASSWORD environment variable is required')

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Superuser created: {username}'))