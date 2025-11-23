#!/bin/bash

# Entrypoint script for Elite Chat
# Sets default environment variables if not provided
# Runs migrations, creates superuser, and starts Gunicorn

set -e  # Exit on any error

# Set default superuser credentials if not provided
export DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin}
export DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@example.com}
export DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-password}

echo "Starting Elite Chat..."

# Run database migrations
echo "Running migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py createsuperuser

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn elite_chat.wsgi:application --bind 0.0.0.0:8000