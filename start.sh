#!/bin/bash

# Entrypoint script for Elite Chat
# Requires environment variables for superuser creation
# Runs migrations, creates superuser, and starts Gunicorn

set -e  # Exit on any error

# Install system dependencies for psycopg compilation
apt-get update && apt-get install -y libpq-dev build-essential

# Check required environment variables
if [ -z "$DJANGO_SUPERUSER_USERNAME" ] || [ -z "$DJANGO_SUPERUSER_EMAIL" ] || [ -z "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Error: Required environment variables not set:"
    echo "  DJANGO_SUPERUSER_USERNAME"
    echo "  DJANGO_SUPERUSER_EMAIL"
    echo "  DJANGO_SUPERUSER_PASSWORD"
    exit 1
fi

echo "Starting Elite Chat..."

# Run database migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py createsuperuser

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn elite_chat.wsgi:application
